# scripts/upload_youtube.py
import os
from datetime import date
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DESCRIPTION_TEMPLATE = """\
🚂 深夜の寝台列車で流れるジャズBGMで作業・勉強・読書に集中できる1時間動画です。

━━━━━━━━━━━━━━━━━━━━
🎵 音楽: AI生成ジャズ・アンビエント
🎬 映像: 夜景・車窓・自然映像
━━━━━━━━━━━━━━━━━━━━

本動画はAIを活用して自動生成しています。
映像素材: Pexels (pexels.com)
音楽: Mubert AI (mubert.com)

#作業用BGM #勉強用BGM #寝台列車 #ジャズ #lofi
"""

TAGS = [
    "作業用BGM", "勉強用BGM", "集中BGM", "寝台列車", "ジャズ",
    "lofi", "study music", "train bgm", "作業用", "ambient music",
]

def build_metadata(target_date: date) -> dict:
    date_str = target_date.strftime("%Y.%m.%d")
    return {
        "title": f"【作業用BGM】深夜の寝台列車 🚂 ジャズで集中 | {date_str}",
        "description": DESCRIPTION_TEMPLATE,
        "tags": TAGS,
        "category_id": "10",
    }

def build_youtube_service(client_id: str, client_secret: str, refresh_token: str):
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("youtube", "v3", credentials=creds)

def upload_video(video_path: str, client_id: str, client_secret: str, refresh_token: str) -> str:
    meta = build_metadata(date.today())
    service = build_youtube_service(client_id, client_secret, refresh_token)

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta["category_id"],
        },
        "status": {"privacyStatus": "public"},
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=50 * 1024 * 1024)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"アップロード: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"投稿完了: https://www.youtube.com/watch?v={video_id}")
    return video_id


if __name__ == "__main__":
    upload_video(
        "tmp/output.mp4",
        os.environ["YOUTUBE_CLIENT_ID"],
        os.environ["YOUTUBE_CLIENT_SECRET"],
        os.environ["YOUTUBE_REFRESH_TOKEN"],
    )
