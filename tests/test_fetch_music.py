# tests/test_fetch_music.py
import os
import pytest
from unittest.mock import MagicMock, patch, call
from scripts.fetch_music import download_tracks, build_track_list, fetch_bgm

def test_download_tracks_uses_internet_archive(mocker, tmp_path):
    mocker.patch(
        "scripts.fetch_music.search_archive_tracks",
        return_value=["id001", "id002", "id003"],
    )
    mocker.patch(
        "scripts.fetch_music.get_mp3_url",
        side_effect=lambda ident: f"https://archive.org/download/{ident}/track.mp3",
    )

    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.iter_content = MagicMock(return_value=[b"fakedata"])
    mocker.patch("scripts.fetch_music.requests.get", return_value=fake_response)

    result = download_tracks(str(tmp_path), count=2)

    assert len(result) == 2
    assert all(r.endswith(".mp3") for r in result)

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
