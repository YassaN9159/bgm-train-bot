# scripts/assemble_video.py
import glob
import json
import os
import subprocess
import tempfile
from pathlib import Path

TARGET_DURATION = 3610  # 1時間 + 余裕10秒

def get_clip_duration(filepath: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", filepath],
        capture_output=True, text=True, check=True
    )
    data = json.loads(result.stdout)
    return float(data["streams"][0]["duration"])

def build_concat_list(clips: list, durations: dict, target: int) -> list:
    result = []
    total = 0.0
    while total < target:
        for clip in clips:
            result.append(clip)
            total += durations[clip]
            if total >= target:
                break
    return result

def assemble(clips: list, bgm_path: str, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    durations = {c: get_clip_duration(c) for c in clips}
    loop_list = build_concat_list(clips, durations, TARGET_DURATION)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        concat_path = f.name
        for clip in loop_list:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    video_only = output_path.replace(".mp4", "_video_only.mp4")
    try:
        # Step 1: クリップを結合・ループして映像のみ作成
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_path,
            "-t", str(TARGET_DURATION),
            "-vf", "scale=1920:1080,fps=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            video_only
        ], check=True)

        # Step 2: BGM音声と合成
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_only,
            "-i", bgm_path,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ], check=True)

    finally:
        os.remove(concat_path)
        if os.path.exists(video_only):
            os.remove(video_only)

    print(f"合成完了: {output_path}")
    return output_path


if __name__ == "__main__":
    clips = sorted(glob.glob("tmp/clips/*.mp4"))
    if not clips:
        raise FileNotFoundError("tmp/clips/ にクリップがありません")
    assemble(clips, "tmp/bgm.mp3", "tmp/output.mp4")
