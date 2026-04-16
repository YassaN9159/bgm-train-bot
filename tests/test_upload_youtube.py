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
    mock_request = MagicMock()
    mock_request.next_chunk.return_value = (None, {"id": "abc123"})
    mock_service.videos.return_value.insert.return_value = mock_request

    mocker.patch("scripts.upload_youtube.MediaFileUpload")
    mocker.patch("scripts.upload_youtube.build_youtube_service", return_value=mock_service)

    result = upload_video(str(video_file), "cid", "csec", "rtoken")
    assert result == "abc123"
