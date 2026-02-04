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
    QListWidget, QListWidgetItem, QSplitter, QGroupBox, QCheckBox
)
from PyQt6.QtGui import QImage, QPixmap, QColor, QPen, QBrush, QPainter
from PyQt6.QtCore import Qt, QRectF, QMargins, QPointF
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis

from pyrheed.video import (
    VideoFileSource, CameraSource,
    enumerate_cameras, SourceState
)
from pyrheed.roi import (
    ROI, ROIManager, ROIGraphicsItem,
    calculate_roi_intensity, calculate_frame_intensity, IntensityTracker
)


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

        # Intensity tracking
        self._intensity_tracker = IntensityTracker()
        self._frame_intensity_tracker = IntensityTracker()  # For full-frame intensity
        self._current_frame: np.ndarray | None = None

    @property
    def intensity_tracker(self) -> IntensityTracker:
        return self._intensity_tracker

    @property
    def frame_intensity_tracker(self) -> IntensityTracker:
        return self._frame_intensity_tracker

    def track_frame_intensity(self, frame_index: int, intensity: float) -> None:
        """Track full-frame intensity."""
        self._frame_intensity_tracker.add("full_frame", frame_index, intensity)

    def set_frame(self, frame: np.ndarray) -> None:
        """Store current frame for intensity calculation."""
        self._current_frame = frame

    def calculate_intensities(self, frame_index: int) -> dict[str, float]:
        """Calculate intensity for all ROIs.

        Returns:
            Dict mapping ROI ID to intensity value.
        """
        results = {}
        if self._current_frame is None:
            return results

        for roi in self._roi_manager:
            intensity = calculate_roi_intensity(self._current_frame, roi)
            if intensity is not None:
                self._intensity_tracker.add(roi.id, frame_index, intensity)
                results[roi.id] = intensity

        return results

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


