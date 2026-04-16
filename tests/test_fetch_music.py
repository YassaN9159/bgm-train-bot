# tests/test_fetch_music.py
import pytest
from unittest.mock import MagicMock, patch
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
