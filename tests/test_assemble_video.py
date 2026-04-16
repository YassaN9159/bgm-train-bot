# tests/test_assemble_video.py
import os
import json
import pytest
from unittest.mock import patch, MagicMock
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
    total = sum(clip_durations[c] for c in result)
    assert total >= target

def test_assemble_calls_ffmpeg(mocker, tmp_path):
    mocker.patch("scripts.assemble_video.get_clip_duration", return_value=120.0)
    mock_run = mocker.patch("scripts.assemble_video.subprocess.run")
    mock_run.return_value = MagicMock(returncode=0)
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.remove")

    clips = [str(tmp_path / "clip_001.mp4"), str(tmp_path / "clip_002.mp4")]
    assemble(clips, "tmp/bgm.mp3", "tmp/output.mp4")

    assert mock_run.called
    all_args = " ".join(str(a) for call in mock_run.call_args_list for a in call[0][0])
    assert "ffmpeg" in all_args
    assert "output.mp4" in all_args
