"""Tests for VideoFileSource."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from pyrheed.video.video_file import VideoFileSource, SUPPORTED_EXTENSIONS
from pyrheed.video.source import SourceState


@pytest.fixture
def temp_video_file():
    """Create a temporary test video file."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        video_path = Path(f.name)

    # Create a simple test video with 30 frames
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, 30.0, (100, 100))

    for i in range(30):
        # Create frame with intensity based on frame number
        frame = np.full((100, 100, 3), i * 8, dtype=np.uint8)
        writer.write(frame)

    writer.release()

    yield video_path

    # Cleanup
    if video_path.exists():
        video_path.unlink()


@pytest.fixture
def temp_invalid_file():
    """Create a temporary invalid file."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"not a valid video")
        invalid_path = Path(f.name)

    yield invalid_path

    if invalid_path.exists():
        invalid_path.unlink()


class TestVideoFileSource:
    """Tests for VideoFileSource."""

    def test_open_valid_video(self, temp_video_file):
        """open() should succeed with valid video file."""
        source = VideoFileSource()
        result = source.open(str(temp_video_file))

        assert result is True
        assert source.total_frames == 30
        assert source.fps == 30.0

        source.close()

    def test_open_nonexistent_file(self):
        """open() should fail for nonexistent file."""
        source = VideoFileSource()
        result = source.open("/nonexistent/video.mp4")

        assert result is False

    def test_open_unsupported_format(self):
        """open() should fail for unsupported format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = Path(f.name)

        try:
            source = VideoFileSource()
            result = source.open(str(temp_path))
            assert result is False
        finally:
            temp_path.unlink()

    def test_open_invalid_video(self, temp_invalid_file):
        """open() should fail for corrupted video."""
        source = VideoFileSource()
        result = source.open(str(temp_invalid_file))

        assert result is False

    def test_get_frame(self, temp_video_file):
        """get_frame() should return correct image data."""
        source = VideoFileSource()
        source.open(str(temp_video_file))

        frame = source.get_frame(0)
        assert frame is not None
        assert frame.shape == (100, 100)
        assert frame.dtype == np.uint8

        source.close()

    def test_get_frame_out_of_bounds(self, temp_video_file):
        """get_frame() should return None for invalid index."""
        source = VideoFileSource()
        source.open(str(temp_video_file))

        assert source.get_frame(-1) is None
        assert source.get_frame(1000) is None

        source.close()

    def test_seek(self, temp_video_file, qtbot):
        """seek() should update current frame and emit signal."""
        source = VideoFileSource()
        source.open(str(temp_video_file))

        with qtbot.waitSignal(source.FRAME_READY, timeout=1000) as blocker:
            result = source.seek(15)

        assert result is True
        assert source.current_frame_index == 15

        frame_data, frame_index = blocker.args
        assert frame_index == 15

        source.close()

    def test_seek_invalid_index(self, temp_video_file):
        """seek() should fail for invalid index."""
        source = VideoFileSource()
        source.open(str(temp_video_file))

        assert source.seek(-1) is False
        assert source.seek(1000) is False

        source.close()

    def test_start_stop(self, temp_video_file, qtbot):
        """start() and stop() should control playback."""
        source = VideoFileSource()
        source.open(str(temp_video_file))

        with qtbot.waitSignal(source.FRAME_READY, timeout=1000):
            source.start()

        assert source.state == SourceState.PLAYING

        source.stop()
        assert source.state == SourceState.STOPPED
        assert source.current_frame_index == 0

        source.close()

    def test_pause_resume(self, temp_video_file, qtbot):
        """pause() should pause and allow resume."""
        source = VideoFileSource()
        source.open(str(temp_video_file))

        source.start()
        assert source.state == SourceState.PLAYING

        source.pause()
        assert source.state == SourceState.PAUSED

        source.start()
        assert source.state == SourceState.PLAYING

        source.stop()
        source.close()

    def test_close(self, temp_video_file):
        """close() should reset all state."""
        source = VideoFileSource()
        source.open(str(temp_video_file))
        source.seek(10)

        source.close()

        assert source.total_frames == 0
        assert source.current_frame_index == 0
        assert source.state == SourceState.STOPPED

    def test_get_video_info(self, temp_video_file):
        """get_video_info() should return video metadata."""
        source = VideoFileSource()
        source.open(str(temp_video_file))

        info = source.get_video_info()

        assert info["total_frames"] == 30
        assert info["fps"] == 30.0
        assert info["width"] == 100
        assert info["height"] == 100
        assert info["duration_sec"] == 1.0

        source.close()

    def test_set_fps(self, temp_video_file):
        """set_fps() should clamp to valid range."""
        source = VideoFileSource()
        source.open(str(temp_video_file))

        source.set_fps(60)
        assert source.fps == 60

        source.set_fps(0)
        assert source.fps == 1.0

        source.set_fps(500)
        assert source.fps == 120.0

        source.close()

    def test_error_signal_on_invalid_file(self, qtbot):
        """ERROR_OCCURRED should be emitted for invalid file."""
        source = VideoFileSource()

        with qtbot.waitSignal(source.ERROR_OCCURRED, timeout=1000) as blocker:
            source.open("/nonexistent/video.mp4")

        assert "not found" in blocker.args[0].lower()

    def test_supported_extensions(self):
        """SUPPORTED_EXTENSIONS should include common formats."""
        assert ".mp4" in SUPPORTED_EXTENSIONS
        assert ".avi" in SUPPORTED_EXTENSIONS
        assert ".mov" in SUPPORTED_EXTENSIONS
        assert ".mkv" in SUPPORTED_EXTENSIONS

    def test_reopen_different_video(self, temp_video_file):
        """Opening a new video should release the previous one."""
        source = VideoFileSource()

        # Open first video
        source.open(str(temp_video_file))
        assert source.total_frames == 30

        # Create and open a second video
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path2 = Path(f.name)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(video_path2), fourcc, 30.0, (50, 50))
        for i in range(10):
            frame = np.zeros((50, 50, 3), dtype=np.uint8)
            writer.write(frame)
        writer.release()

        try:
            source.open(str(video_path2))
            assert source.total_frames == 10
        finally:
            source.close()
            video_path2.unlink()
