---
description: Python 代码全面审查，检查 PEP 8 合规性、类型提示、安全性和 Pythonic 惯用法。
---

# Python 代码审查

调用 **python-reviewer** 代理进行全面的 Python 特定代码审查。

## 功能

1. **识别 Python 更改**: 通过 `git diff` 找到修改的 `.py` 文件
2. **运行静态分析**: 执行 `ruff`, `mypy`
3. **安全扫描**: 检查 SQL 注入、命令注入、不安全反序列化
4. **类型安全审查**: 分析类型提示和 mypy 错误
5. **Pythonic 代码检查**: 验证代码遵循 PEP 8 和 Python 最佳实践
6. **生成报告**: 按严重程度分类问题

## 审查类别

### 关键 (必须修复)
- SQL/命令注入漏洞
- 不安全的 eval/exec 使用
- pickle 不安全反序列化
- 硬编码凭证
- YAML 不安全加载
- 裸 except 子句隐藏错误

### 高 (应该修复)
- 公共函数缺少类型提示
- 可变默认参数
- 静默吞掉异常
- 资源未使用上下文管理器
- C 风格循环而非列表推导
- 使用 type() 而非 isinstance()
- 无锁的竞态条件

### 中 (考虑)
- PEP 8 格式违规
- 公共函数缺少 docstring
- 使用 print 而非 logging
- 低效的字符串操作
- 魔术数字无命名常量
- 未使用 f-string 格式化

## 自动检查运行

```bash
# 类型检查
mypy src/pyrheed/

# 代码检查和格式化
ruff check src/
ruff format --check src/

# 安全扫描
bandit -r src/pyrheed/

# 运行测试
pytest tests/ --cov=pyrheed --cov-report=term-missing
```

## 常见修复

### 添加类型提示
```python
# 之前
def calculate(x, y):
    return x + y

# 之后
def calculate(x: float, y: float) -> float:
    return x + y
```

### 使用上下文管理器
```python
# 之前
f = open("file.txt")
data = f.read()
f.close()

# 之后
with open("file.txt") as f:
    data = f.read()
```

### 使用列表推导
```python
# 之前
result = []
for item in items:
    if item.active:
        result.append(item.name)

# 之后
result = [item.name for item in items if item.active]
```

### 修复可变默认值
```python
# 之前
def append(value, items=[]):
    items.append(value)
    return items

# 之后
def append(value, items=None):
    if items is None:
        items = []
    items.append(value)
    return items
```

### 使用 f-string
```python
# 之前
greeting = "Hello, " + name + "!"
greeting2 = "Hello, {}".format(name)

# 之后
greeting = f"Hello, {name}!"
```

### 修复循环中字符串拼接
```python
# 之前
result = ""
for item in items:
    result += str(item)

# 之后
result = "".join(str(item) for item in items)
```

## PyQt6 特定检查

### 信号定义
```python
# 错误: 信号在 __init__ 中定义
class Worker(QThread):
    def __init__(self):
        self.finished = pyqtSignal()  # 错误!

# 正确: 信号在类级别定义
class Worker(QThread):
    finished = pyqtSignal()  # 正确

    def __init__(self):
        super().__init__()
```

### 线程安全
```python
# 检查是否在非主线程更新 GUI
# 检查是否使用 QMutex 保护共享状态
# 检查 stop() 是否调用 wait()
```

## 批准条件

| 状态 | 条件 |
|------|------|
| ✅ 批准 | 无关键或高优先级问题 |
| ⚠️ 警告 | 仅中等问题 (谨慎合并) |
| ❌ 阻止 | 发现关键或高优先级问题 |
