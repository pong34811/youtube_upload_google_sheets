"""YouTube Upload via Google Sheets — main script.

Reads video metadata from a Google Spreadsheet row, uploads each video
to YouTube, sets thumbnail / playlist, then writes back the video ID
and updates the row status.

Usage:
    python upload.py          # process all WAIT_UPLOAD rows
    python upload.py --dry    # preview without uploading
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from typing import Any

from googleapiclient.discovery import build
from tqdm import tqdm
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from auth import get_credentials
from config import (
    COL_STATE,
    COL_VIDEO_ID,
    DEFAULT_CATEGORY_ID,
    RESUMABLE_CHUNK_SIZE,
    SHEET_NAME,
    SPREADSHEET_ID,
    STATE_FAILED,
    STATE_UPLOADING,
    STATE_UPLOADED,
    STATE_WAIT,
)

# ─── Helpers ─────────────────────────────────────────────────────────────────

YOUTUBE_UPLOAD_MIMETYPE = "video/*"
MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


def _parse_date(raw: Any) -> datetime.datetime | None:
    """Parse a date from Sheets (serial number, ISO string, or DD/MM/YYYY)."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        epoch = datetime.datetime(1899, 12, 30)
        return epoch + datetime.timedelta(days=raw)
    if isinstance(raw, str) and raw.strip():
        raw_str = raw.strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(raw_str, fmt)
            except ValueError:
                continue
        return datetime.datetime.fromisoformat(raw_str)
    return None


def _resumable_upload(
    youtube: Any,
    body: dict,
    media: MediaFileUpload,
    file_size: int,
) -> str:
    """Perform a resumable upload with automatic retries and tqdm progress."""
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    retry = 0
    with tqdm(total=file_size, unit="B", unit_scale=True, desc="   📤 Upload") as pbar:
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    pbar.update(status.progress() * file_size - pbar.n)
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    retry += 1
                    if retry > MAX_RETRIES:
                        raise
                    wait = 2 ** retry
                    print(f"\n   ⚠️  Retriable error {e.resp.status}, retry {retry}/{MAX_RETRIES} in {wait}s")
                    time.sleep(wait)
                else:
                    raise

    return response["id"]


# ─── Core logic ──────────────────────────────────────────────────────────────

def read_pending_rows(sheets: Any) -> list[dict]:
    """Read all rows with state == WAIT_UPLOAD from the spreadsheet."""
    range_ = f"'{SHEET_NAME}'!A:K"
    result = sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_,
    ).execute()
    rows = result.get("values", [])

    if len(rows) < 2:
        print("ℹ️  No data rows found in the spreadsheet.")
        return []

    pending: list[dict] = []
    for idx, row in enumerate(rows[1:], start=2):  # skip header
        # Pad row to at least 10 columns
        while len(row) < 10:
            row.append(None)

        # A=0state B=1title C=2desc D=3tags E=4cat F=5privacy G=6publish H=7video I=8thumb J=9playlist
        state = row[0] if len(row) > 0 else None
        if state and state.strip().upper() == STATE_WAIT:
            pending.append({
                "row_num": idx,
                "state": row[0],
                "title": row[1] if len(row) > 1 else None,
                "description": row[2] if len(row) > 2 else None,
                "tags": row[3] if len(row) > 3 else None,
                "category_id": row[4] if len(row) > 4 else None,
                "privacy_status": row[5] if len(row) > 5 else None,
                "publish_at": row[6] if len(row) > 6 else None,
                "video_path": row[7] if len(row) > 7 else None,
                "thumbnail_path": row[8] if len(row) > 8 else None,
                "playlist_id": row[9] if len(row) > 9 else None,
            })

    return pending


def update_cell(sheets: Any, row_num: int, col: int, value: str) -> None:
    """Write a single cell value back to the spreadsheet."""
    col_letter = chr(ord("A") + col - 1)
    range_ = f"'{SHEET_NAME}'!{col_letter}{row_num}"
    sheets.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_,
        valueInputOption="USER_ENTERED",
        body={"values": [[value]]},
    ).execute()


