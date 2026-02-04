#!/usr/bin/env python3
"""Demo script to test video module and ROI functionality.

Usage:
    python scripts/test_video_demo.py --source image_folder /path/to/images
    python scripts/test_video_demo.py --source video /path/to/video.mp4
    python scripts/test_video_demo.py --source camera 0
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSlider, QStatusBar,
    QSpinBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtGui import QImage, QPixmap, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF

from pyrheed.video import (
    VideoFileSource, CameraSource,
    enumerate_cameras, SourceState
)
from pyrheed.roi import ROI, ROIManager, ROIGraphicsItem


class ImageCanvas(QGraphicsView):
    """Graphics view for displaying frames and ROIs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(QColor(50, 50, 50)))

        self._drawing = False
        self._start_pos = None
        self._temp_rect = None
        self._draw_mode = False  # Whether we're in ROI drawing mode

        # Enable drag to pan by default
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # ROI management
        self._roi_manager = ROIManager()
        self._roi_items: dict[str, ROIGraphicsItem] = {}

    @property
    def roi_manager(self) -> ROIManager:
        return self._roi_manager

    def set_draw_mode(self, enabled: bool) -> None:
        """Enable/disable ROI drawing mode."""
        self._draw_mode = enabled
        if enabled:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Set the displayed image."""
        self._photo.setPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))

    def fit_in_view(self) -> None:
        """Fit the image in the view."""
        if not self._photo.pixmap().isNull():
            self.fitInView(self._photo, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        """Disable wheel zoom to prevent accidental triggers."""
        # Ignore wheel events - use zoom buttons instead
        event.ignore()

    def mousePressEvent(self, event):
        """Start drawing ROI."""
        if self._draw_mode and event.button() == Qt.MouseButton.LeftButton:
            self._drawing = True
            self._start_pos = self.mapToScene(event.pos())
            # Create temporary rect
            self._temp_rect = self._scene.addRect(
                QRectF(self._start_pos, self._start_pos),
                QPen(QColor("#FFFF00"), 2, Qt.PenStyle.DashLine)
            )
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Update ROI preview while drawing."""
        if self._drawing and self._temp_rect:
            current_pos = self.mapToScene(event.pos())
            rect = QRectF(self._start_pos, current_pos).normalized()
            self._temp_rect.setRect(rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finish drawing ROI."""
        if self._drawing and event.button() == Qt.MouseButton.LeftButton:
            self._drawing = False
            if self._temp_rect:
                rect = self._temp_rect.rect()
                self._scene.removeItem(self._temp_rect)
                self._temp_rect = None

                # Create ROI if large enough
                if rect.width() > 5 and rect.height() > 5:
                    self._create_roi(rect)
        else:
            super().mouseReleaseEvent(event)

    def _create_roi(self, rect: QRectF) -> ROI:
        """Create ROI from rectangle."""
        roi = self._roi_manager.add(
            x=int(rect.x()),
            y=int(rect.y()),
            width=int(rect.width()),
            height=int(rect.height()),
            label=f"ROI {len(self._roi_manager) + 1}"
        )
        item = ROIGraphicsItem(roi)
        self._scene.addItem(item)
        self._roi_items[roi.id] = item
        return roi

    def remove_roi(self, roi_id: str) -> None:
        """Remove ROI by ID."""
        if roi_id in self._roi_items:
            item = self._roi_items.pop(roi_id)
            self._scene.removeItem(item)
            self._roi_manager.remove(roi_id)

    def clear_rois(self) -> None:
        """Remove all ROIs."""
        for item in self._roi_items.values():
            self._scene.removeItem(item)
        self._roi_items.clear()
        self._roi_manager.clear()


class VideoTestWindow(QMainWindow):
    """Window to test video sources and ROI functionality."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyRHEED Video + ROI Test")
        self.setMinimumSize(1000, 700)

        self._source = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Source selection
        source_layout = QHBoxLayout()

        self._open_btn = QPushButton("📁 Open File/Folder...")
        self._open_btn.clicked.connect(self._on_open_file)
        source_layout.addWidget(self._open_btn)

        self._camera_btn = QPushButton("📷 Camera")
        self._camera_btn.setCheckable(True)
        self._camera_btn.clicked.connect(self._on_toggle_camera)
        source_layout.addWidget(self._camera_btn)

        source_layout.addStretch()
        main_layout.addLayout(source_layout)

        # Main content: canvas + ROI list
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Image canvas
        self._canvas = ImageCanvas()
        splitter.addWidget(self._canvas)

        # ROI panel
        roi_panel = QWidget()
        roi_layout = QVBoxLayout(roi_panel)
        roi_layout.addWidget(QLabel("ROIs:"))

        self._roi_list = QListWidget()
        self._roi_list.itemSelectionChanged.connect(self._on_roi_selected)
        roi_layout.addWidget(self._roi_list)

        # ROI buttons
        roi_btn_layout = QHBoxLayout()

        self._add_roi_btn = QPushButton("+ Add ROI")
        self._add_roi_btn.setCheckable(True)
        self._add_roi_btn.clicked.connect(self._on_toggle_add_roi)
        roi_btn_layout.addWidget(self._add_roi_btn)

        self._del_roi_btn = QPushButton("- Delete")
        self._del_roi_btn.clicked.connect(self._on_delete_roi)
        roi_btn_layout.addWidget(self._del_roi_btn)

        roi_layout.addLayout(roi_btn_layout)

        self._clear_roi_btn = QPushButton("Clear All")
        self._clear_roi_btn.clicked.connect(self._on_clear_rois)
        roi_layout.addWidget(self._clear_roi_btn)

        splitter.addWidget(roi_panel)
        splitter.setSizes([800, 200])

        main_layout.addWidget(splitter)

        # Controls
        ctrl_layout = QHBoxLayout()

        self._play_pause_btn = QPushButton("▶ Play")
        self._play_pause_btn.clicked.connect(self._on_play_pause)
        self._play_pause_btn.setEnabled(False)
        ctrl_layout.addWidget(self._play_pause_btn)

        ctrl_layout.addWidget(QLabel("  |  "))

        self._color_btn = QPushButton("🎨 Color")
        self._color_btn.setCheckable(True)
        self._color_btn.setChecked(False)
        self._color_btn.clicked.connect(self._on_toggle_color)
        ctrl_layout.addWidget(self._color_btn)

        ctrl_layout.addWidget(QLabel("  |  "))

        self._zoom_in_btn = QPushButton("🔍+")
        self._zoom_in_btn.clicked.connect(self._on_zoom_in)
        self._zoom_in_btn.setToolTip("Zoom In")
        self._zoom_in_btn.setFixedWidth(40)
        ctrl_layout.addWidget(self._zoom_in_btn)

        self._zoom_out_btn = QPushButton("🔍-")
        self._zoom_out_btn.clicked.connect(self._on_zoom_out)
        self._zoom_out_btn.setToolTip("Zoom Out")
        self._zoom_out_btn.setFixedWidth(40)
        ctrl_layout.addWidget(self._zoom_out_btn)

        self._fit_btn = QPushButton("Fit")
        self._fit_btn.clicked.connect(self._on_fit)
        self._fit_btn.setToolTip("Fit to window")
        ctrl_layout.addWidget(self._fit_btn)

        ctrl_layout.addStretch()
        main_layout.addLayout(ctrl_layout)

        # Seek slider
        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setEnabled(False)
        self._seek_slider.sliderReleased.connect(self._on_seek)
        main_layout.addWidget(self._seek_slider)

        # Frame navigation
        nav_layout = QHBoxLayout()

        self._prev_btn = QPushButton("◀ Prev")
        self._prev_btn.clicked.connect(self._on_prev_frame)
        self._prev_btn.setEnabled(False)
        nav_layout.addWidget(self._prev_btn)

        nav_layout.addWidget(QLabel("Frame:"))

        self._frame_spinbox = QSpinBox()
        self._frame_spinbox.setMinimum(1)
        self._frame_spinbox.setMaximum(1)
        self._frame_spinbox.setEnabled(False)
        self._frame_spinbox.valueChanged.connect(self._on_frame_spinbox_changed)
        nav_layout.addWidget(self._frame_spinbox)

        self._total_label = QLabel("/ 0")
        nav_layout.addWidget(self._total_label)

        self._next_btn = QPushButton("Next ▶")
        self._next_btn.clicked.connect(self._on_next_frame)
        self._next_btn.setEnabled(False)
        nav_layout.addWidget(self._next_btn)

        nav_layout.addStretch()
        main_layout.addLayout(nav_layout)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready - Draw ROIs by clicking '+ Add ROI' then drag on image")

    def _on_open_file(self) -> None:
        """Open video or image file."""
        # Turn off camera mode if active
        if self._camera_btn.isChecked():
            self._camera_btn.setChecked(False)

        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video or Image", "",
            "Media Files (*.mp4 *.avi *.mov *.mkv *.png *.jpg *.jpeg *.tif *.tiff *.bmp);;All Files (*)"
        )

        if path:
            self._open_path(path)

    def _on_toggle_camera(self) -> None:
        """Toggle camera on/off."""
        if self._camera_btn.isChecked():
            cameras = enumerate_cameras()
            if cameras:
                self._open_source(CameraSource(), "0")
            else:
                self._status.showMessage("No cameras found!")
                self._camera_btn.setChecked(False)
        else:
            # Stop camera
            if self._source:
                self._source.stop()
                self._source.close()
                self._source = None
            self._status.showMessage("Camera stopped")

    def _open_path(self, path: str) -> None:
        """Auto-detect and open video or image."""
        from pathlib import Path
        p = Path(path)

        if not p.is_file():
            self._status.showMessage(f"File not found: {path}")
            return

        ext = p.suffix.lower()
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
        image_exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

        if ext in video_exts:
            self._open_source(VideoFileSource(), path)
        elif ext in image_exts:
            self._open_image(path)
        else:
            self._status.showMessage(f"Unsupported format: {ext}")

    def _open_image(self, path: str) -> None:
        """Open a single image file."""
        from PIL import Image

        # Close previous source
        if self._source is not None:
            self._source.stop()
            self._source.close()
            self._source = None

        try:
            img = Image.open(path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            frame = np.array(img, dtype=np.uint8)

            # Display the image
            h, w, c = frame.shape
            bytes_per_line = w * c
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self._canvas.set_pixmap(pixmap)
            self._canvas.fit_in_view()

            # Disable playback controls for single image
            self._play_pause_btn.setEnabled(False)
            self._seek_slider.setEnabled(False)
            self._prev_btn.setEnabled(False)
            self._next_btn.setEnabled(False)
            self._frame_spinbox.setEnabled(False)
            self._total_label.setText("/ 1")

            self._status.showMessage(f"Opened image: {path}")
        except Exception as e:
            self._status.showMessage(f"Failed to open image: {e}")

    def _open_source(self, source, path: str) -> None:
        if self._source is not None:
            self._source.stop()
            self._source.close()

        self._source = source

        self._source.FRAME_READY.connect(self._on_frame)
        self._source.STATE_CHANGED.connect(self._on_state_changed)
        self._source.ERROR_OCCURRED.connect(self._on_error)
        self._source.FPS_UPDATED.connect(self._on_fps)

        if self._source.open(path):
            self._status.showMessage(f"Opened: {path}")
            self._play_pause_btn.setEnabled(True)

            if not self._source.is_live and self._source.total_frames > 0:
                total = self._source.total_frames
                self._seek_slider.setEnabled(True)
                self._seek_slider.setRange(0, total - 1)
                self._prev_btn.setEnabled(True)
                self._next_btn.setEnabled(True)
                self._frame_spinbox.setEnabled(True)
                self._frame_spinbox.setMaximum(total)
                self._frame_spinbox.setValue(1)
                self._total_label.setText(f"/ {total}")

                # Show first frame
                frame = self._source.get_frame(0)
                if frame is not None:
                    self._on_frame(frame, 0)
            else:
                self._seek_slider.setEnabled(False)
                self._prev_btn.setEnabled(False)
                self._next_btn.setEnabled(False)
                self._frame_spinbox.setEnabled(False)
                self._total_label.setText("/ 0")
        else:
            self._status.showMessage("Failed to open source")

    def _on_toggle_add_roi(self) -> None:
        """Toggle ROI drawing mode."""
        self._canvas.set_draw_mode(self._add_roi_btn.isChecked())
        if self._add_roi_btn.isChecked():
            self._status.showMessage("ROI mode: Click and drag to draw a region")
        else:
            self._status.showMessage("ROI mode disabled")

    def _on_delete_roi(self) -> None:
        """Delete selected ROI."""
        items = self._roi_list.selectedItems()
        for item in items:
            roi_id = item.data(Qt.ItemDataRole.UserRole)
            self._canvas.remove_roi(roi_id)
            self._roi_list.takeItem(self._roi_list.row(item))

    def _on_clear_rois(self) -> None:
        """Clear all ROIs."""
        self._canvas.clear_rois()
        self._roi_list.clear()

    def _on_roi_selected(self) -> None:
        """Handle ROI selection in list."""
        items = self._roi_list.selectedItems()
        # Could highlight selected ROI in canvas

    def _update_roi_list(self) -> None:
        """Update ROI list widget."""
        self._roi_list.clear()
        for roi in self._canvas.roi_manager:
            item = QListWidgetItem(roi.label or roi.id)
            item.setData(Qt.ItemDataRole.UserRole, roi.id)
            item.setForeground(QColor(roi.color))
            self._roi_list.addItem(item)

    def _on_toggle_color(self) -> None:
        if self._source:
            self._source.grayscale = not self._color_btn.isChecked()
            mode = "Color" if self._color_btn.isChecked() else "Grayscale"
            self._status.showMessage(f"Mode: {mode}")

            current_index = self._source.current_frame_index
            frame = self._source.get_frame(current_index)
            if frame is not None:
                self._on_frame(frame, current_index)

    def _on_frame(self, frame: np.ndarray, index: int) -> None:
        if frame.ndim == 2:
            h, w = frame.shape
            bytes_per_line = w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        else:
            h, w, c = frame.shape
            bytes_per_line = w * c
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg)
        self._canvas.set_pixmap(pixmap)

        # Fit to screen on first frame
        if index == 0:
            self._canvas.fit_in_view()

        # Update ROI list if new ROIs were added
        if len(self._canvas.roi_manager) != self._roi_list.count():
            self._update_roi_list()

        if not self._source.is_live:
            self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(index)
            self._seek_slider.blockSignals(False)

            self._frame_spinbox.blockSignals(True)
            self._frame_spinbox.setValue(index + 1)
            self._frame_spinbox.blockSignals(False)

        if self._source.is_live:
            self._status.showMessage(f"Frame: {index}")
        else:
            self._status.showMessage(f"Frame: {index + 1}/{self._source.total_frames}")

    def _on_state_changed(self, state: SourceState) -> None:
        if state == SourceState.PLAYING:
            self._play_pause_btn.setText("⏸ Pause")
        else:
            self._play_pause_btn.setText("▶ Play")

    def _on_error(self, message: str) -> None:
        self._status.showMessage(f"Error: {message}")

    def _on_fps(self, fps: float) -> None:
        self._status.showMessage(f"FPS: {fps:.1f}")

    def _on_zoom_in(self) -> None:
        """Zoom in."""
        self._canvas.scale(1.25, 1.25)

    def _on_zoom_out(self) -> None:
        """Zoom out."""
        self._canvas.scale(0.8, 0.8)

    def _on_fit(self) -> None:
        """Fit image to view."""
        self._canvas.fit_in_view()

    def _on_play_pause(self) -> None:
        if self._source:
            if self._source.state == SourceState.PLAYING:
                self._source.pause()
            else:
                self._source.start()

    def _on_seek(self) -> None:
        if self._source and not self._source.is_live:
            self._source.seek(self._seek_slider.value())

    def _on_prev_frame(self) -> None:
        if self._source and not self._source.is_live:
            current = self._source.current_frame_index
            if current > 0:
                self._source.seek(current - 1)

    def _on_next_frame(self) -> None:
        if self._source and not self._source.is_live:
            current = self._source.current_frame_index
            if current < self._source.total_frames - 1:
                self._source.seek(current + 1)

    def _on_frame_spinbox_changed(self, value: int) -> None:
        if self._source and not self._source.is_live:
            frame_index = value - 1
            if 0 <= frame_index < self._source.total_frames:
                self._source.seek(frame_index)

    def closeEvent(self, event) -> None:
        if self._source:
            self._source.stop()
            self._source.close()
        event.accept()


def main():
    parser = argparse.ArgumentParser(description="Test PyRHEED video module")
    parser.add_argument("--source", choices=["image", "video", "camera"], help="Source type")
    parser.add_argument("path", nargs="?", help="Path to source (folder/file/device_id)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = VideoTestWindow()

    if args.path:
        if args.source == "camera":
            window._camera_btn.setChecked(True)
            window._on_toggle_camera()
        else:
            window._open_path(args.path)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
