# BGM Train Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 「深夜の寝台列車」コンセプトの作業用BGM動画（1時間）をGitHub Actionsで毎日自動生成・YouTubeにアップロードするパイプラインを構築する。

**Architecture:** fetch_video.py（Pexels API）→ fetch_music.py（Mubert API）→ assemble_video.py（FFmpeg）→ upload_youtube.py（YouTube Data API v3）の4スクリプトをGitHub Actions cronで順次実行する。各スクリプトは独立して実行可能で、tmp/ディレクトリ経由でファイルを受け渡す。

**Tech Stack:** Python 3.11、FFmpeg、Pexels API、Mubert API v2、YouTube Data API v3、google-api-python-client、pytest、pytest-mock

---

## ファイル構成

```
bgm-train-bot/
├── .github/workflows/
│   └── daily-upload.yml
├── scripts/
│   ├── fetch_video.py
│   ├── fetch_music.py
│   ├── assemble_video.py
│   └── upload_youtube.py
├── tests/
│   ├── test_fetch_video.py
│   ├── test_fetch_music.py
│   ├── test_assemble_video.py
│   └── test_upload_youtube.py
├── tmp/                        # .gitignoreに追加（実行時に自動作成）
├── requirements.txt
├── .gitignore
└── README.md
```

---

### Task 1: プロジェクト scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: requirements.txt を作成**

```
requests==2.31.0
google-auth==2.28.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.118.0
pytest==8.0.0
pytest-mock==3.12.0
```

- [ ] **Step 2: .gitignore を作成**

```
tmp/
*.mp4
*.mp3
__pycache__/
*.pyc
.env
```

- [ ] **Step 3: README.md を作成**

```markdown
# BGM Train Bot

深夜の寝台列車コンセプトの作業用BGM動画を毎日自動生成・YouTube投稿するボット。

## 必要なGitHub Secrets

| Secret名 | 取得元 |
|---------|------|
| PEXELS_API_KEY | https://www.pexels.com/api/ |
| MUBERT_API_KEY | https://mubert.com/api （形式: email:license_key） |
| YOUTUBE_CLIENT_ID | Google Cloud Console |
| YOUTUBE_CLIENT_SECRET | Google Cloud Console |
| YOUTUBE_REFRESH_TOKEN | get_token.py で取得 |

## ローカル実行

```bash
pip install -r requirements.txt
export PEXELS_API_KEY=xxx
export MUBERT_API_KEY=email:license_key
python scripts/fetch_video.py
python scripts/fetch_music.py
python scripts/assemble_video.py
export YOUTUBE_CLIENT_ID=xxx YOUTUBE_CLIENT_SECRET=xxx YOUTUBE_REFRESH_TOKEN=xxx
python scripts/upload_youtube.py
```
```

- [ ] **Step 4: ディレクトリ作成 & 初回コミット**

```bash
mkdir -p scripts tests .github/workflows
git init
git add requirements.txt .gitignore README.md
git commit -m "chore: initial project scaffold"
```

---

### Task 2: fetch_video.py（Pexels API 映像DL）

**Files:**
- Create: `scripts/fetch_video.py`
- Create: `tests/test_fetch_video.py`

- [ ] **Step 1: テストを書く**

```python
# tests/test_fetch_video.py
import os
import pytest
from unittest.mock import patch, MagicMock
from scripts.fetch_video import fetch_clips, KEYWORDS

def make_fake_video_response(n=3):
    videos = []
    for i in range(n):
        videos.append({
            "id": i,
            "video_files": [
                {"link": f"https://example.com/clip_{i}.mp4", "width": 1920, "height": 1080},
                {"link": f"https://example.com/clip_{i}_sd.mp4", "width": 1280, "height": 720},
            ]
        })
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"videos": videos}
    mock_resp.raise_for_status.return_value = None
    return mock_resp

def test_fetch_clips_returns_correct_count(tmp_path, mocker):
    mocker.patch("scripts.fetch_video.requests.get", side_effect=[
        make_fake_video_response(4),  # search API
        *[MagicMock(iter_content=lambda chunk_size: [b"fake"], raise_for_status=lambda: None) for _ in range(3)],
    ])
    mocker.patch("builtins.open", mocker.mock_open())
    result = fetch_clips("fake_key", str(tmp_path), count=3)
    assert len(result) == 3

def test_fetch_clips_prefers_1080p(tmp_path, mocker):
    """1920x1080ファイルが優先されることを確認"""
    video = {
        "id": 1,
        "video_files": [
            {"link": "https://example.com/hd.mp4", "width": 1920, "height": 1080},
            {"link": "https://example.com/sd.mp4", "width": 640, "height": 360},
        ]
    }
    mock_search = MagicMock()
    mock_search.json.return_value = {"videos": [video]}
    mock_search.raise_for_status.return_value = None
    mock_dl = MagicMock()
    mock_dl.iter_content = lambda chunk_size: [b"data"]
    mock_dl.raise_for_status.return_value = None

    calls = []
    def fake_get(url, **kwargs):
        calls.append(url)
        if "pexels" in url:
            return mock_search
        return mock_dl

    mocker.patch("scripts.fetch_video.requests.get", side_effect=fake_get)
    mocker.patch("builtins.open", mocker.mock_open())
    fetch_clips("fake_key", str(tmp_path), count=1)
    assert "hd.mp4" in calls[1]

def test_keywords_not_empty():
    assert len(KEYWORDS) >= 4
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_fetch_video.py -v
```
Expected: `ModuleNotFoundError` または `ImportError`

