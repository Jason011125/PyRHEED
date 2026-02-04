# PyQt6 摄像头集成技能

## 架构模式

### 推荐架构

```
┌─────────────────────────────────────────────────────────┐
│                     Main Thread                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Window    │  │   Canvas    │  │  ProfileChart   │  │
│  │  (控制器)   │  │  (显示器)   │  │   (分析图表)    │  │
│  └──────┬──────┘  └──────▲──────┘  └────────▲────────┘  │
│         │                │                   │           │
│         │ start/stop     │ frame_ready       │ analyze   │
│         ▼                │                   │           │
│  ┌──────────────────────┴───────────────────┴────────┐  │
│  │              Signal/Slot 通信层                    │  │
│  └──────────────────────▲────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                  Camera Thread                           │
│  ┌──────────────────────┴────────────────────────────┐  │
│  │                 CameraWorker                       │  │
│  │   cv2.VideoCapture → frame → emit(frame_ready)    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 核心类实现

### CameraWorker (QThread)

```python
from PyQt6.QtCore import QThread, pyqtSignal, QMutex
import cv2
import numpy as np

class CameraWorker(QThread):
    """摄像头捕获工作线程"""

    FRAME_READY = pyqtSignal(np.ndarray)
    ERROR_OCCURRED = pyqtSignal(str)
    FPS_UPDATED = pyqtSignal(float)

    def __init__(self, device_id: int = 0, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        self._running = False
        self._mutex = QMutex()

    def run(self):
        cap = cv2.VideoCapture(self.device_id)
        if not cap.isOpened():
            self.ERROR_OCCURRED.emit(f"无法打开摄像头 {self.device_id}")
            return

        # 配置摄像头
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少延迟

        self._running = True
        frame_count = 0
        start_time = cv2.getTickCount()

        while self._running:
            ret, frame = cap.read()
            if ret:
                self.FRAME_READY.emit(frame)
                frame_count += 1

                # 计算 FPS
                if frame_count % 30 == 0:
                    elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                    fps = frame_count / elapsed
                    self.FPS_UPDATED.emit(fps)
            else:
                self.msleep(10)

        cap.release()

    def stop(self):
        self._mutex.lock()
        self._running = False
        self._mutex.unlock()
        self.wait()
```

### CameraWidget (视频显示)

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import pyqtSignal
import numpy as np

class CameraWidget(QWidget):
    """摄像头视频显示组件"""

    FRAME_CAPTURED = pyqtSignal(np.ndarray)  # 捕获帧用于分析

    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel()
        self.label.setMinimumSize(640, 480)
        self.label.setScaledContents(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        self.worker = None
        self._current_frame = None

    def start(self, device_id: int = 0):
        if self.worker and self.worker.isRunning():
            self.stop()

        self.worker = CameraWorker(device_id)
        self.worker.FRAME_READY.connect(self._on_frame)
        self.worker.ERROR_OCCURRED.connect(self._on_error)
        self.worker.start()

    def stop(self):
        if self.worker:
            self.worker.stop()
            self.worker = None

    def _on_frame(self, frame: np.ndarray):
        self._current_frame = frame

        # 转换为 QImage
        h, w = frame.shape[:2]
        if len(frame.shape) == 3:
            qimg = QImage(frame.data, w, h, 3 * w, QImage.Format.Format_BGR888)
        else:
            qimg = QImage(frame.data, w, h, w, QImage.Format.Format_Grayscale8)

        self.label.setPixmap(QPixmap.fromImage(qimg))

    def _on_error(self, msg: str):
        self.label.setText(f"错误: {msg}")

    def capture(self) -> np.ndarray:
        """捕获当前帧"""
        if self._current_frame is not None:
            frame = self._current_frame.copy()
            self.FRAME_CAPTURED.emit(frame)
            return frame
        return None
```

## 与 PyRHEED 集成

### 修改 window.py

```python
# 在 __init__ 中添加
from pyrheed.camera import CameraWorker, CameraWidget

# 添加摄像头相关信号
CAMERA_FRAME_READY = pyqtSignal(np.ndarray)

# 添加摄像头菜单
self.menuCamera = self.menu.addMenu("Camera")
self.actionStartCamera = self.menuCamera.addAction("Start", self.start_camera)
self.actionStopCamera = self.menuCamera.addAction("Stop", self.stop_camera)
self.actionCaptureFrame = self.menuCamera.addAction("Capture", self.capture_frame)

# 添加方法
def start_camera(self, device_id: int = 0):
    # 创建摄像头 canvas tab
    self.camera_widget = CameraWidget()
    self.camera_widget.FRAME_CAPTURED.connect(self.on_frame_captured)
    self.mainTab.addTab(self.camera_widget, "Camera")
    self.mainTab.setCurrentWidget(self.camera_widget)
    self.camera_widget.start(device_id)

def stop_camera(self):
    if hasattr(self, 'camera_widget'):
        self.camera_widget.stop()

def capture_frame(self):
    if hasattr(self, 'camera_widget'):
        frame = self.camera_widget.capture()
        if frame is not None:
            self.on_frame_captured(frame)

def on_frame_captured(self, frame: np.ndarray):
    # 使用现有的分析流程处理帧
    qImg, img_array = self.image_worker.get_image_from_frame(frame)
    # ... 后续处理
```

## 配置存储

```ini
# configuration/configuration.ini 新增
[cameraDefault]
device_id = 0
width = 1920
height = 1080
fps = 30
auto_analyze = false
```
