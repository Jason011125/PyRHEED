"""ROI (Region of Interest) management module.

Provides tools for defining, managing, and visualizing regions of interest
on RHEED images for intensity tracking.
"""

from pyrheed.roi.model import ROI, ROIManager
from pyrheed.roi.graphics import ROIGraphicsItem
from pyrheed.roi.intensity import (
    calculate_roi_intensity,
    calculate_frame_intensity,
    IntensityTracker,
)

__all__ = [
    "ROI",
    "ROIManager",
    "ROIGraphicsItem",
    "calculate_roi_intensity",
    "calculate_frame_intensity",
    "IntensityTracker",
]
