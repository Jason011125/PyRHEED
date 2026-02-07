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

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt


class IntensityHeatmap(QWidget):
    """Heatmap visualization of image intensity.

    Displays the current frame as a color-coded heatmap where
    color represents intensity value.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题作为独立 Widget（像 Web 一样）
        self._title_label = QLabel("Intensity Heatmap")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet("""
            QLabel {
                color: #B4B3AF;
                font-size: 16px;
                padding: 8px 0;
                background-color: transparent;
            }
        """)
        layout.addWidget(self._title_label)

        # Matplotlib 图表
        self._figure = Figure(figsize=(4, 4), dpi=100, facecolor='#2F3437')
        self._canvas = FigureCanvas(self._figure)
        self._ax = self._figure.add_subplot(111, facecolor='#252729')
        layout.addWidget(self._canvas)

        # Initial setup
        self._image = None
        self._colorbar = None
        self._cmap = "viridis"

        # 暗色主题样式（不设置标题，因为已经用 QLabel 了）
        self._ax.tick_params(colors='#9B9A97', which='both')
        for spine in self._ax.spines.values():
            spine.set_color('#4F5458')
        # 统一布局参数
        self._figure.subplots_adjust(left=0.12, right=0.88, top=0.95, bottom=0.1)

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
            self._colorbar.set_label("Normalized Intensity", color='#B4B3AF')
            self._colorbar.ax.tick_params(colors='#9B9A97')
            for spine in self._colorbar.ax.spines.values():
                spine.set_color('#4F5458')
        else:
            self._image.set_data(gray)

        self._canvas.draw_idle()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._image = None
        self._colorbar = None
        self._canvas.draw_idle()


class IntensityContour(QWidget):
    """Contour visualization of image intensity.

    Displays intensity as contour lines.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题作为独立 Widget（像 Web 一样）
        self._title_label = QLabel("Intensity Contour")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet("""
            QLabel {
                color: #B4B3AF;
                font-size: 16px;
                padding: 8px 0;
                background-color: transparent;
            }
        """)
        layout.addWidget(self._title_label)

        # Matplotlib 图表
        self._figure = Figure(figsize=(4, 4), dpi=100, facecolor='#2F3437')
        self._canvas = FigureCanvas(self._figure)
        self._ax = self._figure.add_subplot(111, facecolor='#252729')
        layout.addWidget(self._canvas)

        self._cmap = "viridis"
        self._levels = 10
        self._contour = None

        # 暗色主题样式（不设置标题，因为已经用 QLabel 了）
        self._ax.tick_params(colors='#9B9A97', which='both')
        for spine in self._ax.spines.values():
            spine.set_color('#4F5458')
        # 统一布局参数
        self._figure.subplots_adjust(left=0.12, right=0.88, top=0.95, bottom=0.1)

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
        self._ax.set_facecolor('#252729')  # 重新设置背景色
        self._contour = self._ax.contourf(
            gray, levels=self._levels, cmap=self._cmap
        )
        self._ax.set_aspect("equal")
        self._ax.tick_params(colors='#9B9A97', which='both')
        for spine in self._ax.spines.values():
            spine.set_color('#4F5458')
        self._canvas.draw_idle()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._contour = None
        self._canvas.draw_idle()


