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
    mock_dl = MagicMock()
    mock_dl.iter_content = lambda chunk_size: [b"fake"]
    mock_dl.raise_for_status.return_value = None

    mocker.patch("scripts.fetch_video.requests.get", side_effect=[
        make_fake_video_response(4),
        mock_dl, mock_dl, mock_dl,
    ])
    mocker.patch("builtins.open", mocker.mock_open())
    result = fetch_clips("fake_key", str(tmp_path), count=3)
    assert len(result) == 3

def test_fetch_clips_prefers_1080p(tmp_path, mocker):
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
