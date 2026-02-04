"""Image sequence source implementation.

Loads a sequence of images from a folder for frame-by-frame analysis.
"""

import os
from pathlib import Path
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from PyQt6.QtCore import QTimer

from pyrheed.video.source import FrameSource, SourceState


# Supported image formats
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


class ImageSequenceSource(FrameSource):
    """Frame source that loads images from a folder.

    Images are sorted alphabetically by filename.
    Supports PNG, JPG, TIFF, BMP formats.

    Example:
        source = ImageSequenceSource()
        source.open("/path/to/images/")
        source.start()  # Begins emitting FRAME_READY signals
    """

    def __init__(self) -> None:
        super().__init__()
        self._image_paths: list[Path] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)
        self._frame_cache: dict[int, NDArray[np.uint8]] = {}
        self._cache_size = 10  # Number of frames to cache

    def open(self, path: str) -> bool:
        """Open a folder containing images.

        Args:
            path: Path to folder containing image files.

        Returns:
            True if folder exists and contains valid images.
        """
        folder = Path(path)
        if not folder.is_dir():
            self.ERROR_OCCURRED.emit(f"Not a directory: {path}")
            return False

        # Find all image files
        self._image_paths = sorted(
            p for p in folder.iterdir()
            if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )

        if not self._image_paths:
            self.ERROR_OCCURRED.emit(f"No images found in: {path}")
            return False

        self._total_frames = len(self._image_paths)
        self._current_frame_index = 0
        self._frame_cache.clear()

        return True

    def close(self) -> None:
        """Close the source and release resources."""
        self.stop()
        self._image_paths = []
        self._frame_cache.clear()
        self._total_frames = 0
        self._current_frame_index = 0

    def start(self) -> None:
        """Start playback, emitting frames at configured FPS."""
        if not self._image_paths:
            self.ERROR_OCCURRED.emit("No images loaded. Call open() first.")
            return

        self._set_state(SourceState.PLAYING)
        interval_ms = int(1000 / self._fps)
        self._timer.start(interval_ms)

    def stop(self) -> None:
        """Stop playback and reset to first frame."""
        self._timer.stop()
        self._current_frame_index = 0
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
        if not 0 <= frame_index < self._total_frames:
            return False

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
        if not 0 <= frame_index < self._total_frames:
            return None

        # Check cache first
        if frame_index in self._frame_cache:
            return self._frame_cache[frame_index]

        # Load from disk
        try:
            image_path = self._image_paths[frame_index]
            img = Image.open(image_path)

            # Convert to grayscale
            if img.mode != "L":
                img = img.convert("L")

            frame = np.array(img, dtype=np.uint8)

            # Update cache
            self._update_cache(frame_index, frame)

            return frame

        except Exception as e:
            self.ERROR_OCCURRED.emit(f"Failed to load frame {frame_index}: {e}")
            return None

    def get_image_path(self, frame_index: int) -> Optional[Path]:
        """Get the file path for a specific frame.

        Args:
            frame_index: Frame index.

        Returns:
            Path to the image file, or None if invalid index.
        """
        if 0 <= frame_index < len(self._image_paths):
            return self._image_paths[frame_index]
        return None

    def set_fps(self, fps: float) -> None:
        """Set playback frames per second.

        Args:
            fps: Target FPS (1-120).
        """
        self._fps = max(1.0, min(120.0, fps))

        # Update timer if playing
        if self._state == SourceState.PLAYING:
            interval_ms = int(1000 / self._fps)
            self._timer.setInterval(interval_ms)

    def _on_timer(self) -> None:
        """Timer callback - emit next frame."""
        frame = self.get_frame(self._current_frame_index)

        if frame is not None:
            self.FRAME_READY.emit(frame, self._current_frame_index)

        # Advance to next frame
        self._current_frame_index += 1

        # Loop or stop at end
        if self._current_frame_index >= self._total_frames:
            self._current_frame_index = 0  # Loop back

    def _update_cache(self, frame_index: int, frame: NDArray[np.uint8]) -> None:
        """Update frame cache with LRU eviction."""
        self._frame_cache[frame_index] = frame

        # Evict oldest if cache is full
        if len(self._frame_cache) > self._cache_size:
            # Remove the key furthest from current position
            keys = list(self._frame_cache.keys())
            distances = [abs(k - self._current_frame_index) for k in keys]
            furthest_idx = distances.index(max(distances))
            del self._frame_cache[keys[furthest_idx]]
