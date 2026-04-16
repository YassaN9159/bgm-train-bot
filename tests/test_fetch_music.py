# tests/test_fetch_music.py
import os
import pytest
from unittest.mock import MagicMock, patch, call
from scripts.fetch_music import download_tracks, build_track_list, fetch_bgm

def test_download_tracks_calls_yt_dlp(mocker, tmp_path):
    mock_run = mocker.patch("scripts.fetch_music.subprocess.run")
    mock_run.return_value = MagicMock(returncode=0)
    # Create fake mp3 files so glob finds them
    (tmp_path / "abc123.mp3").write_bytes(b"fake")
    (tmp_path / "def456.mp3").write_bytes(b"fake")

    result = download_tracks(str(tmp_path), count=8)

    assert mock_run.called
    cmd = mock_run.call_args[0][0]
    assert "yt-dlp" in cmd[0]
    assert "ytsearch8:" in cmd[1]
    assert len(result) == 2

def test_build_track_list_fills_target(mocker):
    mocker.patch("scripts.fetch_music.get_audio_duration", return_value=180.0)
    tracks = ["a.mp3", "b.mp3", "c.mp3"]
    result = build_track_list(tracks, target=3600)
    total = len(result) * 180.0
    assert total >= 3600

def test_fetch_bgm_creates_output(mocker, tmp_path):
    output = str(tmp_path / "bgm.mp3")
    mocker.patch("scripts.fetch_music.download_tracks", return_value=["a.mp3", "b.mp3"])
    mocker.patch("scripts.fetch_music.build_track_list", return_value=["a.mp3"] * 20)
    mocker.patch("scripts.fetch_music.get_audio_duration", return_value=180.0)
    mock_run = mocker.patch("scripts.fetch_music.subprocess.run")
    mock_run.return_value = MagicMock(returncode=0)
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("os.remove")

    result = fetch_bgm(output)
    assert result == output
    assert mock_run.called
