"""Camera source implementation.

Provides real-time frame capture from camera/CCD devices using OpenCV.
"""

from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from PyQt6.QtCore import QThread, QMutex, QMutexLocker

from pyrheed.video.source import FrameSource, SourceState


def enumerate_cameras(max_devices: int = 10) -> list[dict]:
    """Enumerate available camera devices.

    Args:
        max_devices: Maximum number of devices to check.

    Returns:
        List of dicts with device info: {id, name, available}
    """
    devices = []

    for i in range(max_devices):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Try to get device name (platform-dependent)
            backend = cap.getBackendName()
            devices.append({
                "id": i,
                "name": f"Camera {i} ({backend})",
                "available": True,
            })
            cap.release()

    return devices


class CameraWorker(QThread):
    """Worker thread for camera capture.

    Runs in a separate thread to avoid blocking the UI.
    """

    def __init__(self, source: "CameraSource") -> None:
        super().__init__()
        self._source = source
        self._running = False
        self._mutex = QMutex()

    def run(self) -> None:
        """Main capture loop."""
        self._running = True
        frame_index = 0

        while self._running:
            with QMutexLocker(self._mutex):
                if not self._running:
                    break

            cap = self._source._cap
            if cap is None or not cap.isOpened():
                break

            ret, frame = cap.read()

            if not ret or frame is None:
                self._source.ERROR_OCCURRED.emit("Failed to read frame from camera")
                continue

            # Convert based on grayscale setting
            if self._source.grayscale:
                converted = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                converted = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Emit frame
            self._source.FRAME_READY.emit(converted, frame_index)
            frame_index += 1

            # FPS control
            self._source._update_fps()

    def stop(self) -> None:
        """Stop the capture loop."""
        with QMutexLocker(self._mutex):
            self._running = False


class CameraSource(FrameSource):
    """Frame source for live camera capture.

    Uses OpenCV VideoCapture for camera access.
    Runs capture in a separate thread to avoid UI blocking.

    Example:
        source = CameraSource()
        source.open("0")  # Device ID as string
        source.start()    # Begins emitting FRAME_READY signals
    """

    def __init__(self) -> None:
        super().__init__()
        self._cap: Optional[cv2.VideoCapture] = None
        self._device_id: int = 0
        self._worker: Optional[CameraWorker] = None
        self._frame_count = 0
        self._last_fps_time = 0.0
        self._fps_frame_count = 0

    @property
    def is_live(self) -> bool:
        """Camera is a live source."""
        return True

    @property
    def total_frames(self) -> int:
        """Live source has no total frames."""
        return 0

    def open(self, path: str) -> bool:
        """Open a camera device.

        Args:
            path: Device ID as string (e.g., "0" for first camera).

        Returns:
            True if camera opened successfully.
        """
        try:
            device_id = int(path)
        except ValueError:
            self.ERROR_OCCURRED.emit(f"Invalid device ID: {path}")
            return False

        # Close previous capture if any
        self.close()

        cap = cv2.VideoCapture(device_id)

        if not cap.isOpened():
            self.ERROR_OCCURRED.emit(f"Failed to open camera {device_id}")
            return False

        self._cap = cap
        self._device_id = device_id

        # Get camera properties
        self._fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        return True

    def close(self) -> None:
        """Close the camera and release resources."""
        self.stop()

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        self._device_id = 0
        self._frame_count = 0

    def start(self) -> None:
        """Start capturing frames."""
        if self._cap is None or not self._cap.isOpened():
            self.ERROR_OCCURRED.emit("No camera opened. Call open() first.")
            return

        if self._worker is not None and self._worker.isRunning():
            return  # Already running

        self._worker = CameraWorker(self)
        self._worker.start()
        self._set_state(SourceState.PLAYING)

        # Initialize FPS tracking
        import time
        self._last_fps_time = time.time()
        self._fps_frame_count = 0

    def stop(self) -> None:
        """Stop capturing frames."""
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait()  # Wait for thread to finish
            self._worker = None

        self._set_state(SourceState.STOPPED)

    def pause(self) -> None:
        """Pause is not supported for live camera (same as stop)."""
        self.stop()

    def seek(self, frame_index: int) -> bool:
        """Seek is not supported for live camera."""
        return False

    def get_frame(self, frame_index: int) -> Optional[NDArray[np.uint8]]:
        """Get current frame (frame_index is ignored for live source).

        Returns:
            Current camera frame as uint8 array (grayscale or RGB).
        """
        if self._cap is None or not self._cap.isOpened():
            return None

        ret, frame = self._cap.read()

        if not ret or frame is None:
            return None

        if self._grayscale:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def get_camera_info(self) -> dict:
        """Get camera properties.

        Returns:
            Dictionary with camera properties.
        """
        if self._cap is None:
            return {}

        return {
            "device_id": self._device_id,
            "width": int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self._fps,
            "backend": self._cap.getBackendName(),
            "brightness": self._cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": self._cap.get(cv2.CAP_PROP_CONTRAST),
            "exposure": self._cap.get(cv2.CAP_PROP_EXPOSURE),
        }

    def set_resolution(self, width: int, height: int) -> bool:
        """Set camera resolution.

        Args:
            width: Desired width in pixels.
            height: Desired height in pixels.

        Returns:
            True if resolution was set successfully.
        """
        if self._cap is None:
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Verify
        actual_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return actual_width == width and actual_height == height

    def set_exposure(self, exposure: float) -> bool:
        """Set camera exposure.

        Args:
            exposure: Exposure value (camera-dependent).

        Returns:
            True if exposure was set successfully.
        """
        if self._cap is None:
            return False

        return self._cap.set(cv2.CAP_PROP_EXPOSURE, exposure)

    def set_brightness(self, brightness: float) -> bool:
        """Set camera brightness.

        Args:
            brightness: Brightness value (typically 0-255).

        Returns:
            True if brightness was set successfully.
        """
        if self._cap is None:
            return False

        return self._cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)

    def _update_fps(self) -> None:
        """Update FPS calculation."""
        import time

        self._fps_frame_count += 1
        current_time = time.time()
        elapsed = current_time - self._last_fps_time

        if elapsed >= 1.0:  # Update every second
            actual_fps = self._fps_frame_count / elapsed
            self.FPS_UPDATED.emit(actual_fps)
            self._last_fps_time = current_time
            self._fps_frame_count = 0
