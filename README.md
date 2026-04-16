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
