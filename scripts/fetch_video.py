# scripts/fetch_video.py
import os
import random
import requests
from pathlib import Path

PEXELS_API_URL = "https://api.pexels.com/videos/search"
KEYWORDS = [
    "night train window",
    "train rain window",
    "forest night rain",
    "night landscape moving",
    "rainy night city",
]

def fetch_clips(api_key: str, output_dir: str, count: int = 4) -> list:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    keyword = random.choice(KEYWORDS)
    headers = {"Authorization": api_key}
    params = {"query": keyword, "per_page": count * 2, "orientation": "landscape"}

    videos = []
    for attempt in range(3):
        try:
            resp = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            videos = resp.json().get("videos", [])
            if videos:
                break
        except Exception:
            if attempt == 2:
                raise
            remaining = [kw for kw in KEYWORDS if kw != params["query"]]
            params["query"] = random.choice(remaining) if remaining else random.choice(KEYWORDS)

    downloaded = []
    for i, video in enumerate(videos[:count]):
        video_files = video.get("video_files", [])
        if not video_files:
            print(f"Warning: video {video.get('id')} has no files, skipping")
            continue

        files = sorted(video_files, key=lambda f: f.get("width", 0), reverse=True)
        best = next((f for f in files if f.get("width", 0) >= 1920), files[0])
        url = best.get("link")
        if not url:
            print(f"Warning: no link for video {video.get('id')}, skipping")
            continue

        filepath = os.path.join(output_dir, f"clip_{i+1:03d}.mp4")
        try:
            r = requests.get(url, stream=True, timeout=120)
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            downloaded.append(filepath)
            print(f"Downloaded: {filepath}")
        except Exception as e:
            print(f"Warning: failed to download clip {i+1}: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)  # 不完全なファイルを削除

    return downloaded


if __name__ == "__main__":
    api_key = os.environ["PEXELS_API_KEY"]
    clips = fetch_clips(api_key, "tmp/clips")
    print(f"Done: {len(clips)} clips")
