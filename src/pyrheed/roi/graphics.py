"""ROI graphics components.

QGraphicsItem subclasses for visualizing ROIs on a QGraphicsScene.
"""

from enum import IntEnum
from typing import Optional

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QCursor
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsItem,
    QStyleOptionGraphicsItem,
    QWidget,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
    QStyle,
)

from pyrheed.roi.model import ROI


class HandlePosition(IntEnum):
    """Handle positions for resizing."""
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4


class ROIGraphicsItem(QGraphicsRectItem):
    """Graphics item representing an ROI.

    Provides visual representation of an ROI with:
    - Colored border matching ROI color
    - Semi-transparent fill
    - Optional label display
    - Resize handles when selected
    - Drag to move, drag handles to resize

    Example:
        scene = QGraphicsScene()
        roi = ROI(x=100, y=100, width=50, height=50)
        item = ROIGraphicsItem(roi)
        scene.addItem(item)
    """

    HANDLE_SIZE = 8
    MIN_SIZE = 10  # Minimum ROI size

    def __init__(self, roi: ROI, parent: Optional[QGraphicsItem] = None) -> None:
        # Initialize with rect dimensions
        super().__init__(0, 0, roi.width, roi.height, parent)
        self._roi = roi
        self._handles_visible = False
        self._resizing = False
        self._resize_handle = HandlePosition.NONE
        self._resize_start_rect: Optional[QRectF] = None
        self._resize_start_pos: Optional[QPointF] = None
        self._resize_start_scene_pos: Optional[QPointF] = None
        self._resize_start_item_pos: Optional[QPointF] = None

        # Setup appearance
        self._setup_appearance()

        # Setup interaction flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        # Position from ROI
        self.setPos(roi.x, roi.y)

        # Create label if ROI has one
        self._label_item: Optional[QGraphicsTextItem] = None
        if roi.label:
            self._create_label()

    @property
    def roi(self) -> ROI:
        """Get the associated ROI."""
        return self._roi

    @property
    def label_item(self) -> Optional[QGraphicsTextItem]:
        """Get the label text item."""
        return self._label_item

    @property
    def handles_visible(self) -> bool:
        """Whether resize handles are visible."""
        return self._handles_visible

    def _setup_appearance(self) -> None:
        """Setup pen and brush based on ROI color."""
        color = QColor(self._roi.color)
        pen = QPen(color, 2)
        self.setPen(pen)

        # Semi-transparent fill
        fill_color = QColor(color)
        fill_color.setAlpha(40)
        self.setBrush(QBrush(fill_color))

    def _create_label(self) -> None:
        """Create label text item."""
        self._label_item = QGraphicsTextItem(self._roi.label, self)
        self._label_item.setDefaultTextColor(QColor(self._roi.color))
        # Position label above the ROI
        self._label_item.setPos(0, -20)

    def sync_to_roi(self) -> None:
        """Sync current position/size to ROI data."""
        pos = self.pos()
        rect = self.rect()
        self._roi.x = int(pos.x())
        self._roi.y = int(pos.y())
        self._roi.width = int(rect.width())
        self._roi.height = int(rect.height())

    def sync_from_roi(self) -> None:
        """Update item from ROI data."""
        self.setPos(self._roi.x, self._roi.y)
        self.setRect(0, 0, self._roi.width, self._roi.height)
        self._setup_appearance()

    def _get_handle_rects(self) -> dict[HandlePosition, QRectF]:
        """Get rectangles for all handles."""
        rect = self.rect()
        hs = self.HANDLE_SIZE
        return {
            HandlePosition.TOP_LEFT: QRectF(-hs/2, -hs/2, hs, hs),
            HandlePosition.TOP_RIGHT: QRectF(rect.width() - hs/2, -hs/2, hs, hs),
            HandlePosition.BOTTOM_LEFT: QRectF(-hs/2, rect.height() - hs/2, hs, hs),
            HandlePosition.BOTTOM_RIGHT: QRectF(rect.width() - hs/2, rect.height() - hs/2, hs, hs),
        }

    def _handle_at(self, pos: QPointF) -> HandlePosition:
        """Get handle at given position, or NONE."""
        if not self._handles_visible:
            return HandlePosition.NONE

        for handle, rect in self._get_handle_rects().items():
            if rect.contains(pos):
                return handle
        return HandlePosition.NONE

    def _cursor_for_handle(self, handle: HandlePosition) -> Qt.CursorShape:
        """Get cursor shape for handle."""
        if handle in (HandlePosition.TOP_LEFT, HandlePosition.BOTTOM_RIGHT):
            return Qt.CursorShape.SizeFDiagCursor
        elif handle in (HandlePosition.TOP_RIGHT, HandlePosition.BOTTOM_LEFT):
            return Qt.CursorShape.SizeBDiagCursor
        return Qt.CursorShape.ArrowCursor

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Change cursor when hovering over handles."""
        handle = self._handle_at(event.pos())
        if handle != HandlePosition.NONE:
            self.setCursor(QCursor(self._cursor_for_handle(handle)))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Start resizing if clicking on handle."""
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._handle_at(event.pos())
            if handle != HandlePosition.NONE:
                self._resizing = True
                self._resize_handle = handle
                self._resize_start_rect = QRectF(self.rect())
                self._resize_start_pos = event.pos()
                self._resize_start_scene_pos = event.scenePos()
                self._resize_start_item_pos = self.pos()
                # Disable moving while resizing
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Resize ROI when dragging handle."""
        if self._resizing and self._resize_start_rect is not None:
            # Use scene coordinates for more stable resizing
            current_scene_pos = event.scenePos()
            start_scene_pos = self.mapToScene(self._resize_start_pos) if self._resize_start_pos else current_scene_pos

            old_rect = self._resize_start_rect
            old_pos = self._resize_start_scene_pos

            delta_x = current_scene_pos.x() - old_pos.x()
            delta_y = current_scene_pos.y() - old_pos.y()

            new_x = self._resize_start_item_pos.x()
            new_y = self._resize_start_item_pos.y()
            new_w = old_rect.width()
            new_h = old_rect.height()

            # Adjust based on which handle is being dragged
            if self._resize_handle == HandlePosition.TOP_LEFT:
                new_x += delta_x
                new_y += delta_y
                new_w -= delta_x
                new_h -= delta_y
            elif self._resize_handle == HandlePosition.TOP_RIGHT:
                new_y += delta_y
                new_w += delta_x
                new_h -= delta_y
            elif self._resize_handle == HandlePosition.BOTTOM_LEFT:
                new_x += delta_x
                new_w -= delta_x
                new_h += delta_y
            elif self._resize_handle == HandlePosition.BOTTOM_RIGHT:
                new_w += delta_x
                new_h += delta_y

            # Apply minimum size constraint
            if new_w >= self.MIN_SIZE and new_h >= self.MIN_SIZE:
                self.prepareGeometryChange()
                self.setPos(new_x, new_y)
                self.setRect(0, 0, new_w, new_h)
                self.sync_to_roi()

            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Finish resizing."""
        if self._resizing:
            self._resizing = False
            self._resize_handle = HandlePosition.NONE
            self._resize_start_rect = None
            self._resize_start_pos = None
            self._resize_start_scene_pos = None
            self._resize_start_item_pos = None
            # Re-enable moving
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.sync_to_roi()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def itemChange(
        self, change: QGraphicsItem.GraphicsItemChange, value
    ):
        """Handle item changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._handles_visible = bool(value)
            self.update()
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Sync position to ROI when moved
            self.sync_to_roi()
        return super().itemChange(change, value)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        """Paint the ROI rectangle and handles."""
        # Remove default selection rectangle by clearing the state
        option.state &= ~QStyle.StateFlag.State_Selected

        # Draw main rectangle
        super().paint(painter, option, widget)

        # Draw resize handles if selected
        if self._handles_visible:
            self._draw_handles(painter)

    def _draw_handles(self, painter: QPainter) -> None:
        """Draw resize handles at corners."""
        painter.setPen(QPen(QColor(self._roi.color), 1))
        painter.setBrush(QBrush(QColor("white")))

        for handle_rect in self._get_handle_rects().values():
            painter.drawRect(handle_rect)

    def boundingRect(self) -> QRectF:
        """Return bounding rectangle including handles."""
        rect = super().boundingRect()
        if self._handles_visible:
            # Expand for handles and label
            hs = self.HANDLE_SIZE
            return rect.adjusted(-hs, -22, hs, hs)
        return rect
