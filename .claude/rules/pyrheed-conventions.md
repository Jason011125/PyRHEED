# PyRHEED 项目规范

## 代码风格

### 信号命名
- 使用大写加下划线: `FRAME_READY`, `ERROR_OCCURRED`
- 与现有代码保持一致: `PHOTO_MOUSE_MOVEMENT`, `FILE_OPENED`

### 私有属性
- 使用单下划线前缀: `_running`, `_mutex`, `_mode`

### 类型注解
```python
def get_image(self, bit_depth: int, img_path: str, ...) -> tuple[QImage, np.ndarray]:
    ...
```

## PyQt6 规范

### 信号定义位置
```python
class MyWidget(QWidget):
    # 信号定义在类级别，__init__ 之前
    SIGNAL_NAME = pyqtSignal(type1, type2)

    def __init__(self):
        super().__init__()
        ...
```

### 线程安全
- 使用 `QMutex` 保护共享状态
- 使用信号在线程间通信，不直接访问 GUI
- 在 `stop()` 中调用 `wait()` 确保线程结束

### 资源释放
```python
def closeEvent(self, event):
    if self.worker:
        self.worker.stop()
    super().closeEvent(event)
```

## 文件组织

### 新模块结构
```
src/pyrheed/camera/
├── __init__.py      # 导出公共接口
├── worker.py        # CameraWorker QThread
├── widget.py        # CameraWidget 显示组件
├── config.py        # 摄像头配置
└── utils.py         # 工具函数
```

### 导入顺序
```python
# 1. 标准库
import os
import sys

# 2. 第三方库
import cv2
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

# 3. 本地模块
from pyrheed.camera import CameraWorker
```

## 错误处理

### 摄像头错误
```python
try:
    cap = cv2.VideoCapture(device_id)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {device_id}")
except Exception as e:
    self.ERROR_OCCURRED.emit(str(e))
```

### 优雅降级
```python
try:
    import cv2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

# 在 UI 中
if not CAMERA_AVAILABLE:
    self.menuCamera.setEnabled(False)
    self.menuCamera.setToolTip("Camera requires opencv-python")
```

## 测试规范

### 测试文件命名
```
tests/
├── test_camera_worker.py
├── test_camera_widget.py
└── test_camera_integration.py
```

### Mock 摄像头
```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_camera():
    with patch('cv2.VideoCapture') as mock:
        cap = MagicMock()
        cap.isOpened.return_value = True
        cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock.return_value = cap
        yield mock
```
