# 构建修复命令

增量修复 Python 类型错误和构建问题:

1. 运行类型检查: `mypy src/pyrheed/`

2. 解析错误输出:
   - 按文件分组
   - 按严重程度排序

3. 对每个错误:
   - 显示错误上下文 (前后5行)
   - 解释问题
   - 提出修复方案
   - 应用修复
   - 重新运行检查
   - 验证错误已解决

4. 停止条件:
   - 修复引入新错误
   - 同一错误尝试3次后仍存在
   - 用户请求暂停

5. 显示摘要:
   - 已修复的错误
   - 剩余的错误
   - 新引入的错误

## 常见错误类型

### 类型错误 (mypy)
```python
# 错误: Incompatible types in assignment
x: str = 123  # 错误

# 修复:
x: int = 123  # 或 x: str = "123"
```

### 导入错误
```python
# 错误: Cannot find module 'xxx'

# 修复: 检查模块是否安装，或修正导入路径
```

### PyQt6 信号错误
```python
# 错误: "pyqtSignal" has incompatible type

# 修复: 确保信号在类级别定义，类型正确
FRAME_READY = pyqtSignal(np.ndarray)  # 正确
```

## 运行命令

```bash
# 类型检查
mypy src/pyrheed/ --show-error-codes

# 带详细错误
mypy src/pyrheed/ --show-error-context

# 检查单个文件
mypy src/pyrheed/camera/worker.py
```

每次修复一个错误以确保安全!