class IntensityChart(QWidget):
    """Widget containing chart and frame range controls."""

    # Maximum points to display for performance
    MAX_DISPLAY_POINTS = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Frame range controls
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Frame:"))

        self._start_spin = QSpinBox()
        self._start_spin.setMinimum(0)
        self._start_spin.setMaximum(999999)
        self._start_spin.setValue(0)
        self._start_spin.valueChanged.connect(self._on_spin_changed)
        range_layout.addWidget(self._start_spin)

        range_layout.addWidget(QLabel("-"))

        self._end_spin = QSpinBox()
        self._end_spin.setMinimum(0)
        self._end_spin.setMaximum(999999)
        self._end_spin.setValue(100)
        self._end_spin.valueChanged.connect(self._on_spin_changed)
        range_layout.addWidget(self._end_spin)

        self._auto_range_cb = QCheckBox("Auto")
        self._auto_range_cb.setChecked(True)
        self._auto_range_cb.stateChanged.connect(self._on_auto_range_changed)
        range_layout.addWidget(self._auto_range_cb)

        range_layout.addStretch()
        layout.addLayout(range_layout)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red; font-size: 11px;")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        # Chart view
        self._chart_view = QChartView()
        self._chart = QChart()
        self._chart.setTitle("Intensity Trend")
        self._chart.legend().setVisible(True)
        self._chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
        self._chart.setMargins(QMargins(0, 0, 0, 0))

        # Axes
        self._axis_x = QValueAxis()
        self._axis_x.setTitleText("Frame")
        self._axis_x.setLabelFormat("%d")
        self._chart.addAxis(self._axis_x, Qt.AlignmentFlag.AlignBottom)

        self._axis_y = QValueAxis()
        self._axis_y.setTitleText("Intensity")
        self._axis_y.setRange(0, 1)
        self._chart.addAxis(self._axis_y, Qt.AlignmentFlag.AlignLeft)

        self._chart_view.setChart(self._chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self._chart_view)

        # Series storage
        self._series: dict[str, QLineSeries] = {}

        # Colors for series
        self._colors = [
            QColor("#00BFFF"),  # Full frame - cyan
            QColor("#FF6B6B"),  # ROI 1 - red
            QColor("#4ECDC4"),  # ROI 2 - teal
            QColor("#FFE66D"),  # ROI 3 - yellow
            QColor("#95E1D3"),  # ROI 4 - mint
            QColor("#F38181"),  # ROI 5 - coral
        ]

        # Store current data for re-filtering
        self._current_frame_tracker: IntensityTracker | None = None
        self._current_roi_tracker: IntensityTracker | None = None
        self._current_roi_labels: dict[str, str] = {}

        # Valid data range
        self._data_min_frame = 0
        self._data_max_frame = 0

    def _on_spin_changed(self) -> None:
        """Handle spinbox value change - auto switch to manual mode."""
        # Auto-switch to manual mode when user edits
        if self._auto_range_cb.isChecked():
            self._auto_range_cb.blockSignals(True)
            self._auto_range_cb.setChecked(False)
            self._auto_range_cb.blockSignals(False)

        self._validate_and_apply_range()

    def _on_auto_range_changed(self, state: int) -> None:
        """Handle auto range checkbox change."""
        auto = state == Qt.CheckState.Checked.value
        if auto:
            self._error_label.setVisible(False)
            self._update_auto_range()

    def _validate_and_apply_range(self) -> None:
        """Validate input and apply range."""
        start = self._start_spin.value()
        end = self._end_spin.value()

        # Check if values are within data range
        has_data = self._data_max_frame > 0
        start_valid = not has_data or (0 <= start <= self._data_max_frame)
        end_valid = not has_data or (0 <= end <= self._data_max_frame)

        # Show error if out of range
        if has_data and (not start_valid or not end_valid):
            self._error_label.setText(
                f"Range out of bounds (valid: 0-{self._data_max_frame})"
            )
            self._error_label.setVisible(True)
            return

        # Auto-swap if start > end but both valid
        if start > end:
            self._start_spin.blockSignals(True)
            self._end_spin.blockSignals(True)
            self._start_spin.setValue(end)
            self._end_spin.setValue(start)
            self._start_spin.blockSignals(False)
            self._end_spin.blockSignals(False)
            start, end = end, start

        # Clear error and apply
        self._error_label.setVisible(False)
        if end > start:
            self._axis_x.setRange(start, end)

    def _update_auto_range(self) -> None:
        """Update range automatically based on data."""
        if self._current_frame_tracker:
            frame_history = self._current_frame_tracker.get_history("full_frame")
            if frame_history:
                max_frame = max(f[0] for f in frame_history)
                min_frame = min(f[0] for f in frame_history)
                self._data_min_frame = min_frame
                self._data_max_frame = max_frame
                self._axis_x.setRange(max(0, min_frame), max(10, max_frame + 1))
                # Update spinbox values to reflect current range
                self._start_spin.blockSignals(True)
                self._end_spin.blockSignals(True)
                self._start_spin.setValue(max(0, min_frame))
                self._end_spin.setValue(max(10, max_frame + 1))
                self._start_spin.blockSignals(False)
                self._end_spin.blockSignals(False)

    def update_data(
        self,
        frame_tracker: IntensityTracker,
        roi_tracker: IntensityTracker,
        roi_labels: dict[str, str]
    ) -> None:
        """Update chart with latest intensity data."""
        # Store references for range filtering
        self._current_frame_tracker = frame_tracker
        self._current_roi_tracker = roi_tracker
        self._current_roi_labels = roi_labels

        # Update full-frame series
        frame_history = frame_tracker.get_history("full_frame")
        self._update_series("full_frame", "Full Frame", frame_history, self._colors[0])

        # Track data range for validation
        if frame_history:
            self._data_min_frame = min(f[0] for f in frame_history)
            self._data_max_frame = max(f[0] for f in frame_history)

        # Update ROI series
        color_idx = 1
        for roi_id, label in roi_labels.items():
            roi_history = roi_tracker.get_history(roi_id)
            color = self._colors[color_idx % len(self._colors)]
            self._update_series(roi_id, label, roi_history, color)
            color_idx += 1

        # Remove series for deleted ROIs
        current_ids = {"full_frame"} | set(roi_labels.keys())
        to_remove = [sid for sid in self._series if sid not in current_ids]
        for sid in to_remove:
            self._chart.removeSeries(self._series[sid])
            del self._series[sid]

        # Update X axis range
        if self._auto_range_cb.isChecked():
            self._update_auto_range()

    def _update_series(
        self,
        series_id: str,
        label: str,
        history: list[tuple[int, float]],
        color: QColor
    ) -> None:
        """Update or create a series."""
        if series_id not in self._series:
            series = QLineSeries()
            series.setName(label)
            series.setColor(color)
            self._chart.addSeries(series)
            series.attachAxis(self._axis_x)
            series.attachAxis(self._axis_y)
            self._series[series_id] = series
        else:
            series = self._series[series_id]
            series.setName(label)  # Update label in case it changed

        # Downsample if too many points
        if len(history) > self.MAX_DISPLAY_POINTS:
            # Keep every Nth point to stay under limit
            step = len(history) // self.MAX_DISPLAY_POINTS + 1
            display_data = history[::step]
            # Always include the last point
            if history[-1] not in display_data:
                display_data = list(display_data) + [history[-1]]
        else:
            display_data = history

        # Use batch replace for better performance
        points = [QPointF(float(frame_idx), intensity) for frame_idx, intensity in display_data]
        series.replace(points)

    def clear(self) -> None:
        """Clear all series."""
        for series in self._series.values():
            self._chart.removeSeries(series)
        self._series.clear()


