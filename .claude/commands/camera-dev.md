---
name: camera-dev
description: 摄像头功能开发辅助命令
arguments:
  - name: action
    description: 操作类型 (scaffold/test/integrate/review)
    required: true
---

# /camera-dev 命令

摄像头功能开发辅助命令。

## 用法

```
/camera-dev scaffold     # 创建摄像头模块骨架
/camera-dev test         # 运行摄像头相关测试
/camera-dev integrate    # 检查集成状态
/camera-dev review       # 代码审查
```

## scaffold - 创建模块骨架

创建 `src/pyrheed/camera/` 目录和基础文件：
- `__init__.py`
- `worker.py` - CameraWorker
- `widget.py` - CameraWidget
- `config.py` - 配置管理

## test - 运行测试

```bash
pytest tests/test_camera*.py -v
```

## integrate - 检查集成

检查以下集成点：
1. `window.py` 是否添加摄像头菜单
2. `process.py` 是否有 `get_image_from_frame`
3. `canvas.py` 是否支持帧显示
4. `pyproject.toml` 是否包含 opencv-python

## review - 代码审查

使用 camera-integrator agent 审查代码：
- 信号命名是否一致
- 线程是否安全
- 资源是否正确释放
- 错误处理是否完善
