"""Tests for ROI intensity calculation."""

import numpy as np
import pytest

from pyrheed.roi.model import ROI
from pyrheed.roi.intensity import (
    calculate_roi_intensity,
    calculate_frame_intensity,
    IntensityTracker,
)


class TestCalculateFrameIntensity:
    """Tests for calculate_frame_intensity function."""

    def test_calculate_grayscale_normalized(self) -> None:
        """Calculate normalized full-frame intensity."""
        frame = np.full((100, 100), 128, dtype=np.uint8)

        intensity = calculate_frame_intensity(frame, normalize=True)
        assert intensity == 1.0  # All same value: 128/128 = 1.0

    def test_calculate_grayscale_unnormalized(self) -> None:
        """Calculate raw full-frame intensity."""
        frame = np.full((100, 100), 128, dtype=np.uint8)

        intensity = calculate_frame_intensity(frame, normalize=False)
        assert intensity == 128.0

    def test_calculate_color_intensity(self) -> None:
        """Calculate intensity in color image."""
        frame = np.full((100, 100, 3), [100, 150, 200], dtype=np.uint8)

        intensity = calculate_frame_intensity(frame, normalize=False)
        # Weighted mean: 0.299*100 + 0.587*150 + 0.114*200 = 140.75
        assert abs(intensity - 140.75) < 0.1

    def test_varying_intensity_normalized(self) -> None:
        """Calculate normalized intensity in image with varying values."""
        frame = np.arange(0, 256, dtype=np.uint8).reshape(16, 16)

        intensity = calculate_frame_intensity(frame, normalize=True)
        # Mean of 0-255 is 127.5, max is 255
        expected = 127.5 / 255
        assert abs(intensity - expected) < 0.01

    def test_zero_image(self) -> None:
        """Zero image returns 0."""
        frame = np.zeros((100, 100), dtype=np.uint8)

        intensity = calculate_frame_intensity(frame, normalize=True)
        assert intensity == 0.0


class TestCalculateROIIntensity:
    """Tests for calculate_roi_intensity function."""

    def test_calculate_grayscale_intensity_normalized(self) -> None:
        """Calculate normalized intensity in grayscale image."""
        # Create 100x100 image with value 128, max is 128
        frame = np.full((100, 100), 128, dtype=np.uint8)
        roi = ROI(x=10, y=10, width=20, height=20)

        intensity = calculate_roi_intensity(frame, roi, normalize=True)
        assert intensity == 1.0  # 128/128 = 1.0

    def test_calculate_grayscale_intensity_unnormalized(self) -> None:
        """Calculate raw intensity in grayscale image."""
        frame = np.full((100, 100), 128, dtype=np.uint8)
        roi = ROI(x=10, y=10, width=20, height=20)

        intensity = calculate_roi_intensity(frame, roi, normalize=False)
        assert intensity == 128.0

    def test_calculate_color_intensity(self) -> None:
        """Calculate intensity in color image (converts to grayscale)."""
        # Create 100x100 RGB image
        frame = np.full((100, 100, 3), [100, 150, 200], dtype=np.uint8)
        roi = ROI(x=10, y=10, width=20, height=20)

        intensity = calculate_roi_intensity(frame, roi, normalize=False)
        # Should be weighted mean: 0.299*100 + 0.587*150 + 0.114*200 = 140.75
        assert abs(intensity - 140.75) < 0.1

    def test_roi_partial_overlap(self) -> None:
        """ROI partially outside image should only use valid region."""
        frame = np.full((100, 100), 100, dtype=np.uint8)
        roi = ROI(x=90, y=90, width=20, height=20)  # Extends past image

        intensity = calculate_roi_intensity(frame, roi, normalize=True)
        assert intensity == 1.0  # 100/100 = 1.0

    def test_roi_completely_outside(self) -> None:
        """ROI completely outside image returns None."""
        frame = np.full((100, 100), 100, dtype=np.uint8)
        roi = ROI(x=200, y=200, width=20, height=20)

        intensity = calculate_roi_intensity(frame, roi)
        assert intensity is None

    def test_varying_intensity_normalized(self) -> None:
        """Calculate normalized intensity in region with varying values."""
        frame = np.zeros((100, 100), dtype=np.uint8)
        # Set ROI region to gradient 0-255
        frame[10:30, 10:30] = np.arange(0, 400).reshape(20, 20) % 256

        roi = ROI(x=10, y=10, width=20, height=20)
        intensity = calculate_roi_intensity(frame, roi, normalize=True)

        # Mean of (0-399 mod 256) / max(255)
        expected = np.mean(np.arange(0, 400) % 256) / 255
        assert abs(intensity - expected) < 0.01

    def test_default_is_normalized(self) -> None:
        """Default behavior should be normalized."""
        frame = np.full((100, 100), 200, dtype=np.uint8)
        roi = ROI(x=10, y=10, width=20, height=20)

        intensity = calculate_roi_intensity(frame, roi)
        assert intensity == 1.0  # Normalized: 200/200 = 1.0


