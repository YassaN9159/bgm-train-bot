# scripts/fetch_music.py
import glob
import os
import random
import subprocess
import tempfile
from pathlib import Path

TARGET_DURATION = 3600  # 60分

# 検索クエリ（毎回ランダムに選択）
SEARCH_QUERIES = [
    "jazz lofi instrumental study music",
    "soft jazz piano ambient instrumental",
    "calm jazz background music instrumental",
    "lofi jazz chill instrumental",
    "smooth jazz ambient relaxing",
]

def download_tracks(output_dir: str, count: int = 8) -> list:
    """yt-dlpでジャズ系トラックをダウンロード"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    query = random.choice(SEARCH_QUERIES)
    print(f"検索クエリ: {query}")

    subprocess.run([
        "yt-dlp",
        f"ytsearch{count}:{query}",
        "--match-filter", "duration > 60 & duration < 600",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "192K",
        "-o", os.path.join(output_dir, "%(id)s.%(ext)s"),
        "--no-playlist",
        "--quiet",
        "--no-warnings",
    ], check=True)

    tracks = sorted(glob.glob(os.path.join(output_dir, "*.mp3")))
    if not tracks:
        raise FileNotFoundError(f"トラックのダウンロードに失敗しました: {output_dir}")
    print(f"{len(tracks)}トラックをダウンロード")
    return tracks


def get_audio_duration(filepath: str) -> float:
    """ffprobeでオーディオの長さを取得"""
    import json
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
            durations[t] = 180.0  # 取得失敗時は3分と仮定

    while total < target:
        for t in tracks:
            result.append(t)
            total += durations[t]
            if total >= target:
                break
    return result


def fetch_bgm(output_path: str) -> str:
    """yt-dlpでトラックDL → FFmpegで1時間BGMを生成"""
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
