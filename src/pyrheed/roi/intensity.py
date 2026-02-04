"""ROI intensity calculation and tracking.

Provides functions to calculate mean intensity within ROIs
and track intensity changes over time.
"""

from collections import defaultdict
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from pyrheed.roi.model import ROI


def calculate_frame_intensity(
    frame: NDArray[np.uint8],
    normalize: bool = True
) -> float:
    """Calculate mean intensity of entire frame.

    Args:
        frame: Image frame (grayscale or RGB).
        normalize: If True, normalize by image max value (0-1 range).

    Returns:
        Mean intensity value.
        If normalized, returns value in range [0, 1].
    """
    # Convert to grayscale if color
    if frame.ndim == 2:
        grayscale = frame.astype(np.float32)
    else:
        # Convert RGB to grayscale using luminosity method
        grayscale = (
            0.299 * frame[:, :, 0] +
            0.587 * frame[:, :, 1] +
            0.114 * frame[:, :, 2]
        ).astype(np.float32)

    mean_intensity = float(np.mean(grayscale))

    if normalize:
        img_max = float(np.max(grayscale))
        if img_max > 0:
            return mean_intensity / img_max
        return 0.0

    return mean_intensity


def calculate_roi_intensity(
    frame: NDArray[np.uint8],
    roi: ROI,
    normalize: bool = True
) -> Optional[float]:
    """Calculate mean intensity within an ROI.

    Args:
        frame: Image frame (grayscale or RGB).
        roi: Region of interest.
        normalize: If True, normalize by image max value (0-1 range).

    Returns:
        Mean intensity value, or None if ROI is outside image.
        If normalized, returns value in range [0, 1].
    """
    # Get frame dimensions
    if frame.ndim == 2:
        height, width = frame.shape
        grayscale = frame.astype(np.float32)
    else:
        height, width = frame.shape[:2]
        # Convert RGB to grayscale using luminosity method
        grayscale = (
            0.299 * frame[:, :, 0] +
            0.587 * frame[:, :, 1] +
            0.114 * frame[:, :, 2]
        ).astype(np.float32)

    # Calculate intersection with image bounds
    x1 = max(0, roi.x)
    y1 = max(0, roi.y)
    x2 = min(width, roi.x + roi.width)
    y2 = min(height, roi.y + roi.height)

    # Check if ROI is completely outside image
    if x1 >= x2 or y1 >= y2:
        return None

    # Extract region and calculate mean
    region = grayscale[y1:y2, x1:x2]
    mean_intensity = float(np.mean(region))

    # Normalize by image max if requested
    if normalize:
        img_max = float(np.max(grayscale))
        if img_max > 0:
            return mean_intensity / img_max
        return 0.0

    return mean_intensity


class IntensityTracker:
    """Tracks intensity measurements over time for multiple ROIs.

    Maintains a history of intensity values for each ROI,
    useful for plotting intensity trends. Uses frame_index as key
    to avoid duplicate entries when replaying the same frame.

    Example:
        tracker = IntensityTracker()
        tracker.add("roi1", frame_index=0, intensity=100.0)
        tracker.add("roi1", frame_index=1, intensity=105.0)
        history = tracker.get_history("roi1")  # [(0, 100.0), (1, 105.0)]
    """

    def __init__(self, max_history: int = 1000) -> None:
        """Initialize tracker.

        Args:
            max_history: Maximum number of measurements to keep per ROI.
        """
        # Store as dict[roi_id, dict[frame_index, intensity]]
        self._data: dict[str, dict[int, float]] = defaultdict(dict)
        self._max_history = max_history

    def __len__(self) -> int:
        return len(self._data)

    def add(self, roi_id: str, frame_index: int, intensity: float) -> None:
        """Add or update intensity measurement.

        If the same frame_index already exists, it will be updated.

        Args:
            roi_id: ROI identifier.
            frame_index: Frame number.
            intensity: Measured intensity value.
        """
        data = self._data[roi_id]
        data[frame_index] = intensity

        # Trim to max length if exceeded
        if len(data) > self._max_history:
            # Keep most recent entries
            sorted_keys = sorted(data.keys())
            for key in sorted_keys[:-self._max_history]:
                del data[key]

    def get_history(self, roi_id: str) -> list[tuple[int, float]]:
        """Get intensity history for ROI.

        Args:
            roi_id: ROI identifier.

        Returns:
            List of (frame_index, intensity) tuples, sorted by frame_index.
        """
        data = self._data.get(roi_id, {})
        return sorted(data.items())

    def get_latest(self, roi_id: str) -> Optional[float]:
        """Get most recent intensity for ROI.

        Args:
            roi_id: ROI identifier.

        Returns:
            Latest intensity value, or None if no history.
        """
        data = self._data.get(roi_id)
        if data:
            max_frame = max(data.keys())
            return data[max_frame]
        return None

    def clear_roi(self, roi_id: str) -> None:
        """Clear history for specific ROI.

        Args:
            roi_id: ROI identifier.
        """
        if roi_id in self._data:
            del self._data[roi_id]

    def clear(self) -> None:
        """Clear all history."""
        self._data.clear()

    def frame_count(self, roi_id: str) -> int:
        """Get number of recorded frames for ROI.

        Args:
            roi_id: ROI identifier.

        Returns:
            Number of frames with recorded intensity.
        """
        return len(self._data.get(roi_id, {}))