def upload_video(
    youtube: Any,
    sheets: Any,
    row: dict,
    dry: bool = False,
) -> bool:
    """Upload a single video. Returns True on success."""

    row_num = row["row_num"]
    title = row["title"]
    video_path = row["video_path"]
    thumbnail_path = row["thumbnail_path"]

    print(f"\n{'─' * 60}")
    print(f"📹  Row {row_num}: {title}")

    # ── Validate video file ──────────────────────────────────────────────
    if not video_path:
        print("   ❌  No video_path — skipping.")
        update_cell(sheets, row_num, COL_STATE, STATE_FAILED)
        return False

    # Strip all quotes (outer and inner like "Katy404" in filename)
    video_path = video_path.replace('"', '').replace("'", "")

    if not os.path.isfile(video_path):
        print(f"   ❌  File not found: {video_path}")
        update_cell(sheets, row_num, COL_STATE, STATE_FAILED)
        return False

    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"   📂  File: {os.path.basename(video_path)} ({file_size_mb:.1f} MB)")

    if dry:
        print("   🧪  [DRY RUN] Would upload this file.")
        return True

    # ── Mark as UPLOADING ────────────────────────────────────────────────
    update_cell(sheets, row_num, COL_STATE, STATE_UPLOADING)

    # ── Build snippet ────────────────────────────────────────────────────
    snippet: dict[str, Any] = {
        "title": title or "Untitled",
        "description": row["description"] or "",
    }

    tags_str = row["tags"]
    if tags_str:
        snippet["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]

    raw_cat = row["category_id"]
    category_id = str(int(float(raw_cat))) if raw_cat else DEFAULT_CATEGORY_ID
    snippet["categoryId"] = category_id

    # ── Build status ─────────────────────────────────────────────────────
    status: dict[str, str] = {
        "privacyStatus": (row["privacy_status"] or "private").lower(),
    }

    publish_at = _parse_date(row["publish_at"])
    if publish_at and status["privacyStatus"] == "private":
        # YouTube expects ISO 8601 with timezone — assume local (ICT, UTC+7)
        if publish_at.tzinfo is None:
            publish_at = publish_at.replace(
                hour=0, minute=0, second=0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=7)),
            )
        status["publishAt"] = publish_at.isoformat()
        snippet["publishAt"] = status["publishAt"]

    body = {"snippet": snippet, "status": status}

    # ── Upload ───────────────────────────────────────────────────────────
    try:
        media = MediaFileUpload(
            video_path,
            mimetype=YOUTUBE_UPLOAD_MIMETYPE,
            resumable=True,
            chunksize=RESUMABLE_CHUNK_SIZE,
        )
        file_size = os.path.getsize(video_path)
        video_id = _resumable_upload(youtube, body, media, file_size)
        print(f"   ✅  Uploaded!  video_id = {video_id}")
        print(f"   🔗  https://youtu.be/{video_id}")
    except Exception as exc:
        print(f"   ❌  Upload failed: {exc}")
        update_cell(sheets, row_num, COL_STATE, STATE_FAILED)
        return False

    # ── Thumbnail ────────────────────────────────────────────────────────
    if thumbnail_path:
        thumbnail_path = thumbnail_path.replace('"', '').replace("'", "")
        if os.path.isfile(thumbnail_path):
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
                ).execute()
                print(f"   🖼️  Thumbnail set.")
            except HttpError as e:
                print(f"   ⚠️  Thumbnail upload failed (non-fatal): {e}")
        else:
            print(f"   ⚠️  Thumbnail file not found: {thumbnail_path}")

    # ── Add to playlist ──────────────────────────────────────────────────
    playlist_id = row.get("playlist_id")
    if playlist_id:
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()
            print(f"   📋  Added to playlist: {playlist_id}")
        except HttpError as e:
            print(f"   ⚠️  Playlist insert failed (non-fatal): {e}")

    # ── Write back ───────────────────────────────────────────────────────
    update_cell(sheets, row_num, COL_STATE, STATE_UPLOADED)
    update_cell(sheets, row_num, COL_VIDEO_ID, video_id)
    print(f"   📝  Sheet updated: {STATE_UPLOADED}")

    return True


# ─── CLI entry point ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Upload videos to YouTube from Google Sheets.")
    parser.add_argument("--dry", action="store_true", help="Preview mode — no actual upload.")
    args = parser.parse_args()

    print("=" * 60)
    print("  🎬  YouTube Upload via Google Sheets")
    print("=" * 60)

    # Authenticate
    creds = get_credentials()
    sheets = build("sheets", "v4", credentials=creds)
    youtube = build("youtube", "v3", credentials=creds)

    # Read pending rows
    print(f"\n📖  Reading spreadsheet '{SHEET_NAME}'...")
    pending = read_pending_rows(sheets)
    print(f"   Found {len(pending)} row(s) with state = {STATE_WAIT}")

    if not pending:
        print("\n✅  Nothing to upload. All done!")
        return

    # Upload each video
    success = 0
    fail = 0
    for row in pending:
        ok = upload_video(youtube, sheets, row, dry=args.dry)
        if ok:
            success += 1
        else:
            fail += 1

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  📊  Summary:  ✅ {success} succeeded  |  ❌ {fail} failed")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔  Cancelled by user.")
        sys.exit(1)
    except Exception as exc:
        print(f"\n💥  Fatal error: {exc}")
        sys.exit(1)