class IntensitySurface(QWidget):
    """3D surface visualization of image intensity.

    Displays intensity as a 3D surface where height represents intensity.
    """

    # --- Theme colors ---
    _COLOR_FIGURE_BG = '#252729'
    _COLOR_AXES_BG = '#252729'
    _COLOR_LABEL = '#B4B3AF'
    _COLOR_TICK = '#9B9A97'
    _COLOR_GRID = '#3F4447'

    # --- Layout ---
    _SUBPLOT_MARGINS = dict(left=-0.05, right=1.0, top=0.96, bottom=0.0)
    _BOX_ASPECT = [1, 1, 0.8]
    _BOX_ZOOM = 0.95

    # --- Font ---
    _LABEL_FONTSIZE = 8
    _TICK_LABELSIZE = 7
    _LABEL_PAD = 2
    _TICK_PAD = 1

    _TITLE_FONTSIZE = 13

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {self._COLOR_FIGURE_BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._figure = Figure(figsize=(4, 4), dpi=100,
                              facecolor=self._COLOR_FIGURE_BG)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Expanding)
        self._ax = self._figure.add_subplot(
            111, projection="3d", facecolor=self._COLOR_AXES_BG)
        self._ax.disable_mouse_rotation()
        layout.addWidget(self._canvas)

        self._cmap = "viridis"
        self._surface = None

        # --- Persistent settings (survive ax.clear()) ---

        self._ax.set_box_aspect(self._BOX_ASPECT, zoom=self._BOX_ZOOM)
        self._ax.view_init(elev=30, azim=-60)

        for axis in (self._ax.xaxis, self._ax.yaxis, self._ax.zaxis):
            axis.pane.fill = False
            axis.pane.set_edgecolor('none')
            axis._axinfo["grid"]['color'] = self._COLOR_GRID
            axis._axinfo["grid"]['linewidth'] = 0.5

        self._figure.subplots_adjust(**self._SUBPLOT_MARGINS)

        # Legend (figure-level, survives ax.clear())
        self._figure.text(
            0.98, 0.02, "X, Y : Position\nZ : Intensity",
            color=self._COLOR_TICK, fontsize=7,
            ha='right', va='bottom')

        # --- Non-persistent settings (reset by ax.clear()) ---
        self._apply_post_clear_style()

    def _apply_post_clear_style(self) -> None:
        """Apply axes styling that is reset by ax.clear()."""
        from matplotlib.ticker import MultipleLocator

        ax = self._ax

        ax.set_title("Intensity Surface", color=self._COLOR_LABEL,
                     fontsize=self._TITLE_FONTSIZE, y=1.0, pad=12)

        ax.set_xlabel("X", color=self._COLOR_LABEL,
                       fontsize=self._LABEL_FONTSIZE, labelpad=self._LABEL_PAD)
        ax.set_ylabel("Y", color=self._COLOR_LABEL,
                       fontsize=self._LABEL_FONTSIZE, labelpad=self._LABEL_PAD)
        ax.set_zlabel("", labelpad=0)

        ax.tick_params(colors=self._COLOR_TICK, which='both',
                       labelsize=self._TICK_LABELSIZE, pad=self._TICK_PAD)

        ax.xaxis.set_major_locator(MultipleLocator(0.2))
        ax.yaxis.set_major_locator(MultipleLocator(0.2))
        ax.zaxis.set_major_locator(MultipleLocator(0.2))
        ax.xaxis.set_minor_locator(MultipleLocator(0.1))
        ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax.zaxis.set_minor_locator(MultipleLocator(0.1))

        ax.grid(which='minor', alpha=0.3, linestyle=':')


    def set_colormap(self, cmap: str) -> None:
        """Set the colormap."""
        self._cmap = cmap

    def update_frame(self, frame: NDArray[np.uint8]) -> None:
        """Update with new frame data."""
        if frame.ndim == 3:
            gray = (
                0.299 * frame[:, :, 0] +
                0.587 * frame[:, :, 1] +
                0.114 * frame[:, :, 2]
            ).astype(np.float32)
        else:
            gray = frame.astype(np.float32)

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
        x = np.linspace(0, 1, w)
        y = np.linspace(0, 1, h)
        X, Y = np.meshgrid(x, y)

        elev = self._ax.elev
        azim = self._ax.azim

        self._ax.clear()
        self._ax.set_facecolor(self._COLOR_AXES_BG)
        self._surface = self._ax.plot_surface(
            X, Y, gray, cmap=self._cmap, linewidth=0, antialiased=False
        )

        self._ax.set_xlim(0, 1)
        self._ax.set_ylim(0, 1)
        self._ax.set_zlim(0, 1)
        self._ax.margins(x=0.0, y=0.0, z=0.0)

        self._ax.view_init(elev=elev, azim=azim)
        self._apply_post_clear_style()

        self._canvas.draw_idle()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._surface = None
        self._canvas.draw_idle()
