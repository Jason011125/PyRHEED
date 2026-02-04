"""Abstract base class for frame sources.

This module defines the interface for all frame data sources:
- Image sequences (folder of images)
- Video files (mp4, avi, etc.)
- Camera/CCD input
"""

from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from PyQt6.QtCore import QObject, pyqtSignal


class SourceState(Enum):
    """State of a frame source."""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class QObjectABCMeta(type(QObject), ABCMeta):
    """Metaclass combining QObject and ABC metaclasses."""
    pass


class FrameSource(QObject, metaclass=QObjectABCMeta):
    """Abstract base class for frame data sources.

    All frame sources (image sequence, video, camera) implement this interface
    to provide a unified way to access frame data.

    Signals:
        FRAME_READY: Emitted when a new frame is available.
            Args: (frame_data: np.ndarray, frame_index: int)
        STATE_CHANGED: Emitted when playback state changes.
            Args: (new_state: SourceState)
        ERROR_OCCURRED: Emitted when an error occurs.
            Args: (error_message: str)
        FPS_UPDATED: Emitted with current frames per second.
            Args: (fps: float)
    """

    FRAME_READY = pyqtSignal(np.ndarray, int)
    STATE_CHANGED = pyqtSignal(SourceState)
    ERROR_OCCURRED = pyqtSignal(str)
    FPS_UPDATED = pyqtSignal(float)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._state = SourceState.STOPPED
        self._current_frame_index = 0
        self._total_frames = 0
        self._fps = 30.0

    @property
    def state(self) -> SourceState:
        """Current playback state."""
        return self._state

    @property
    def current_frame_index(self) -> int:
        """Current frame index (0-based)."""
        return self._current_frame_index

    @property
    def total_frames(self) -> int:
        """Total number of frames (0 for live sources like camera)."""
        return self._total_frames

    @property
    def fps(self) -> float:
        """Frames per second."""
        return self._fps

    @property
    def is_live(self) -> bool:
        """Whether this is a live source (camera) vs recorded."""
        return False

    @abstractmethod
    def open(self, path: str) -> bool:
        """Open the source.

        Args:
            path: Path to file/folder, or device ID for camera.

        Returns:
            True if successfully opened, False otherwise.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the source and release resources."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start playback/capture."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop playback/capture."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause playback (not applicable for live sources)."""
        pass

    @abstractmethod
    def seek(self, frame_index: int) -> bool:
        """Seek to a specific frame.

        Args:
            frame_index: Target frame index.

        Returns:
            True if seek succeeded, False otherwise.
        """
        pass

    @abstractmethod
    def get_frame(self, frame_index: int) -> Optional[NDArray[np.uint8]]:
        """Get a specific frame by index.

        Args:
            frame_index: Frame index to retrieve.

        Returns:
            Frame data as grayscale uint8 array, or None if unavailable.
        """
        pass

    def _set_state(self, new_state: SourceState) -> None:
        """Update state and emit signal."""
        if self._state != new_state:
            self._state = new_state
            self.STATE_CHANGED.emit(new_state)
