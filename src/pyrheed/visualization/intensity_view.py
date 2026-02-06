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
from matplotlib.ticker import MaxNLocator

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt


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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题作为独立 Widget（像 Web 一样）
        self._title_label = QLabel("Intensity Surface")
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

        # Matplotlib 图表（固定大小，防止窗口拉伸时标签溢出）
        self._figure = Figure(figsize=(4, 4), dpi=100, facecolor='#2F3437')
        self._canvas = FigureCanvas(self._figure)

        # 固定 canvas 大小，不随窗口缩放
        self._canvas.setFixedSize(400, 400)  # 4 inch * 100 dpi = 400 pixels

        self._ax = self._figure.add_subplot(111, projection="3d", facecolor='#252729')
        layout.addWidget(self._canvas)

        self._cmap = "viridis"
        self._surface = None

        # 刻度设置：主刻度（标签）0.2 间隔，次刻度（网格线）0.1 间隔
        from matplotlib.ticker import MultipleLocator
        self._ax.xaxis.set_major_locator(MultipleLocator(0.2))
        self._ax.yaxis.set_major_locator(MultipleLocator(0.2))
        self._ax.zaxis.set_major_locator(MultipleLocator(0.2))
        self._ax.xaxis.set_minor_locator(MultipleLocator(0.1))
        self._ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        self._ax.zaxis.set_minor_locator(MultipleLocator(0.1))

        # 暗色主题样式（不设置标题，因为已经用 QLabel 了）
        self._ax.tick_params(colors='#9B9A97', which='both', pad=2)

        # 隐藏 pane 的边缘线，避免旋转时显示异常
        self._ax.xaxis.pane.fill = False
        self._ax.yaxis.pane.fill = False
        self._ax.zaxis.pane.fill = False
        self._ax.xaxis.pane.set_edgecolor('none')  # 完全隐藏边缘线
        self._ax.yaxis.pane.set_edgecolor('none')
        self._ax.zaxis.pane.set_edgecolor('none')

        # 设置网格线样式（更细更柔和）
        # 主网格线（0.2间隔）
        self._ax.xaxis._axinfo["grid"]['color'] = '#3F4447'
        self._ax.yaxis._axinfo["grid"]['color'] = '#3F4447'
        self._ax.zaxis._axinfo["grid"]['color'] = '#3F4447'
        self._ax.xaxis._axinfo["grid"]['linewidth'] = 0.5
        self._ax.yaxis._axinfo["grid"]['linewidth'] = 0.5
        self._ax.zaxis._axinfo["grid"]['linewidth'] = 0.5

        # 启用次要网格线（0.1间隔）
        self._ax.grid(which='minor', alpha=0.3, linestyle=':')

        self._ax.xaxis.label.set_color('#B4B3AF')
        self._ax.yaxis.label.set_color('#B4B3AF')
        self._ax.zaxis.label.set_color('#B4B3AF')

        # 调整 Z 轴标签位置，让它更靠近轴线
        self._ax.zaxis._axinfo['label']['space_factor'] = 2.0

        # 设置固定视角（仰角 30 度，方位角 -60 度）
        self._ax.view_init(elev=30, azim=-60)

        # 缩小 3D 盒子本身的尺寸，让坐标轴不会超出边框
        self._ax.set_box_aspect([1, 1, 0.8])  # x, y, z 比例，z 轴稍短

        # 设置相机距离
        self._ax.dist = 10.5

        # 禁用交互旋转，固定视角
        self._ax.mouse_init(rotate_btn=None, zoom_btn=None)

        # 手动调整布局，给标签预留足够空间（固定比例）
        self._figure.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

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
        # 归一化坐标到 0-1，确保与轴刻度一致
        x = np.linspace(0, 1, w)
        y = np.linspace(0, 1, h)
        X, Y = np.meshgrid(x, y)

        # 保存当前视角
        elev = self._ax.elev
        azim = self._ax.azim

        self._ax.clear()
        self._ax.set_facecolor('#252729')  # 重新设置背景色
        self._surface = self._ax.plot_surface(
            X, Y, gray, cmap=self._cmap, linewidth=0, antialiased=False
        )
        self._ax.set_zlim(0, 1)

        # 归一化坐标轴范围到 0-1，确保所有轴刻度一致
        self._ax.set_xlim(0, 1)
        self._ax.set_ylim(0, 1)
        self._ax.set_zlim(0, 1)
        self._ax.margins(x=0.0, y=0.0, z=0.0)

        # 恢复视角
        self._ax.view_init(elev=elev, azim=azim)
        self._ax.set_xlabel("X", color='#B4B3AF')
        self._ax.set_ylabel("Y", color='#B4B3AF')
        self._ax.set_zlabel("Intensity", color='#B4B3AF')

        # 重新应用刻度设置（clear 后需要重新设置）
        from matplotlib.ticker import MultipleLocator
        self._ax.tick_params(colors='#9B9A97', which='both', pad=2)
        self._ax.xaxis.set_major_locator(MultipleLocator(0.2))
        self._ax.yaxis.set_major_locator(MultipleLocator(0.2))
        self._ax.zaxis.set_major_locator(MultipleLocator(0.2))
        self._ax.xaxis.set_minor_locator(MultipleLocator(0.1))
        self._ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        self._ax.zaxis.set_minor_locator(MultipleLocator(0.1))

        # 调整 Z 轴标签位置
        self._ax.zaxis._axinfo['label']['space_factor'] = 2.0

        self._ax.set_box_aspect([1, 1, 0.8])
        self._ax.xaxis.pane.fill = False
        self._ax.yaxis.pane.fill = False
        self._ax.zaxis.pane.fill = False
        self._ax.xaxis.pane.set_edgecolor('none')
        self._ax.yaxis.pane.set_edgecolor('none')
        self._ax.zaxis.pane.set_edgecolor('none')

        # 重新启用次要网格线
        self._ax.grid(which='minor', alpha=0.3, linestyle=':')

        self._canvas.draw_idle()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._surface = None
        self._canvas.draw_idle()
