"""Video file source implementation.

Loads video files (mp4, avi, etc.) using OpenCV for frame-by-frame analysis.
"""

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from PyQt6.QtCore import QTimer

from pyrheed.video.source import FrameSource, SourceState


# Supported video formats
SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}


class VideoFileSource(FrameSource):
    """Frame source that loads video files.

    Uses OpenCV VideoCapture for decoding.
    Supports MP4, AVI, MOV, MKV, WMV, FLV, WebM formats.

    Example:
        source = VideoFileSource()
        source.open("/path/to/video.mp4")
        source.start()  # Begins emitting FRAME_READY signals
    """

    def __init__(self) -> None:
        super().__init__()
        self._cap: Optional[cv2.VideoCapture] = None
        self._video_path: Optional[Path] = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)

    def open(self, path: str) -> bool:
        """Open a video file.

        Args:
            path: Path to video file.

        Returns:
            True if video opened successfully.
        """
        video_path = Path(path)

        if not video_path.is_file():
            self.ERROR_OCCURRED.emit(f"File not found: {path}")
            return False

        if video_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            self.ERROR_OCCURRED.emit(
                f"Unsupported format: {video_path.suffix}. "
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
            return False

        # Open with OpenCV
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            self.ERROR_OCCURRED.emit(f"Failed to open video: {path}")
            return False

        # Close previous capture if any
        if self._cap is not None:
            self._cap.release()

        self._cap = cap
        self._video_path = video_path

        # Get video properties
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._current_frame_index = 0

        return True

    def close(self) -> None:
        """Close the video and release resources."""
        self.stop()

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        self._video_path = None
        self._total_frames = 0
        self._current_frame_index = 0

    def start(self) -> None:
        """Start playback, emitting frames at video's FPS."""
        if self._cap is None or not self._cap.isOpened():
            self.ERROR_OCCURRED.emit("No video loaded. Call open() first.")
            return

        self._set_state(SourceState.PLAYING)
        interval_ms = int(1000 / self._fps)
        self._timer.start(interval_ms)

    def stop(self) -> None:
        """Stop playback and reset to first frame."""
        self._timer.stop()
        self._current_frame_index = 0

        # Seek to beginning
        if self._cap is not None:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self._set_state(SourceState.STOPPED)

    def pause(self) -> None:
        """Pause playback at current frame."""
        if self._state == SourceState.PLAYING:
            self._timer.stop()
            self._set_state(SourceState.PAUSED)

    def seek(self, frame_index: int) -> bool:
        """Seek to a specific frame.

        Args:
            frame_index: Target frame index (0-based).

        Returns:
            True if seek succeeded.
        """
        if self._cap is None:
            return False

        if not 0 <= frame_index < self._total_frames:
            return False

        # OpenCV seek
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        self._current_frame_index = frame_index

        # Emit the frame at new position
        frame = self.get_frame(frame_index)
        if frame is not None:
            self.FRAME_READY.emit(frame, frame_index)

        return True

    def get_frame(self, frame_index: int) -> Optional[NDArray[np.uint8]]:
        """Get a specific frame by index.

        Args:
            frame_index: Frame index to retrieve.

        Returns:
            Grayscale uint8 numpy array, or None if unavailable.
        """
        if self._cap is None:
            return None

        if not 0 <= frame_index < self._total_frames:
            return None

        # Seek if needed
        current_pos = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
        if current_pos != frame_index:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        ret, frame = self._cap.read()

        if not ret or frame is None:
            return None

        # Convert based on grayscale setting
        if self._grayscale:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def get_video_info(self) -> dict:
        """Get video metadata.

        Returns:
            Dictionary with video properties.
        """
        if self._cap is None:
            return {}

        return {
            "path": str(self._video_path) if self._video_path else None,
            "total_frames": self._total_frames,
            "fps": self._fps,
            "width": int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration_sec": self._total_frames / self._fps if self._fps > 0 else 0,
            "codec": self._get_codec(),
        }

    def set_fps(self, fps: float) -> None:
        """Override playback FPS (does not affect video file).

        Args:
            fps: Target FPS (1-120).
        """
        self._fps = max(1.0, min(120.0, fps))

        if self._state == SourceState.PLAYING:
            interval_ms = int(1000 / self._fps)
            self._timer.setInterval(interval_ms)

    def _on_timer(self) -> None:
        """Timer callback - read and emit next frame."""
        if self._cap is None:
            return

        ret, frame = self._cap.read()

        if not ret or frame is None:
            # End of video - loop back
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._current_frame_index = 0
            return

        # Convert based on grayscale setting
        if self._grayscale:
            converted = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            converted = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.FRAME_READY.emit(converted, self._current_frame_index)
        self._current_frame_index += 1

    def _get_codec(self) -> str:
        """Get video codec fourcc code."""
        if self._cap is None:
            return ""

        fourcc = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        # Convert int to 4-char string
        return "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
