"""Tests for ROI graphics components."""

import pytest
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsScene

from pyrheed.roi.model import ROI
from pyrheed.roi.graphics import ROIGraphicsItem


class TestROIGraphicsItem:
    """Tests for ROIGraphicsItem."""

    @pytest.fixture
    def scene(self, qtbot):
        """Create a QGraphicsScene for testing."""
        return QGraphicsScene()

    @pytest.fixture
    def roi(self):
        """Create a test ROI."""
        return ROI(x=100, y=100, width=50, height=30, color="#FF0000")

    def test_create_item(self, scene, roi) -> None:
        """Can create graphics item from ROI."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        assert item.roi is roi

    def test_item_position(self, scene, roi) -> None:
        """Item should be positioned at ROI coordinates."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        assert item.pos().x() == 100
        assert item.pos().y() == 100

    def test_item_size(self, scene, roi) -> None:
        """Item should have ROI dimensions."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        rect = item.rect()  # Use rect() not boundingRect()
        assert rect.width() == 50
        assert rect.height() == 30

    def test_item_color(self, scene, roi) -> None:
        """Item should use ROI color."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        # Pen color should match ROI color
        assert item.pen().color() == QColor("#FF0000")

    def test_item_is_selectable(self, scene, roi) -> None:
        """Item should be selectable."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        assert item.flags() & item.GraphicsItemFlag.ItemIsSelectable

    def test_item_is_movable(self, scene, roi) -> None:
        """Item should be movable."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        assert item.flags() & item.GraphicsItemFlag.ItemIsMovable

    def test_sync_to_roi(self, scene, roi) -> None:
        """Item should sync position back to ROI."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        item.setPos(200, 300)
        item.sync_to_roi()
        assert roi.x == 200
        assert roi.y == 300

    def test_sync_from_roi(self, scene, roi) -> None:
        """Item should update from ROI changes."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        roi.x = 200
        roi.y = 300
        item.sync_from_roi()
        assert item.pos().x() == 200
        assert item.pos().y() == 300

    def test_item_shows_label(self, scene) -> None:
        """Item should show label if ROI has one."""
        roi = ROI(x=100, y=100, width=50, height=30, label="Test ROI")
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        # Label should be visible
        assert item.label_item is not None
        assert item.label_item.toPlainText() == "Test ROI"

    def test_resize_handles_visible_when_selected(self, scene, roi) -> None:
        """Resize handles should be visible when item is selected."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        item.setSelected(True)
        assert item.handles_visible is True

    def test_resize_handles_hidden_when_not_selected(self, scene, roi) -> None:
        """Resize handles should be hidden when item is not selected."""
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
        item.setSelected(False)
        assert item.handles_visible is False
