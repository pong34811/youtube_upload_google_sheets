"""Google OAuth2 authentication helper."""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from config import CLIENT_SECRETS_FILE, TOKEN_FILE, SCOPES


def get_credentials() -> Credentials:
    """Load or create OAuth2 credentials for YouTube + Sheets APIs.

    Flow:
    1. Try loading a cached token.json
    2. If expired, refresh it
    3. If missing or unrefreshable, run the OAuth consent flow
    """
    creds = None

    # 1. Try cached token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 2. Refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("♻️  Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Opening browser for Google sign-in...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(
                port=0,
                prompt="consent",
                access_type="offline",
            )

        # Cache the token
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"✅ Token saved to {TOKEN_FILE}")

    return creds