class VideoTestWindow(QMainWindow):
    """Window to test video sources and ROI functionality."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyRHEED Video + ROI Test")
        self.setMinimumSize(1000, 700)

        self._source = None
        self._last_chart_update = 0.0  # For throttling chart updates
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

        # Main content: canvas + ROI panel + chart (horizontal)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Image canvas
        self._canvas = ImageCanvas()
        main_splitter.addWidget(self._canvas)

        # ROI panel
        roi_panel = QWidget()
        roi_layout = QVBoxLayout(roi_panel)

        # Full-frame intensity display
        frame_intensity_layout = QHBoxLayout()
        frame_intensity_layout.addWidget(QLabel("Full Frame:"))
        self._frame_intensity_label = QLabel("--")
        self._frame_intensity_label.setStyleSheet("font-weight: bold; color: #00BFFF;")
        frame_intensity_layout.addWidget(self._frame_intensity_label)
        frame_intensity_layout.addStretch()
        roi_layout.addLayout(frame_intensity_layout)

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

        # Export section
        roi_layout.addSpacing(10)
        export_group = QGroupBox("Log")
        export_layout = QVBoxLayout(export_group)

        self._record_count_label = QLabel("Records: 0")
        export_layout.addWidget(self._record_count_label)

        export_btn_layout = QHBoxLayout()
        self._export_btn = QPushButton("📄 Export")
        self._export_btn.clicked.connect(self._on_export_log)
        export_btn_layout.addWidget(self._export_btn)

        self._clear_log_btn = QPushButton("🗑 Clear")
        self._clear_log_btn.clicked.connect(self._on_clear_log)
        export_btn_layout.addWidget(self._clear_log_btn)

        export_layout.addLayout(export_btn_layout)

        roi_layout.addWidget(export_group)

        main_splitter.addWidget(roi_panel)

        # Intensity chart (right side)
        self._chart = IntensityChart()
        self._chart.setMinimumWidth(300)
        main_splitter.addWidget(self._chart)

        main_splitter.setSizes([500, 150, 350])

        main_layout.addWidget(main_splitter)

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

            # Store frame and calculate full-frame intensity
            self._canvas.set_frame(frame)
            frame_intensity = calculate_frame_intensity(frame)
            self._frame_intensity_label.setText(f"{frame_intensity:.3f}")

            # Track full-frame intensity
            self._canvas.track_frame_intensity(0, frame_intensity)
            self._record_count_label.setText("Records: 1")

            # Calculate ROI intensities if any ROIs exist
            intensities = self._canvas.calculate_intensities(0)
            self._update_roi_list(intensities)
            self._update_chart(force=True)

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

    def _on_export_log(self) -> None:
        """Export intensity data to CSV file."""
        frame_history = self._canvas.frame_intensity_tracker.get_history("full_frame")
        if not frame_history:
            self._status.showMessage("No data to export")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Intensity Log", "intensity_log.csv",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not path:
            return

        try:
            # Collect all ROI IDs
            roi_ids = [roi.id for roi in self._canvas.roi_manager]
            roi_labels = {roi.id: (roi.label or roi.id) for roi in self._canvas.roi_manager}

            # Build data by frame index
            frame_data: dict[int, dict[str, float]] = {}

            # Add full-frame data
            for frame_idx, intensity in frame_history:
                if frame_idx not in frame_data:
                    frame_data[frame_idx] = {}
                frame_data[frame_idx]["full_frame"] = intensity

            # Add ROI data
            for roi_id in roi_ids:
                roi_history = self._canvas.intensity_tracker.get_history(roi_id)
                for frame_idx, intensity in roi_history:
                    if frame_idx not in frame_data:
                        frame_data[frame_idx] = {}
                    frame_data[frame_idx][roi_id] = intensity

            # Write CSV
            with open(path, "w", encoding="utf-8") as f:
                # Header
                headers = ["frame", "full_frame"]
                for roi_id in roi_ids:
                    headers.append(roi_labels[roi_id])
                f.write(",".join(headers) + "\n")

                # Data rows (sorted by frame index)
                for frame_idx in sorted(frame_data.keys()):
                    row = [str(frame_idx)]
                    row.append(f"{frame_data[frame_idx].get('full_frame', ''):.6f}"
                               if 'full_frame' in frame_data[frame_idx] else "")
                    for roi_id in roi_ids:
                        if roi_id in frame_data[frame_idx]:
                            row.append(f"{frame_data[frame_idx][roi_id]:.6f}")
                        else:
                            row.append("")
                    f.write(",".join(row) + "\n")

            self._status.showMessage(f"Exported {len(frame_data)} frames to {path}")
        except Exception as e:
            self._status.showMessage(f"Export failed: {e}")

    def _on_clear_log(self) -> None:
        """Clear all tracked intensity data."""
        self._canvas.intensity_tracker.clear()
        self._canvas.frame_intensity_tracker.clear()
        self._chart.clear()
        self._record_count_label.setText("Records: 0")
        self._status.showMessage("Log cleared")

    def _on_roi_selected(self) -> None:
        """Handle ROI selection in list."""
        items = self._roi_list.selectedItems()
        # Could highlight selected ROI in canvas

    def _update_roi_list(self, intensities: dict[str, float] | None = None) -> None:
        """Update ROI list widget with intensity values.

        Uses incremental update when possible to avoid rebuilding the list.
        """
        roi_ids = [roi.id for roi in self._canvas.roi_manager]

        # Check if we need to rebuild the list (ROIs added/removed)
        current_ids = []
        for i in range(self._roi_list.count()):
            item = self._roi_list.item(i)
            current_ids.append(item.data(Qt.ItemDataRole.UserRole))

        if current_ids != roi_ids:
            # ROIs changed - rebuild list
            self._roi_list.clear()
            for roi in self._canvas.roi_manager:
                label = roi.label or roi.id
                if intensities and roi.id in intensities:
                    label = f"{label}: {intensities[roi.id]:.3f}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, roi.id)
                item.setForeground(QColor(roi.color))
                self._roi_list.addItem(item)
        elif intensities:
            # Just update intensity values in place
            for i, roi in enumerate(self._canvas.roi_manager):
                item = self._roi_list.item(i)
                if item and roi.id in intensities:
                    label = roi.label or roi.id
                    item.setText(f"{label}: {intensities[roi.id]:.3f}")

    def _update_chart(self, force: bool = False) -> None:
        """Update intensity trend chart with throttling.

        Args:
            force: If True, update regardless of throttle.
        """
        import time

        # Throttle updates to max 5 per second (200ms interval)
        current_time = time.time()
        if not force and (current_time - self._last_chart_update) < 0.2:
            return

        self._last_chart_update = current_time

        roi_labels = {
            roi.id: (roi.label or roi.id)
            for roi in self._canvas.roi_manager
        }
        self._chart.update_data(
            self._canvas.frame_intensity_tracker,
            self._canvas.intensity_tracker,
            roi_labels
        )

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

        # Store frame and calculate intensities
        self._canvas.set_frame(frame)
        intensities = self._canvas.calculate_intensities(index)

        # Calculate and display full-frame intensity
        frame_intensity = calculate_frame_intensity(frame)
        self._frame_intensity_label.setText(f"{frame_intensity:.3f}")

        # Track full-frame intensity
        self._canvas.track_frame_intensity(index, frame_intensity)

        # Update record count
        frame_count = self._canvas.frame_intensity_tracker.frame_count("full_frame")
        self._record_count_label.setText(f"Records: {frame_count}")

        # Fit to screen on first frame
        if index == 0:
            self._canvas.fit_in_view()

        # Update ROI list with intensity values
        self._update_roi_list(intensities)

        # Update intensity chart
        self._update_chart()

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
