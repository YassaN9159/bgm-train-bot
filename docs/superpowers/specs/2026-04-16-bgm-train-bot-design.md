# BGM Train Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 「深夜の寝台列車」コンセプトの作業用BGM動画（1時間）をGitHub Actionsで毎日自動生成・YouTubeにアップロードする。

**Architecture:** Pexels APIで夜景・車窓映像を自動DL、Mubert APIで60分ジャズBGMを生成、FFmpegで映像ループ+音楽を合成し1時間動画を作成。YouTube Data APIで毎朝自動投稿。サーバー不要・コスト0円（API無料枠）。

**Tech Stack:** Python 3.11、FFmpeg、Pexels API、Mubert API、YouTube Data API v3、GitHub Actions

---

## システム全体フロー

```
GitHub Actions cron (毎日 07:00 JST = 22:00 UTC)
  │
  ├─ fetch_video.py   → Pexels APIで夜景・車窓クリップ3〜5本DL → tmp/clips/
  ├─ fetch_music.py   → Mubert APIで60分ジャズBGM生成 → tmp/bgm.mp3
  ├─ assemble_video.py → FFmpegで動画ループ合成+BGM重ね → tmp/output.mp4（1時間・1080p）
  └─ upload_youtube.py → YouTube Data APIで投稿（タイトル・説明・タグ自動生成）
```

---

## ファイル構成

```
bgm-train-bot/
├── .github/workflows/
│   └── daily-upload.yml       # cron毎日実行ワークフロー
├── scripts/
│   ├── fetch_video.py         # Pexels API映像DL
│   ├── fetch_music.py         # Mubert API BGM生成
│   ├── assemble_video.py      # FFmpeg合成
│   └── upload_youtube.py      # YouTube投稿
├── assets/
│   └── title_card.png         # オープニングタイトル画像（5秒）
├── requirements.txt
└── README.md
```

---

## 各モジュール仕様

### fetch_video.py
- **入力:** 環境変数 `PEXELS_API_KEY`
- **キーワード:** `["night train window", "train rain window", "forest night rain", "night landscape moving"]` からランダム選択
- **取得数:** 3〜5クリップ（各30〜90秒）
- **解像度:** 1920x1080優先、なければ最大解像度
- **出力:** `tmp/clips/clip_001.mp4`, `clip_002.mp4` ...

### fetch_music.py
- **入力:** 環境変数 `MUBERT_API_KEY`
- **ジャンル:** `"jazz"` + `"ambient"` ミックス
- **長さ:** 3600秒（60分）
- **出力:** `tmp/bgm.mp3`

### assemble_video.py
- **処理フロー:**
  1. `tmp/clips/` の動画クリップをFFmpegで結合・ループして3610秒に伸ばす
  2. タイトルカード（`assets/title_card.png`）を冒頭5秒に合成
  3. `tmp/bgm.mp3` を音声トラックとして合成（元動画音声はミュート）
  4. 出力: 1080p / 30fps / AAC 192kbps
- **出力:** `tmp/output.mp4`

### upload_youtube.py
- **認証:** OAuth2（YOUTUBE_CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN）
- **タイトル自動生成:**
  ```
  【作業用BGM】深夜の寝台列車 🚂 ジャズで集中 | {YYYY.MM.DD}
  ```
- **説明文自動生成:** 固定テンプレート（チャンネル説明・タグ・著作権表記）
- **タグ:** `["作業用BGM", "勉強用BGM", "寝台列車", "ジャズ", "lofi", "study music", "train bgm"]`
- **公開設定:** `public`
- **カテゴリ:** Music (10)

---

## GitHub Actions ワークフロー

```yaml
name: Daily BGM Upload
on:
  schedule:
    - cron: '0 22 * * *'  # 毎日 07:00 JST
  workflow_dispatch:       # 手動実行も可能

jobs:
  build-and-upload:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: sudo apt-get install -y ffmpeg
      - run: pip install -r requirements.txt
      - run: python scripts/fetch_video.py
      - run: python scripts/fetch_music.py
      - run: python scripts/assemble_video.py
      - run: python scripts/upload_youtube.py
```

---

## GitHub Secrets

| Secret名 | 用途 |
|---------|------|
| `PEXELS_API_KEY` | Pexels映像DL |
| `MUBERT_API_KEY` | BGM生成 |
| `YOUTUBE_CLIENT_ID` | YouTube OAuth |
| `YOUTUBE_CLIENT_SECRET` | YouTube OAuth |
| `YOUTUBE_REFRESH_TOKEN` | YouTube OAuth |

---

## エラーハンドリング

- Pexels APIでクリップ取得失敗 → キーワードを変えてリトライ（最大3回）
- Mubert API失敗 → YouTubeオーディオライブラリのフリー素材（事前DL済み）をフォールバック使用
- FFmpeg失敗 → ワークフローをexit 1で停止・GitHub通知
- YouTube投稿失敗 → ワークフローをexit 1で停止

---

## 動画スペック

| 項目 | 値 |
|------|-----|
| 解像度 | 1920x1080 (1080p) |
| フレームレート | 30fps |
| 映像コーデック | H.264 |
| 音声コーデック | AAC |
| 音声ビットレート | 192kbps |
| 長さ | 3600秒（1時間） |

---

## 収益化見込み

- YouTube収益化条件：1000登録者 + 4000時間視聴
- 毎日1本投稿 → 3ヶ月で90本蓄積
- 再生数が伸び始めたらAdSense収益発生
- 追加コスト：0円（全API無料枠内）
