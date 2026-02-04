"""Tests for FrameSource abstract base class."""

import numpy as np
import pytest
from typing import Optional
from numpy.typing import NDArray

from pyrheed.video.source import FrameSource, SourceState


class MockFrameSource(FrameSource):
    """Mock implementation for testing."""

    def __init__(self) -> None:
        super().__init__()
        self._opened = False
        self._frames: list[NDArray[np.uint8]] = []

    def open(self, path: str) -> bool:
        self._opened = True
        self._total_frames = 10
        self._frames = [
            np.full((100, 100), i * 25, dtype=np.uint8)
            for i in range(10)
        ]
        return True

    def close(self) -> None:
        self._opened = False
        self._frames = []
        self._set_state(SourceState.STOPPED)

    def start(self) -> None:
        if self._opened:
            self._set_state(SourceState.PLAYING)

    def stop(self) -> None:
        self._set_state(SourceState.STOPPED)
        self._current_frame_index = 0

    def pause(self) -> None:
        if self._state == SourceState.PLAYING:
            self._set_state(SourceState.PAUSED)

    def seek(self, frame_index: int) -> bool:
        if 0 <= frame_index < self._total_frames:
            self._current_frame_index = frame_index
            return True
        return False

    def get_frame(self, frame_index: int) -> Optional[NDArray[np.uint8]]:
        if 0 <= frame_index < len(self._frames):
            return self._frames[frame_index]
        return None


class TestFrameSource:
    """Tests for FrameSource interface."""

    def test_initial_state(self) -> None:
        """Source should start in STOPPED state."""
        source = MockFrameSource()
        assert source.state == SourceState.STOPPED
        assert source.current_frame_index == 0
        assert source.total_frames == 0

    def test_open_source(self) -> None:
        """Opening source should set total_frames."""
        source = MockFrameSource()
        result = source.open("/fake/path")
        assert result is True
        assert source.total_frames == 10

    def test_state_transitions(self) -> None:
        """State should transition correctly."""
        source = MockFrameSource()
        source.open("/fake/path")

        # STOPPED -> PLAYING
        source.start()
        assert source.state == SourceState.PLAYING

        # PLAYING -> PAUSED
        source.pause()
        assert source.state == SourceState.PAUSED

        # PAUSED -> STOPPED
        source.stop()
        assert source.state == SourceState.STOPPED

    def test_seek(self) -> None:
        """Seek should update current_frame_index."""
        source = MockFrameSource()
        source.open("/fake/path")

        assert source.seek(5) is True
        assert source.current_frame_index == 5

        # Out of bounds should fail
        assert source.seek(100) is False
        assert source.current_frame_index == 5  # unchanged

    def test_get_frame(self) -> None:
        """get_frame should return correct data."""
        source = MockFrameSource()
        source.open("/fake/path")

        frame = source.get_frame(0)
        assert frame is not None
        assert frame.shape == (100, 100)
        assert frame.dtype == np.uint8
        assert np.all(frame == 0)  # First frame is all zeros

        frame = source.get_frame(4)
        assert frame is not None
        assert np.all(frame == 100)  # 4 * 25 = 100

    def test_get_frame_out_of_bounds(self) -> None:
        """get_frame should return None for invalid index."""
        source = MockFrameSource()
        source.open("/fake/path")

        assert source.get_frame(-1) is None
        assert source.get_frame(100) is None

    def test_state_changed_signal(self, qtbot) -> None:
        """STATE_CHANGED signal should be emitted."""
        source = MockFrameSource()
        source.open("/fake/path")

        with qtbot.waitSignal(source.STATE_CHANGED, timeout=1000) as blocker:
            source.start()

        assert blocker.args == [SourceState.PLAYING]

    def test_close_resets_state(self) -> None:
        """close() should reset to STOPPED."""
        source = MockFrameSource()
        source.open("/fake/path")
        source.start()
        assert source.state == SourceState.PLAYING

        source.close()
        assert source.state == SourceState.STOPPED

    def test_is_live_default(self) -> None:
        """is_live should default to False."""
        source = MockFrameSource()
        assert source.is_live is False

    def test_grayscale_default(self) -> None:
        """grayscale should default to True for RHEED."""
        source = MockFrameSource()
        assert source.grayscale is True

    def test_grayscale_setter(self) -> None:
        """grayscale can be toggled."""
        source = MockFrameSource()
        assert source.grayscale is True

        source.grayscale = False
        assert source.grayscale is False

        source.grayscale = True
        assert source.grayscale is True
