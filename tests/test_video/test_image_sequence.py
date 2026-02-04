"""Tests for ImageSequenceSource."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pyrheed.video.image_sequence import ImageSequenceSource, SUPPORTED_EXTENSIONS
from pyrheed.video.source import SourceState


@pytest.fixture
def temp_image_folder():
    """Create a temporary folder with test images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = Path(tmpdir)

        # Create 5 test images with different intensities
        for i in range(5):
            img_array = np.full((100, 100), i * 50, dtype=np.uint8)
            img = Image.fromarray(img_array, mode="L")
            img.save(folder / f"frame_{i:03d}.png")

        yield folder


@pytest.fixture
def empty_folder():
    """Create an empty temporary folder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestImageSequenceSource:
    """Tests for ImageSequenceSource."""

    def test_open_valid_folder(self, temp_image_folder):
        """open() should succeed with valid image folder."""
        source = ImageSequenceSource()
        result = source.open(str(temp_image_folder))

        assert result is True
        assert source.total_frames == 5

    def test_open_empty_folder(self, empty_folder):
        """open() should fail for folder with no images."""
        source = ImageSequenceSource()
        result = source.open(str(empty_folder))

        assert result is False
        assert source.total_frames == 0

    def test_open_nonexistent_path(self):
        """open() should fail for nonexistent path."""
        source = ImageSequenceSource()
        result = source.open("/nonexistent/path/to/folder")

        assert result is False

    def test_get_frame(self, temp_image_folder):
        """get_frame() should return correct image data."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))

        # First frame should be all zeros
        frame0 = source.get_frame(0)
        assert frame0 is not None
        assert frame0.shape == (100, 100)
        assert frame0.dtype == np.uint8
        assert np.all(frame0 == 0)

        # Third frame should be 100
        frame2 = source.get_frame(2)
        assert frame2 is not None
        assert np.all(frame2 == 100)

    def test_get_frame_out_of_bounds(self, temp_image_folder):
        """get_frame() should return None for invalid index."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))

        assert source.get_frame(-1) is None
        assert source.get_frame(100) is None

    def test_seek(self, temp_image_folder, qtbot):
        """seek() should update current frame and emit signal."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))

        with qtbot.waitSignal(source.FRAME_READY, timeout=1000) as blocker:
            result = source.seek(3)

        assert result is True
        assert source.current_frame_index == 3

        # Check signal args: (frame_data, frame_index)
        frame_data, frame_index = blocker.args
        assert frame_index == 3
        assert np.all(frame_data == 150)  # 3 * 50

    def test_seek_invalid_index(self, temp_image_folder):
        """seek() should fail for invalid index."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))

        assert source.seek(-1) is False
        assert source.seek(100) is False

    def test_start_stop(self, temp_image_folder, qtbot):
        """start() and stop() should control playback."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))
        source.set_fps(10)  # 10 FPS for faster test

        # Start should emit frames
        with qtbot.waitSignal(source.FRAME_READY, timeout=1000):
            source.start()

        assert source.state == SourceState.PLAYING

        # Stop should halt playback
        source.stop()
        assert source.state == SourceState.STOPPED
        assert source.current_frame_index == 0

    def test_pause_resume(self, temp_image_folder, qtbot):
        """pause() should pause and allow resume."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))
        source.set_fps(10)

        source.start()
        assert source.state == SourceState.PLAYING

        source.pause()
        assert source.state == SourceState.PAUSED

        # Resume
        source.start()
        assert source.state == SourceState.PLAYING

        source.stop()

    def test_close(self, temp_image_folder):
        """close() should reset all state."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))
        source.seek(2)

        source.close()

        assert source.total_frames == 0
        assert source.current_frame_index == 0
        assert source.state == SourceState.STOPPED

    def test_get_image_path(self, temp_image_folder):
        """get_image_path() should return correct path."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))

        path = source.get_image_path(0)
        assert path is not None
        assert path.name == "frame_000.png"

        path = source.get_image_path(2)
        assert path.name == "frame_002.png"

        # Invalid index
        assert source.get_image_path(100) is None

    def test_set_fps(self, temp_image_folder):
        """set_fps() should clamp to valid range."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))

        source.set_fps(30)
        assert source.fps == 30

        # Clamp to minimum
        source.set_fps(0)
        assert source.fps == 1.0

        # Clamp to maximum
        source.set_fps(500)
        assert source.fps == 120.0

    def test_frame_caching(self, temp_image_folder):
        """Frames should be cached for performance."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))

        # Load frame to cache
        frame1 = source.get_frame(0)

        # Second call should return cached version
        frame2 = source.get_frame(0)

        # Should be the same object (cached)
        assert frame1 is frame2

    def test_images_sorted_alphabetically(self, temp_image_folder):
        """Images should be sorted by filename."""
        source = ImageSequenceSource()
        source.open(str(temp_image_folder))

        # Verify order
        for i in range(5):
            path = source.get_image_path(i)
            assert path.name == f"frame_{i:03d}.png"

    def test_error_signal_on_invalid_folder(self, qtbot):
        """ERROR_OCCURRED should be emitted for invalid folder."""
        source = ImageSequenceSource()

        with qtbot.waitSignal(source.ERROR_OCCURRED, timeout=1000) as blocker:
            source.open("/nonexistent/path")

        assert "Not a directory" in blocker.args[0]

    def test_supported_extensions(self):
        """SUPPORTED_EXTENSIONS should include common formats."""
        assert ".png" in SUPPORTED_EXTENSIONS
        assert ".jpg" in SUPPORTED_EXTENSIONS
        assert ".jpeg" in SUPPORTED_EXTENSIONS
        assert ".tif" in SUPPORTED_EXTENSIONS
        assert ".tiff" in SUPPORTED_EXTENSIONS
        assert ".bmp" in SUPPORTED_EXTENSIONS
