# scripts/fetch_music.py
import hashlib
import os
import requests
from pathlib import Path

MUBERT_BASE = "https://api.mubert.com/v2"

def get_pat(email: str, license_key: str) -> str:
    token = hashlib.md5(license_key.encode()).hexdigest()
    resp = requests.post(f"{MUBERT_BASE}/GetServiceAccess", json={
        "method": "GetServiceAccess",
        "params": {
            "email": email,
            "license": license_key,
            "token": token,
            "mode": "loop",
        }
    }, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    pat = data.get("data", {}).get("pat")
    if not pat:
        raise ValueError(f"Mubert PAT取得失敗: {data}")
    return pat

def generate_track(pat: str, duration: int = 3600, tags: list = None) -> str:
    if tags is None:
        tags = ["jazz", "ambient", "lofi"]
    resp = requests.post(f"{MUBERT_BASE}/RecordTrackTtT", json={
        "method": "RecordTrackTtT",
        "params": {
            "pat": pat,
            "duration": duration,
            "tags": tags,
            "format": "mp3",
            "intensity": "medium",
        }
    }, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        url = data["data"]["tasks"][0]["download_link"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Mubert トラックURL取得失敗: {data}") from e
    return url

def fetch_bgm(api_key: str, output_path: str) -> str:
    email, license_key = api_key.split(":", 1)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print("Mubert PAT取得中...")
    pat = get_pat(email, license_key)

    print("BGM生成中（60分）...")
    track_url = generate_track(pat, duration=3600)

    print(f"BGMダウンロード中: {track_url}")
    r = requests.get(track_url, stream=True, timeout=300)
    r.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"BGM保存完了: {output_path}")
    return output_path


if __name__ == "__main__":
    api_key = os.environ["MUBERT_API_KEY"]
    fetch_bgm(api_key, "tmp/bgm.mp3")
