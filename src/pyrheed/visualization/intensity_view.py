"""Intensity visualization widgets.

Provides different visualization methods for image intensity distribution:
- Heatmap: 2D color-coded intensity map
- Contour: 2D contour lines
- Surface: 3D surface plot
"""

from typing import Optional

import numpy as np
from numpy.typing import NDArray

# Ensure matplotlib uses Qt backend before importing pyplot
import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer


class IntensityHeatmap(QWidget):
    """Heatmap visualization of image intensity.

    Displays the current frame as a color-coded heatmap where
    color represents intensity value.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._figure = Figure(figsize=(4, 4), dpi=100)
        self._canvas = FigureCanvas(self._figure)
        self._ax = self._figure.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        # Initial setup
        self._image = None
        self._colorbar = None
        self._cmap = "viridis"

        self._ax.set_title("Intensity Heatmap")
        self._figure.tight_layout()

    def set_colormap(self, cmap: str) -> None:
        """Set the colormap."""
        self._cmap = cmap
        if self._image is not None:
            self._image.set_cmap(cmap)
            self._canvas.draw_idle()

    def update_frame(self, frame: NDArray[np.uint8]) -> None:
        """Update with new frame data.

        Args:
            frame: Grayscale or RGB image array.
        """
        # Convert to grayscale if needed
        if frame.ndim == 3:
            gray = (
                0.299 * frame[:, :, 0] +
                0.587 * frame[:, :, 1] +
                0.114 * frame[:, :, 2]
            ).astype(np.float32)
        else:
            gray = frame.astype(np.float32)

        # Normalize to 0-1
        max_val = np.max(gray)
        if max_val > 0:
            gray = gray / max_val

        if self._image is None:
            self._image = self._ax.imshow(
                gray, cmap=self._cmap, vmin=0, vmax=1,
                aspect="equal", interpolation="nearest"
            )
            self._colorbar = self._figure.colorbar(self._image, ax=self._ax)
            self._colorbar.set_label("Normalized Intensity")
        else:
            self._image.set_data(gray)

        self._canvas.draw_idle()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._image = None
        self._colorbar = None
        self._ax.set_title("Intensity Heatmap")
        self._canvas.draw_idle()


class IntensityContour(QWidget):
    """Contour visualization of image intensity.

    Displays intensity as contour lines.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._figure = Figure(figsize=(4, 4), dpi=100)
        self._canvas = FigureCanvas(self._figure)
        self._ax = self._figure.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        self._cmap = "viridis"
        self._levels = 10
        self._contour = None

        self._ax.set_title("Intensity Contour")
        self._figure.tight_layout()

    def set_colormap(self, cmap: str) -> None:
        """Set the colormap."""
        self._cmap = cmap

    def set_levels(self, levels: int) -> None:
        """Set number of contour levels."""
        self._levels = levels

    def update_frame(self, frame: NDArray[np.uint8]) -> None:
        """Update with new frame data."""
        # Convert to grayscale if needed
        if frame.ndim == 3:
            gray = (
                0.299 * frame[:, :, 0] +
                0.587 * frame[:, :, 1] +
                0.114 * frame[:, :, 2]
            ).astype(np.float32)
        else:
            gray = frame.astype(np.float32)

        # Normalize
        max_val = np.max(gray)
        if max_val > 0:
            gray = gray / max_val

        # Downsample for performance if large
        h, w = gray.shape
        max_size = 200
        if h > max_size or w > max_size:
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            # Simple downsampling
            gray = gray[::h // new_h, ::w // new_w]

        self._ax.clear()
        self._contour = self._ax.contourf(
            gray, levels=self._levels, cmap=self._cmap
        )
        self._ax.set_title("Intensity Contour")
        self._ax.set_aspect("equal")
        self._canvas.draw_idle()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._contour = None
        self._ax.set_title("Intensity Contour")
        self._canvas.draw_idle()


class IntensitySurface(QWidget):
    """3D surface visualization of image intensity.

    Displays intensity as a 3D surface where height represents intensity.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._figure = Figure(figsize=(4, 4), dpi=100)
        self._canvas = FigureCanvas(self._figure)
        self._ax = self._figure.add_subplot(111, projection="3d")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        self._cmap = "viridis"
        self._surface = None

        self._ax.set_title("Intensity Surface")
        self._figure.tight_layout()

    def set_colormap(self, cmap: str) -> None:
        """Set the colormap."""
        self._cmap = cmap

    def update_frame(self, frame: NDArray[np.uint8]) -> None:
        """Update with new frame data."""
        # Convert to grayscale if needed
        if frame.ndim == 3:
            gray = (
                0.299 * frame[:, :, 0] +
                0.587 * frame[:, :, 1] +
                0.114 * frame[:, :, 2]
            ).astype(np.float32)
        else:
            gray = frame.astype(np.float32)

        # Normalize
        max_val = np.max(gray)
        if max_val > 0:
            gray = gray / max_val

        # Downsample for performance (3D is expensive)
        h, w = gray.shape
        max_size = 100
        if h > max_size or w > max_size:
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            step_h = max(1, h // new_h)
            step_w = max(1, w // new_w)
            gray = gray[::step_h, ::step_w]

        h, w = gray.shape
        x = np.arange(w)
        y = np.arange(h)
        X, Y = np.meshgrid(x, y)

        self._ax.clear()
        self._surface = self._ax.plot_surface(
            X, Y, gray, cmap=self._cmap, linewidth=0, antialiased=False
        )
        self._ax.set_title("Intensity Surface")
        self._ax.set_zlim(0, 1)
        self._ax.set_xlabel("X")
        self._ax.set_ylabel("Y")
        self._ax.set_zlabel("Intensity")
        self._canvas.draw_idle()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._surface = None
        self._ax.set_title("Intensity Surface")
        self._canvas.draw_idle()
