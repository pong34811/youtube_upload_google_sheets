"""Configuration constants for YouTube Upload via Google Sheets."""

import os

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

# ─── Google Sheets ───────────────────────────────────────────────────────────
SPREADSHEET_ID = "1RJHqQASgP7U2bej9qnibKYVyBC_zpc6EpW33P1irCsU"
SHEET_NAME = "KATY404"

# ─── Column indices
# read_pending_rows uses 0-based inline (row[0]..row[9])
# update_cell uses 1-based (A=1, K=11)
COL_STATE = 1
COL_VIDEO_ID = 11

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