- [ ] **Step 3: fetch_video.py を実装**

```python
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
            params["query"] = random.choice(KEYWORDS)

    downloaded = []
    for i, video in enumerate(videos[:count]):
        files = sorted(video["video_files"], key=lambda f: f.get("width", 0), reverse=True)
        best = next((f for f in files if f.get("width", 0) >= 1920), files[0])
        url = best["link"]
        filepath = os.path.join(output_dir, f"clip_{i+1:03d}.mp4")
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        downloaded.append(filepath)
        print(f"Downloaded: {filepath}")

    return downloaded


if __name__ == "__main__":
    api_key = os.environ["PEXELS_API_KEY"]
    clips = fetch_clips(api_key, "tmp/clips")
    print(f"Done: {len(clips)} clips")
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_fetch_video.py -v
```
Expected: 3 tests PASSED

- [ ] **Step 5: コミット**

```bash
git add scripts/fetch_video.py tests/test_fetch_video.py
git commit -m "feat: add fetch_video.py with Pexels API"
```

---

### Task 3: fetch_music.py（Mubert API BGM生成）

**Files:**
- Create: `scripts/fetch_music.py`
- Create: `tests/test_fetch_music.py`

> **Note:** Mubert API Key の形式は `email:license_key`（コロン区切り）。
> Mubert Developer Portal: https://mubert.com/api でAPIキーを取得。
> PAT取得URL: `POST https://api.mubert.com/v2/GetServiceAccess`
> トラック生成URL: `POST https://api.mubert.com/v2/RecordTrackTtT`

- [ ] **Step 1: テストを書く**

```python
# tests/test_fetch_music.py
import os
import pytest
from unittest.mock import patch, MagicMock, call
from scripts.fetch_music import get_pat, generate_track, fetch_bgm

def test_get_pat_calls_correct_endpoint(mocker):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": {"pat": "test-pat-token"}}
    mock_resp.raise_for_status.return_value = None
    mock_post = mocker.patch("scripts.fetch_music.requests.post", return_value=mock_resp)

    pat = get_pat("test@example.com", "license123")

    assert pat == "test-pat-token"
    args, kwargs = mock_post.call_args
    assert "GetServiceAccess" in args[0]

def test_generate_track_returns_url(mocker):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {"tasks": [{"download_link": "https://example.com/bgm.mp3"}]}
    }
    mock_resp.raise_for_status.return_value = None
    mocker.patch("scripts.fetch_music.requests.post", return_value=mock_resp)

    url = generate_track("test-pat", duration=3600)
    assert url == "https://example.com/bgm.mp3"

def test_fetch_bgm_creates_file(tmp_path, mocker):
    mocker.patch("scripts.fetch_music.get_pat", return_value="fake-pat")
    mocker.patch("scripts.fetch_music.generate_track", return_value="https://example.com/bgm.mp3")
    mock_dl = MagicMock()
    mock_dl.iter_content = lambda chunk_size: [b"audio_data"]
    mock_dl.raise_for_status.return_value = None
    mocker.patch("scripts.fetch_music.requests.get", return_value=mock_dl)
    mocker.patch("builtins.open", mocker.mock_open())

    output = fetch_bgm("test@example.com:license123", str(tmp_path / "bgm.mp3"))
    assert output.endswith("bgm.mp3")
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_fetch_music.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: fetch_music.py を実装**

```python
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
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_fetch_music.py -v
```
Expected: 3 tests PASSED

- [ ] **Step 5: コミット**

```bash
git add scripts/fetch_music.py tests/test_fetch_music.py
git commit -m "feat: add fetch_music.py with Mubert API"
```

---

### Task 4: assemble_video.py（FFmpeg合成）

**Files:**
- Create: `scripts/assemble_video.py`
- Create: `tests/test_assemble_video.py`

- [ ] **Step 1: テストを書く**

```python
# tests/test_assemble_video.py
import os
import json
import pytest
from unittest.mock import patch, MagicMock, call
from scripts.assemble_video import get_clip_duration, build_concat_list, assemble

