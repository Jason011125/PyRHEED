"""Tests for ROI model."""

import pytest
import numpy as np

from pyrheed.roi.model import ROI, ROIManager


class TestROI:
    """Tests for ROI dataclass."""

    def test_create_roi(self) -> None:
        """ROI can be created with position and size."""
        roi = ROI(x=100, y=200, width=50, height=30)
        assert roi.x == 100
        assert roi.y == 200
        assert roi.width == 50
        assert roi.height == 30

    def test_roi_has_unique_id(self) -> None:
        """Each ROI should have a unique ID."""
        roi1 = ROI(x=0, y=0, width=10, height=10)
        roi2 = ROI(x=0, y=0, width=10, height=10)
        assert roi1.id != roi2.id

    def test_roi_has_default_color(self) -> None:
        """ROI should have a default color."""
        roi = ROI(x=0, y=0, width=10, height=10)
        assert roi.color is not None
        assert len(roi.color) == 7  # "#RRGGBB" format

    def test_roi_custom_color(self) -> None:
        """ROI can have custom color."""
        roi = ROI(x=0, y=0, width=10, height=10, color="#FF0000")
        assert roi.color == "#FF0000"

    def test_roi_has_label(self) -> None:
        """ROI can have an optional label."""
        roi = ROI(x=0, y=0, width=10, height=10, label="ROI 1")
        assert roi.label == "ROI 1"

    def test_roi_bounds(self) -> None:
        """ROI should provide bounds as tuple."""
        roi = ROI(x=100, y=200, width=50, height=30)
        assert roi.bounds == (100, 200, 50, 30)

    def test_roi_center(self) -> None:
        """ROI should calculate center point."""
        roi = ROI(x=100, y=200, width=50, height=30)
        assert roi.center == (125, 215)

    def test_roi_contains_point(self) -> None:
        """ROI should check if point is inside."""
        roi = ROI(x=100, y=100, width=50, height=50)
        assert roi.contains(125, 125) is True
        assert roi.contains(100, 100) is True  # Edge
        assert roi.contains(149, 149) is True  # Edge
        assert roi.contains(50, 50) is False   # Outside
        assert roi.contains(200, 200) is False # Outside


class TestROIManager:
    """Tests for ROIManager."""

    def test_create_manager(self) -> None:
        """Manager starts with no ROIs."""
        manager = ROIManager()
        assert len(manager) == 0

    def test_add_roi(self) -> None:
        """Can add ROI to manager."""
        manager = ROIManager()
        roi = manager.add(x=100, y=100, width=50, height=50)
        assert len(manager) == 1
        assert roi.id in manager

    def test_add_multiple_rois(self) -> None:
        """Can add multiple ROIs."""
        manager = ROIManager()
        roi1 = manager.add(x=0, y=0, width=10, height=10)
        roi2 = manager.add(x=100, y=100, width=20, height=20)
        assert len(manager) == 2
        assert roi1.id in manager
        assert roi2.id in manager

    def test_get_roi_by_id(self) -> None:
        """Can get ROI by ID."""
        manager = ROIManager()
        roi = manager.add(x=100, y=100, width=50, height=50)
        retrieved = manager.get(roi.id)
        assert retrieved is roi

    def test_get_nonexistent_roi(self) -> None:
        """Getting nonexistent ROI returns None."""
        manager = ROIManager()
        assert manager.get("nonexistent") is None

    def test_remove_roi(self) -> None:
        """Can remove ROI by ID."""
        manager = ROIManager()
        roi = manager.add(x=100, y=100, width=50, height=50)
        result = manager.remove(roi.id)
        assert result is True
        assert len(manager) == 0
        assert roi.id not in manager

    def test_remove_nonexistent_roi(self) -> None:
        """Removing nonexistent ROI returns False."""
        manager = ROIManager()
        assert manager.remove("nonexistent") is False

    def test_update_roi(self) -> None:
        """Can update ROI properties."""
        manager = ROIManager()
        roi = manager.add(x=100, y=100, width=50, height=50)
        manager.update(roi.id, x=200, y=200)
        updated = manager.get(roi.id)
        assert updated.x == 200
        assert updated.y == 200
        assert updated.width == 50  # Unchanged

    def test_iterate_rois(self) -> None:
        """Can iterate over all ROIs."""
        manager = ROIManager()
        manager.add(x=0, y=0, width=10, height=10)
        manager.add(x=100, y=100, width=20, height=20)
        rois = list(manager)
        assert len(rois) == 2

    def test_clear_all_rois(self) -> None:
        """Can clear all ROIs."""
        manager = ROIManager()
        manager.add(x=0, y=0, width=10, height=10)
        manager.add(x=100, y=100, width=20, height=20)
        manager.clear()
        assert len(manager) == 0

    def test_rois_have_unique_colors(self) -> None:
        """Auto-assigned colors should be unique."""
        manager = ROIManager()
        roi1 = manager.add(x=0, y=0, width=10, height=10)
        roi2 = manager.add(x=100, y=100, width=20, height=20)
        roi3 = manager.add(x=200, y=200, width=30, height=30)
        colors = {roi1.color, roi2.color, roi3.color}
        assert len(colors) == 3  # All different
