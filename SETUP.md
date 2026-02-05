# PyRHEED 环境安装指南

## 系统要求

- Python 3.12+
- Git

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/Jason011125/PyRHEED.git
cd PyRHEED
```

### 2. 创建虚拟环境

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. 升级 pip

```bash
pip install --upgrade pip
```

### 4. 安装依赖

#### 方式 A: 从 pyproject.toml 安装（推荐）

```bash
pip install -e .
```

#### 方式 B: 手动安装核心依赖

如果方式 A 失败，使用此方法：

```bash
pip install PyQt6>=6.7.0 PyQt6-Charts>=6.7.0 opencv-python matplotlib>=3.9.0 numpy>=1.26.4 pillow>=10.3.0 scipy>=1.13.0
```

### 5. 验证安装

```bash
python -c "import PyQt6, cv2, matplotlib, numpy; print('✓ 所有依赖已安装')"
```

### 6. 运行演示程序

```bash
python scripts/test_video_demo.py
```

## 常见问题

### macOS: pip 提示权限错误

```bash
# 使用用户安装模式
pip install --user -e .
```

### Windows: 提示 "python" 命令不存在

使用 `python3` 或 `py` 替代 `python`

### 虚拟环境激活后仍找不到模块

确认虚拟环境已正确激活（命令行前应显示 `(.venv)`），然后重新安装依赖。
