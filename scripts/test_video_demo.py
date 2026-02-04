#!/usr/bin/env python3
"""Demo script to test video module functionality.

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
    QPushButton, QLabel, QFileDialog, QComboBox, QSlider, QStatusBar,
    QSpinBox
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

from pyrheed.video import (
    ImageSequenceSource, VideoFileSource, CameraSource,
    enumerate_cameras, SourceState
)


class VideoTestWindow(QMainWindow):
    """Simple window to test video sources."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyRHEED Video Module Test")
        self.setMinimumSize(800, 600)

        self._source = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Source selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))

        self._source_combo = QComboBox()
        self._source_combo.addItems(["Image Folder", "Video File", "Camera"])
        source_layout.addWidget(self._source_combo)

        self._open_btn = QPushButton("Open...")
        self._open_btn.clicked.connect(self._on_open)
        source_layout.addWidget(self._open_btn)

        source_layout.addStretch()
        layout.addLayout(source_layout)

        # Image display
        self._image_label = QLabel("No image loaded")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(640, 480)
        self._image_label.setStyleSheet("QLabel { background-color: #333; color: white; }")
        layout.addWidget(self._image_label)

        # Controls
        ctrl_layout = QHBoxLayout()

        self._play_pause_btn = QPushButton("▶ Play")
        self._play_pause_btn.clicked.connect(self._on_play_pause)
        self._play_pause_btn.setEnabled(False)
        ctrl_layout.addWidget(self._play_pause_btn)

        ctrl_layout.addWidget(QLabel("  |  "))

        self._color_btn = QPushButton("🎨 Color")
        self._color_btn.setCheckable(True)
        self._color_btn.setChecked(False)  # Default: grayscale
        self._color_btn.clicked.connect(self._on_toggle_color)
        self._color_btn.setToolTip("Toggle color/grayscale mode")
        ctrl_layout.addWidget(self._color_btn)

        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        # Seek slider (for non-live sources)
        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setEnabled(False)
        self._seek_slider.sliderReleased.connect(self._on_seek)
        layout.addWidget(self._seek_slider)

        # Frame navigation controls
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
        layout.addLayout(nav_layout)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _on_open(self) -> None:
        source_type = self._source_combo.currentText()

        if source_type == "Image Folder":
            path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
            if path:
                self._open_source(ImageSequenceSource(), path)

        elif source_type == "Video File":
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Video File", "",
                "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
            )
            if path:
                self._open_source(VideoFileSource(), path)

        elif source_type == "Camera":
            cameras = enumerate_cameras()
            if cameras:
                self._open_source(CameraSource(), "0")
            else:
                self._status.showMessage("No cameras found!")

    def _open_source(self, source, path: str) -> None:
        # Close previous source
        if self._source is not None:
            self._source.stop()
            self._source.close()

        self._source = source

        # Connect signals
        self._source.FRAME_READY.connect(self._on_frame)
        self._source.STATE_CHANGED.connect(self._on_state_changed)
        self._source.ERROR_OCCURRED.connect(self._on_error)
        self._source.FPS_UPDATED.connect(self._on_fps)

        if self._source.open(path):
            self._status.showMessage(f"Opened: {path}")
            self._play_pause_btn.setEnabled(True)

            # Setup slider and navigation for non-live sources
            if not self._source.is_live and self._source.total_frames > 0:
                total = self._source.total_frames
                self._seek_slider.setEnabled(True)
                self._seek_slider.setRange(0, total - 1)
                # Enable frame navigation
                self._prev_btn.setEnabled(True)
                self._next_btn.setEnabled(True)
                self._frame_spinbox.setEnabled(True)
                self._frame_spinbox.setMaximum(total)
                self._frame_spinbox.setValue(1)
                self._total_label.setText(f"/ {total}")
            else:
                self._seek_slider.setEnabled(False)
                self._prev_btn.setEnabled(False)
                self._next_btn.setEnabled(False)
                self._frame_spinbox.setEnabled(False)
                self._total_label.setText("/ 0")
        else:
            self._status.showMessage("Failed to open source")

    def _on_toggle_color(self) -> None:
        """Toggle between color and grayscale mode."""
        if self._source:
            # Toggle grayscale mode (button checked = color mode)
            self._source.grayscale = not self._color_btn.isChecked()
            mode = "Color" if self._color_btn.isChecked() else "Grayscale"
            self._status.showMessage(f"Mode: {mode}")

            # Refresh current frame immediately
            current_index = self._source.current_frame_index
            frame = self._source.get_frame(current_index)
            if frame is not None:
                self._on_frame(frame, current_index)

    def _on_frame(self, frame: np.ndarray, index: int) -> None:
        # Convert numpy array to QImage based on frame dimensions
        if frame.ndim == 2:
            # Grayscale frame
            h, w = frame.shape
            bytes_per_line = w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        else:
            # Color frame (RGB)
            h, w, c = frame.shape
            bytes_per_line = w * c
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        # Scale to fit label
        scaled = pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._image_label.setPixmap(scaled)

        # Update slider and spinbox position
        if not self._source.is_live:
            self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(index)
            self._seek_slider.blockSignals(False)

            self._frame_spinbox.blockSignals(True)
            self._frame_spinbox.setValue(index + 1)  # 1-based for UI
            self._frame_spinbox.blockSignals(False)

        # Update status
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

    def _on_play_pause(self) -> None:
        """Toggle between play and pause."""
        if self._source:
            if self._source.state == SourceState.PLAYING:
                self._source.pause()
            else:
                self._source.start()

    def _on_seek(self) -> None:
        if self._source and not self._source.is_live:
            self._source.seek(self._seek_slider.value())

    def _on_prev_frame(self) -> None:
        """Go to previous frame."""
        if self._source and not self._source.is_live:
            current = self._source.current_frame_index
            if current > 0:
                self._source.seek(current - 1)

    def _on_next_frame(self) -> None:
        """Go to next frame."""
        if self._source and not self._source.is_live:
            current = self._source.current_frame_index
            if current < self._source.total_frames - 1:
                self._source.seek(current + 1)

    def _on_frame_spinbox_changed(self, value: int) -> None:
        """Jump to specific frame from spinbox."""
        if self._source and not self._source.is_live:
            # Convert 1-based UI to 0-based index
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

    # Auto-open if args provided
    if args.source and args.path:
        if args.source == "image":
            window._open_source(ImageSequenceSource(), args.path)
        elif args.source == "video":
            window._open_source(VideoFileSource(), args.path)
        elif args.source == "camera":
            window._open_source(CameraSource(), args.path)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
