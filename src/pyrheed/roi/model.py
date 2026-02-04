"""ROI data model.

Defines the ROI class and ROIManager for managing multiple regions of interest.
"""

from dataclasses import dataclass, field
from typing import Iterator, Optional
import uuid


# Default color palette for ROIs
DEFAULT_COLORS = [
    "#FF6B6B",  # Red
    "#4ECDC4",  # Teal
    "#45B7D1",  # Blue
    "#96CEB4",  # Green
    "#FFEAA7",  # Yellow
    "#DDA0DD",  # Plum
    "#98D8C8",  # Mint
    "#F7DC6F",  # Gold
    "#BB8FCE",  # Purple
    "#85C1E9",  # Light Blue
]


def _generate_id() -> str:
    """Generate a unique ROI ID."""
    return str(uuid.uuid4())[:8]


@dataclass
class ROI:
    """Region of Interest on an image.

    Attributes:
        x: Left edge x coordinate.
        y: Top edge y coordinate.
        width: Width in pixels.
        height: Height in pixels.
        id: Unique identifier.
        color: Display color in #RRGGBB format.
        label: Optional display label.
    """

    x: int
    y: int
    width: int
    height: int
    id: str = field(default_factory=_generate_id)
    color: str = field(default_factory=lambda: DEFAULT_COLORS[0])
    label: Optional[str] = None

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)

    @property
    def center(self) -> tuple[int, int]:
        """Return center point (cx, cy)."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains(self, px: int, py: int) -> bool:
        """Check if point (px, py) is inside this ROI."""
        return (
            self.x <= px < self.x + self.width
            and self.y <= py < self.y + self.height
        )


class ROIManager:
    """Manages a collection of ROIs.

    Provides methods to add, remove, update, and query ROIs.
    Automatically assigns unique colors to new ROIs.

    Example:
        manager = ROIManager()
        roi = manager.add(x=100, y=100, width=50, height=50)
        print(f"Created ROI {roi.id} with color {roi.color}")
    """

    def __init__(self) -> None:
        self._rois: dict[str, ROI] = {}
        self._color_index = 0

    def __len__(self) -> int:
        return len(self._rois)

    def __contains__(self, roi_id: str) -> bool:
        return roi_id in self._rois

    def __iter__(self) -> Iterator[ROI]:
        return iter(self._rois.values())

    def _next_color(self) -> str:
        """Get next color from palette."""
        color = DEFAULT_COLORS[self._color_index % len(DEFAULT_COLORS)]
        self._color_index += 1
        return color

    def add(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Optional[str] = None,
        label: Optional[str] = None,
    ) -> ROI:
        """Add a new ROI.

        Args:
            x: Left edge x coordinate.
            y: Top edge y coordinate.
            width: Width in pixels.
            height: Height in pixels.
            color: Optional color (auto-assigned if not provided).
            label: Optional display label.

        Returns:
            The created ROI.
        """
        roi_color = color if color else self._next_color()
        roi = ROI(
            x=x,
            y=y,
            width=width,
            height=height,
            color=roi_color,
            label=label,
        )
        self._rois[roi.id] = roi
        return roi

    def get(self, roi_id: str) -> Optional[ROI]:
        """Get ROI by ID.

        Args:
            roi_id: The ROI identifier.

        Returns:
            The ROI if found, None otherwise.
        """
        return self._rois.get(roi_id)

    def remove(self, roi_id: str) -> bool:
        """Remove ROI by ID.

        Args:
            roi_id: The ROI identifier.

        Returns:
            True if removed, False if not found.
        """
        if roi_id in self._rois:
            del self._rois[roi_id]
            return True
        return False

    def update(self, roi_id: str, **kwargs) -> bool:
        """Update ROI properties.

        Args:
            roi_id: The ROI identifier.
            **kwargs: Properties to update (x, y, width, height, color, label).

        Returns:
            True if updated, False if ROI not found.
        """
        roi = self._rois.get(roi_id)
        if roi is None:
            return False

        for key, value in kwargs.items():
            if hasattr(roi, key) and key != "id":
                setattr(roi, key, value)

        return True

    def clear(self) -> None:
        """Remove all ROIs."""
        self._rois.clear()
        self._color_index = 0
