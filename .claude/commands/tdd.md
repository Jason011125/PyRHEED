---
description: 测试驱动开发流程。先定义接口，先写测试，再实现最小代码通过测试。确保 80%+ 覆盖率。
---

# TDD 命令

调用 **tdd-guide** 代理执行测试驱动开发方法论。

## 功能

1. **定义接口** - 先定义类型/接口
2. **先写测试** - 编写失败的测试 (RED)
3. **最小实现** - 写刚好能通过的代码 (GREEN)
4. **重构** - 在测试通过的情况下改进代码 (REFACTOR)
5. **验证覆盖率** - 确保 80%+ 测试覆盖率

## 使用场景

使用 `/tdd` 当:
- 实现新功能
- 添加新函数/组件
- 修复 bug (先写复现 bug 的测试)
- 重构现有代码
- 构建关键业务逻辑

## TDD 循环

```
RED → GREEN → REFACTOR → REPEAT

RED:      写一个失败的测试
GREEN:    写最小代码让测试通过
REFACTOR: 改进代码，保持测试通过
REPEAT:   下一个功能/场景
```

## 示例

```
User: /tdd 需要一个计算图像灰度直方图的函数

Agent (tdd-guide):
# TDD 会话: 图像灰度直方图计算器

## 步骤 1: 定义接口 (SCAFFOLD)

```python
# src/pyrheed/histogram.py
import numpy as np
from numpy.typing import NDArray

def calculate_histogram(
    image: NDArray[np.uint8],
    bins: int = 256
) -> NDArray[np.int64]:
    """计算灰度图像的直方图。

    Args:
        image: 灰度图像数组
        bins: 直方图的 bin 数量

    Returns:
        直方图数组
    """
    raise NotImplementedError()
```

## 步骤 2: 编写失败测试 (RED)

```python
# tests/test_histogram.py
import numpy as np
import pytest
from pyrheed.histogram import calculate_histogram

class TestCalculateHistogram:
    def test_uniform_image_returns_single_peak(self):
        # Arrange
        image = np.full((100, 100), 128, dtype=np.uint8)

        # Act
        hist = calculate_histogram(image)

        # Assert
        assert hist[128] == 10000  # 100x100 像素
        assert hist.sum() == 10000

    def test_gradient_image_has_uniform_distribution(self):
        # Arrange
        image = np.arange(256, dtype=np.uint8).reshape(16, 16)

        # Act
        hist = calculate_histogram(image)

        # Assert
        assert np.all(hist == 1)

    def test_empty_image_returns_zero_histogram(self):
        # Arrange
        image = np.zeros((0, 0), dtype=np.uint8)

        # Act
        hist = calculate_histogram(image)

        # Assert
        assert hist.sum() == 0

    def test_custom_bins(self):
        # Arrange
        image = np.full((10, 10), 200, dtype=np.uint8)

        # Act
        hist = calculate_histogram(image, bins=16)

        # Assert
        assert len(hist) == 16
```

## 步骤 3: 运行测试 - 验证失败

```bash
pytest tests/test_histogram.py -v

FAILED tests/test_histogram.py::TestCalculateHistogram::test_uniform_image
    NotImplementedError

4 failed
```

✅ 测试按预期失败，准备实现。

## 步骤 4: 最小实现 (GREEN)

```python
# src/pyrheed/histogram.py
import numpy as np
from numpy.typing import NDArray

def calculate_histogram(
    image: NDArray[np.uint8],
    bins: int = 256
) -> NDArray[np.int64]:
    if image.size == 0:
        return np.zeros(bins, dtype=np.int64)

    hist, _ = np.histogram(image.ravel(), bins=bins, range=(0, 256))
    return hist.astype(np.int64)
```

## 步骤 5: 运行测试 - 验证通过

```bash
pytest tests/test_histogram.py -v

PASSED tests/test_histogram.py::TestCalculateHistogram::test_uniform_image
PASSED tests/test_histogram.py::TestCalculateHistogram::test_gradient_image
PASSED tests/test_histogram.py::TestCalculateHistogram::test_empty_image
PASSED tests/test_histogram.py::TestCalculateHistogram::test_custom_bins

4 passed
```

✅ 所有测试通过!

## 步骤 6: 检查覆盖率

```bash
pytest tests/test_histogram.py --cov=pyrheed.histogram --cov-report=term-missing

Name                    Stmts   Miss  Cover
-------------------------------------------
pyrheed/histogram.py        6      0   100%

Coverage: 100% ✅ (目标: 80%)
```

✅ TDD 会话完成!
```

## TDD 最佳实践

**应该做:**
- ✅ 先写测试，再实现
- ✅ 运行测试验证失败后再实现
- ✅ 写最小代码让测试通过
- ✅ 只在测试通过后重构
- ✅ 添加边界情况和错误场景
- ✅ 目标 80%+ 覆盖率 (关键代码 100%)

**不应该做:**
- ❌ 先实现再写测试
- ❌ 跳过每次变更后运行测试
- ❌ 一次写太多代码
- ❌ 忽略失败的测试
- ❌ 测试实现细节 (应测试行为)

## 覆盖率要求

- **80% 最低** 所有代码
- **100% 要求** 用于:
  - 图像处理算法
  - 数据分析计算
  - 核心业务逻辑

## 与其他命令配合

- 先用 `/plan` 理解要构建什么
- 用 `/tdd` 带测试实现
- 用 `/build-fix` 修复构建错误
- 用 `/code-review` 审查实现
- 用 `/test-coverage` 验证覆盖率