class TestIntensityTracker:
    """Tests for IntensityTracker."""

    def test_create_tracker(self) -> None:
        """Tracker starts empty."""
        tracker = IntensityTracker()
        assert len(tracker) == 0

    def test_add_measurement(self) -> None:
        """Can add intensity measurement."""
        tracker = IntensityTracker()
        tracker.add("roi1", frame_index=0, intensity=100.0)

        assert len(tracker) == 1
        assert tracker.get_history("roi1") == [(0, 100.0)]

    def test_add_multiple_measurements(self) -> None:
        """Can add multiple measurements for same ROI."""
        tracker = IntensityTracker()
        tracker.add("roi1", 0, 100.0)
        tracker.add("roi1", 1, 110.0)
        tracker.add("roi1", 2, 105.0)

        history = tracker.get_history("roi1")
        assert len(history) == 3
        assert history == [(0, 100.0), (1, 110.0), (2, 105.0)]

    def test_multiple_rois(self) -> None:
        """Can track multiple ROIs independently."""
        tracker = IntensityTracker()
        tracker.add("roi1", 0, 100.0)
        tracker.add("roi2", 0, 200.0)

        assert tracker.get_history("roi1") == [(0, 100.0)]
        assert tracker.get_history("roi2") == [(0, 200.0)]

    def test_get_latest(self) -> None:
        """Can get latest intensity for ROI."""
        tracker = IntensityTracker()
        tracker.add("roi1", 0, 100.0)
        tracker.add("roi1", 1, 110.0)

        assert tracker.get_latest("roi1") == 110.0

    def test_get_latest_nonexistent(self) -> None:
        """Getting latest for nonexistent ROI returns None."""
        tracker = IntensityTracker()
        assert tracker.get_latest("nonexistent") is None

    def test_clear_roi(self) -> None:
        """Can clear history for specific ROI."""
        tracker = IntensityTracker()
        tracker.add("roi1", 0, 100.0)
        tracker.add("roi2", 0, 200.0)

        tracker.clear_roi("roi1")
        assert tracker.get_history("roi1") == []
        assert tracker.get_history("roi2") == [(0, 200.0)]

    def test_clear_all(self) -> None:
        """Can clear all history."""
        tracker = IntensityTracker()
        tracker.add("roi1", 0, 100.0)
        tracker.add("roi2", 0, 200.0)

        tracker.clear()
        assert len(tracker) == 0

    def test_max_history_length(self) -> None:
        """History is limited to max length."""
        tracker = IntensityTracker(max_history=5)

        for i in range(10):
            tracker.add("roi1", i, float(i))

        history = tracker.get_history("roi1")
        assert len(history) == 5
        # Should keep most recent
        assert history[0] == (5, 5.0)
        assert history[-1] == (9, 9.0)

    def test_update_same_frame(self) -> None:
        """Adding same frame_index updates instead of appending."""
        tracker = IntensityTracker()
        tracker.add("roi1", 0, 100.0)
        tracker.add("roi1", 0, 150.0)  # Same frame, should update

        history = tracker.get_history("roi1")
        assert len(history) == 1
        assert history[0] == (0, 150.0)  # Updated value

    def test_frame_count(self) -> None:
        """frame_count returns number of recorded frames."""
        tracker = IntensityTracker()
        tracker.add("roi1", 0, 100.0)
        tracker.add("roi1", 1, 110.0)
        tracker.add("roi1", 0, 105.0)  # Update frame 0

        assert tracker.frame_count("roi1") == 2
        assert tracker.frame_count("nonexistent") == 0
