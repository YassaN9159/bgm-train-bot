# scripts/fetch_music.py
import glob
import json
import os
import random
import subprocess
import tempfile
from pathlib import Path

import requests

TARGET_DURATION = 3600  # 60分

SEARCH_QUERIES = [
    "jazz instrumental relaxing",
    "jazz piano ambient background",
    "smooth jazz chill instrumental",
    "jazz background music calm",
    "lofi jazz instrumental study",
]


def search_archive_tracks(count: int = 30) -> list:
    """Internet Archive APIでジャズ音楽アイテムを検索"""
    query = random.choice(SEARCH_QUERIES)
    print(f"検索クエリ: {query}")

    resp = requests.get(
        "https://archive.org/advancedsearch.php",
        params={
            "q": f"({query}) AND mediatype:audio",
            "fl[]": ["identifier"],
            "rows": count,
            "output": "json",
            "sort[]": "downloads desc",
        },
        timeout=30,
    )
    resp.raise_for_status()
    docs = resp.json()["response"]["docs"]
    return [d["identifier"] for d in docs]


def get_mp3_url(identifier: str):
    """アイテムIDからMP3ダウンロードURLを取得"""
    try:
        resp = requests.get(
            f"https://archive.org/metadata/{identifier}",
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        files = data.get("files", [])
        mp3s = [
            f for f in files
            if f.get("format") in ("MP3", "VBR MP3")
            and int(f.get("size", "0")) < 30_000_000
        ]
        if not mp3s:
            return None
        return f"https://archive.org/download/{identifier}/{mp3s[0]['name']}"
    except Exception:
        return None


def download_tracks(output_dir: str, count: int = 8) -> list:
    """Internet ArchiveからジャズMP3をダウンロード"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    identifiers = search_archive_tracks(count * 4)
    random.shuffle(identifiers)

    downloaded = []
    for identifier in identifiers:
        if len(downloaded) >= count:
            break
        url = get_mp3_url(identifier)
        if not url:
            continue
        out_path = os.path.join(output_dir, f"{identifier}.mp3")
        try:
            print(f"  DL: {identifier}")
            resp = requests.get(url, timeout=120, stream=True)
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            downloaded.append(out_path)
        except Exception as e:
            print(f"  スキップ: {identifier} ({e})")
            if os.path.exists(out_path):
                os.remove(out_path)

    if not downloaded:
        raise FileNotFoundError(f"トラックのダウンロードに失敗しました: {output_dir}")
    print(f"{len(downloaded)}トラックをダウンロード")
    return downloaded


def get_audio_duration(filepath: str) -> float:
    """ffprobeでオーディオの長さを取得"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", filepath],
        capture_output=True, text=True, check=True
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def build_track_list(tracks: list, target: int) -> list:
    """合計がtarget秒以上になるまでトラックをループ"""
    result = []
    total = 0.0
    durations = {}
    for t in tracks:
        try:
            durations[t] = get_audio_duration(t)
        except Exception:
            durations[t] = 180.0

    while total < target:
        for t in tracks:
            result.append(t)
            total += durations[t]
            if total >= target:
                break
    return result


def fetch_bgm(output_path: str) -> str:
    """Internet ArchiveからDL → FFmpegで1時間BGMを生成"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tracks_dir = os.path.join(os.path.dirname(output_path), "tracks")

    print("ジャズトラックをダウンロード中...")
    tracks = download_tracks(tracks_dir)

    print("トラックを結合して1時間BGMを生成中...")
    track_list = build_track_list(tracks, TARGET_DURATION)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        concat_path = f.name
        for t in track_list:
            f.write(f"file '{os.path.abspath(t)}'\n")

    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_path,
            "-t", str(TARGET_DURATION),
            "-c:a", "libmp3lame", "-b:a", "192k",
            output_path
        ], check=True)
    finally:
        os.remove(concat_path)

    print(f"BGM生成完了: {output_path}")
    return output_path


if __name__ == "__main__":
    fetch_bgm("tmp/bgm.mp3")
