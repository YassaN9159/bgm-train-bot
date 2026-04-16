# scripts/get_token.py
import os
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
CLIENT_SECRET = os.environ["YOUTUBE_CLIENT_SECRET"]
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

flow = InstalledAppFlow.from_client_config(
    {"installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }},
    scopes=SCOPES,
)
creds = flow.run_local_server(port=8080)
print(f"\nYOUTUBE_REFRESH_TOKEN={creds.refresh_token}")