def test_get_clip_duration(mocker):
    fake_output = json.dumps({
        "streams": [{"duration": "45.5"}]
    })
    mock_run = mocker.patch("scripts.assemble_video.subprocess.run")
    mock_run.return_value = MagicMock(stdout=fake_output, returncode=0)

    duration = get_clip_duration("tmp/clips/clip_001.mp4")
    assert duration == pytest.approx(45.5)
    args = mock_run.call_args[0][0]
    assert "ffprobe" in args[0]

def test_build_concat_list_fills_one_hour(tmp_path):
    clips = ["clip_a.mp4", "clip_b.mp4"]
    clip_durations = {"clip_a.mp4": 60.0, "clip_b.mp4": 90.0}
    target = 3610

    result = build_concat_list(clips, clip_durations, target)
    # リストの合計時間が target 以上であることを確認
    total = sum(clip_durations[c] for c in result)
    assert total >= target

def test_assemble_calls_ffmpeg(mocker, tmp_path):
    mocker.patch("scripts.assemble_video.get_clip_duration", return_value=120.0)
    mock_run = mocker.patch("scripts.assemble_video.subprocess.run")
    mock_run.return_value = MagicMock(returncode=0)
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("os.path.exists", return_value=True)

    clips = [str(tmp_path / "clip_001.mp4"), str(tmp_path / "clip_002.mp4")]
    assemble(clips, "tmp/bgm.mp3", "tmp/output.mp4")

    assert mock_run.called
    all_args = " ".join(str(a) for call in mock_run.call_args_list for a in call[0][0])
    assert "ffmpeg" in all_args
    assert "output.mp4" in all_args
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_assemble_video.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: assemble_video.py を実装**

```python
# scripts/assemble_video.py
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

    # 各クリップの長さを取得
    durations = {c: get_clip_duration(c) for c in clips}
    loop_list = build_concat_list(clips, durations, TARGET_DURATION)

    # FFmpeg用 concat リストファイルを一時ファイルに書く
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        concat_path = f.name
        for clip in loop_list:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    try:
        # Step 1: クリップを結合・ループして映像のみ作成
        video_only = output_path.replace(".mp4", "_video_only.mp4")
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

        os.remove(video_only)
    finally:
        os.remove(concat_path)

    print(f"合成完了: {output_path}")
    return output_path


if __name__ == "__main__":
    import glob
    clips = sorted(glob.glob("tmp/clips/*.mp4"))
    if not clips:
        raise FileNotFoundError("tmp/clips/ にクリップがありません")
    assemble(clips, "tmp/bgm.mp3", "tmp/output.mp4")
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_assemble_video.py -v
```
Expected: 3 tests PASSED

- [ ] **Step 5: コミット**

```bash
git add scripts/assemble_video.py tests/test_assemble_video.py
git commit -m "feat: add assemble_video.py with FFmpeg loop + BGM merge"
```

---

### Task 5: upload_youtube.py（YouTube Data API 投稿）

**Files:**
- Create: `scripts/upload_youtube.py`
- Create: `tests/test_upload_youtube.py`
- Create: `scripts/get_token.py`（リフレッシュトークン取得用ヘルパー）

- [ ] **Step 1: テストを書く**

