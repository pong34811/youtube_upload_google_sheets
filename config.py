"""Configuration constants for YouTube Upload via Google Sheets."""

import os

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

# ─── Google Sheets ───────────────────────────────────────────────────────────
SPREADSHEET_ID = "1RJHqQASgP7U2bej9qnibKYVyBC_zpc6EpW33P1irCsU"
SHEET_NAME = "KATY404"

# Column indices (1-based, matching Google Sheets API)
COL_STATE = 1          # A
COL_VIDEO_TITLE = 2    # B
COL_DESCRIPTION = 3    # C
COL_TAGS = 4           # D
COL_CATEGORY_ID = 5    # E
COL_PRIVACY_STATUS = 6 # F
COL_PUBLISH_AT = 7     # G
COL_VIDEO_PATH = 8     # H
COL_THUMBNAIL_PATH = 9 # I
COL_PLAYLIST_ID = 10   # J
COL_VIDEO_ID = 11      # K  (written back after upload)

# ─── Upload states ───────────────────────────────────────────────────────────
STATE_WAIT = "WAIT_UPLOAD"
STATE_UPLOADING = "UPLOADING"
STATE_UPLOADED = "Complete"
STATE_FAILED = "FAILED"

# ─── YouTube API scopes ──────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Default YouTube category (20 = Gaming)
DEFAULT_CATEGORY_ID = "20"

# Max upload chunk size (10 MB)
RESUMABLE_CHUNK_SIZE = 10 * 1024 * 1024