```python
# tests/test_upload_youtube.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from scripts.upload_youtube import build_metadata, upload_video

def test_build_metadata_includes_date():
    meta = build_metadata(date(2026, 4, 16))
    assert "2026.04.16" in meta["title"]
    assert "寝台列車" in meta["title"]
    assert len(meta["tags"]) >= 5
    assert meta["category_id"] == "10"

def test_build_metadata_description_not_empty():
    meta = build_metadata(date(2026, 4, 16))
    assert len(meta["description"]) > 50

def test_upload_video_calls_insert(mocker, tmp_path):
    video_file = tmp_path / "output.mp4"
    video_file.write_bytes(b"fake_video")

    mock_service = MagicMock()
    mock_insert = MagicMock()
    mock_insert.next_chunk.return_value = (None, {"id": "abc123"})
    mock_service.videos.return_value.insert.return_value = mock_insert

    mocker.patch("scripts.upload_youtube.MediaFileUpload")
    mocker.patch("scripts.upload_youtube.build_youtube_service", return_value=mock_service)

    result = upload_video(str(video_file), "cid", "csec", "rtoken")
    assert result == "abc123"
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_upload_youtube.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: upload_youtube.py を実装**

```python
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
        "category_id": "10",  # Music
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
```

- [ ] **Step 4: get_token.py を作成（リフレッシュトークン取得用・一回限り実行）**

```python
# scripts/get_token.py
# ローカルで一回だけ実行してYOUTUBE_REFRESH_TOKENを取得する
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
```

- [ ] **Step 5: テストが通ることを確認**

```bash
pytest tests/test_upload_youtube.py -v
```
Expected: 3 tests PASSED

- [ ] **Step 6: コミット**

```bash
git add scripts/upload_youtube.py scripts/get_token.py tests/test_upload_youtube.py
git commit -m "feat: add upload_youtube.py with YouTube Data API v3"
```

---

### Task 6: GitHub Actions ワークフロー

**Files:**
- Create: `.github/workflows/daily-upload.yml`

- [ ] **Step 1: daily-upload.yml を作成**

```yaml
# .github/workflows/daily-upload.yml
name: Daily BGM Upload

on:
  schedule:
    - cron: '0 22 * * *'  # 毎日 07:00 JST（UTC+9 = UTC 22:00前日）
  workflow_dispatch:        # 手動実行用

jobs:
  build-and-upload:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Python セットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: FFmpeg インストール
        run: sudo apt-get install -y ffmpeg

      - name: 依存ライブラリインストール
        run: pip install -r requirements.txt

      - name: テスト実行
        run: pytest tests/ -v

      - name: 映像クリップDL（Pexels）
        env:
          PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}
        run: python scripts/fetch_video.py

      - name: BGM生成（Mubert）
        env:
          MUBERT_API_KEY: ${{ secrets.MUBERT_API_KEY }}
        run: python scripts/fetch_music.py

      - name: 動画合成（FFmpeg）
        run: python scripts/assemble_video.py

      - name: YouTube投稿
        env:
          YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
          YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
          YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN }}
        run: python scripts/upload_youtube.py
```

- [ ] **Step 2: GitHub にリポジトリを作成してプッシュ**

```bash
gh repo create YassaN9159/bgm-train-bot --public --source=. --remote=origin
git push -u origin main
```

- [ ] **Step 3: GitHub Secrets を登録**

```bash
gh secret set PEXELS_API_KEY
gh secret set MUBERT_API_KEY          # 形式: email:license_key
gh secret set YOUTUBE_CLIENT_ID
gh secret set YOUTUBE_CLIENT_SECRET
gh secret set YOUTUBE_REFRESH_TOKEN   # get_token.py で取得した値
```

- [ ] **Step 4: 手動実行でテスト**

```bash
gh workflow run daily-upload.yml
gh run watch  # 実行状況をリアルタイムで確認
```

Expected: 全ステップ GREEN、YouTubeチャンネルに動画が投稿される

- [ ] **Step 5: コミット**

```bash
git add .github/workflows/daily-upload.yml
git commit -m "feat: add GitHub Actions daily upload workflow"
git push
```

---

## 全テスト一括実行

```bash
pytest tests/ -v
```

Expected:
```
tests/test_fetch_video.py::test_fetch_clips_returns_correct_count PASSED
tests/test_fetch_video.py::test_fetch_clips_prefers_1080p PASSED
tests/test_fetch_video.py::test_keywords_not_empty PASSED
tests/test_fetch_music.py::test_get_pat_calls_correct_endpoint PASSED
tests/test_fetch_music.py::test_generate_track_returns_url PASSED
tests/test_fetch_music.py::test_fetch_bgm_creates_file PASSED
tests/test_assemble_video.py::test_get_clip_duration PASSED
tests/test_assemble_video.py::test_build_concat_list_fills_one_hour PASSED
tests/test_assemble_video.py::test_assemble_calls_ffmpeg PASSED
tests/test_upload_youtube.py::test_build_metadata_includes_date PASSED
tests/test_upload_youtube.py::test_build_metadata_description_not_empty PASSED
tests/test_upload_youtube.py::test_upload_video_calls_insert PASSED
12 passed
```
