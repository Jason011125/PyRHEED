# PyRHEED 摄像头支持技术规划

## 核心挑战

```
当前模式（静态图片）:
  图片 → 完整分析 → 精确结果
  时间: 无限制，精度: 100%

目标模式（实时视频）:
  视频流 → ??? → 实时反馈
  时间: 受限（需要实时），精度: ???
```

**核心矛盾**: 实时性 vs 准确性

---

## 分析：当前处理流程的时间消耗

### 三种分析模式

| 模式 | 函数 | 计算复杂度 | 估计耗时 |
|------|------|-----------|---------|
| Line Scan | `get_line_scan()` | O(n) | < 10ms |
| Integral | `get_integral()` | O(n*w) | < 50ms |
| Chi Scan | `get_chi_scan()` | O(n*m*k) | 100-500ms |

### 瓶颈分析

```python
# get_chi_scan() 中的嵌套循环 - 主要瓶颈
for i in range(...):           # chi 角度步数
    for j in range(...):       # 像素遍历
        if 条件判断:           # 每个像素的几何判断
            indices.append()
```

---

## 方案设计：三级处理架构

```
┌─────────────────────────────────────────────────────────────┐
│                    摄像头视频流                              │
│                        30 fps                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Level 1: 实时预览层 (Preview)                   │
│  - 直接显示原始帧                                           │
│  - 无分析处理                                               │
│  - 延迟: < 33ms (30fps)                                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ 用户选择分析区域 (ROI)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Level 2: 快速分析层 (Quick Analysis)           │
│  - 只处理 ROI 区域                                          │
│  - 简化算法 (降采样/近似)                                    │
│  - 实时趋势显示                                             │
│  - 延迟: < 100ms (10fps)                                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ 用户触发"捕获"
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Level 3: 精确分析层 (Full Analysis)            │
│  - 捕获单帧                                                 │
│  - 完整精度分析                                             │
│  - 与现有图片分析完全一致                                    │
│  - 延迟: 无限制                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 详细方案

### Level 1: 实时预览

**目标**: 让用户看到摄像头画面，选择分析区域

```python
class CameraPreview:
    """仅显示，不分析"""

    def on_frame(self, frame: np.ndarray):
        # 直接转换显示，无处理
        qimg = self._to_qimage(frame)
        self.display.setPixmap(QPixmap.fromImage(qimg))
```

**精度影响**: 无（不涉及分析）

---

### Level 2: 快速分析（关键设计）

**目标**: 实时显示分析趋势，帮助用户调整

#### 策略 2.1: ROI 裁剪

```python
# 只分析用户选择的区域，而非全图
def quick_analyze(self, frame: np.ndarray, roi: ROI):
    cropped = frame[roi.y:roi.y+roi.h, roi.x:roi.x+roi.w]
    # 分析区域从 2600x1450 减少到例如 400x400
    # 计算量减少约 26 倍
```

#### 策略 2.2: 降采样

```python
def quick_line_scan(self, frame, start, end, downsample=4):
    """每隔 downsample 个像素采样一次"""
    # 原本 1000 个点 → 250 个点
    # 速度提升 4 倍，精度损失 ~5%
```

#### 策略 2.3: 预计算几何

```python
class ChiScanOptimizer:
    """预计算 chi scan 的像素索引"""

    def __init__(self, center, radius, width, chi_range):
        # 一次性计算所有需要的像素索引
        self.indices = self._precompute_indices()
        # 之后每帧只需要索引查找

    def scan(self, frame):
        # O(1) 索引查找，而非 O(n*m) 遍历
        return frame[self.indices].sum(axis=1)
```

#### 策略 2.4: 帧跳过

```python
class FrameSkipper:
    """如果处理跟不上，自动跳帧"""

    def __init__(self, target_fps=10):
        self.target_interval = 1.0 / target_fps
        self.last_process_time = 0

    def should_process(self, frame_time):
        if frame_time - self.last_process_time >= self.target_interval:
            self.last_process_time = frame_time
            return True
        return False
```

**精度权衡表**:

| 策略 | 速度提升 | 精度损失 | 适用场景 |
|------|---------|---------|---------|
| ROI 裁剪 | 10-50x | 0% | 总是使用 |
| 2x 降采样 | 4x | ~2% | 推荐 |
| 4x 降采样 | 16x | ~10% | 粗略预览 |
| 预计算几何 | 10-100x | 0% | chi scan 必用 |
| 帧跳过 | 可变 | 0% | 自动调节 |

---

### Level 3: 精确分析

**目标**: 用户确定参数后，捕获帧进行完整分析

```python
def capture_and_analyze(self):
    """捕获当前帧，使用与图片完全相同的分析流程"""

    # 1. 捕获帧
    frame = self.camera.capture_frame()

    # 2. 转换为与图片加载相同的格式
    img_array = self.image_worker.get_image_from_frame(
        frame,
        bit_depth=16,  # 与 rawpy 输出一致
        # ... 其他参数
    )

    # 3. 使用现有的精确分析
    # 完全复用 process.py 中的代码
    result = self.image_worker.get_chi_scan(
        center, radius, width, chi_range, tilt, img_array
    )

    return result  # 精度 100%，与图片分析一致
```

**精度影响**: 0%（与现有图片分析完全一致）

---

## 数据反馈设计

### 实时反馈 UI

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │                     │  │     实时趋势图 (快速)       │  │
│  │    摄像头预览       │  │   ~~~~~~~~~~~~~~~~~~~~~~~~  │  │
│  │    [ROI 框]         │  │   强度随时间变化            │  │
│  │                     │  │   (Level 2 分析结果)        │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              精确剖面图 (捕获后)                      │   │
│  │   ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁                                   │   │
│  │   (Level 3 分析结果，与图片分析一致)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [实时分析: ON/OFF]  [捕获] [导出]  FPS: 28.5              │
└─────────────────────────────────────────────────────────────┘
```

### 数据输出格式

```python
@dataclass
class AnalysisResult:
    """分析结果数据结构"""

    # 元数据
    timestamp: datetime
    source: Literal["camera", "file"]
    analysis_level: Literal["quick", "full"]

    # 分析参数
    roi: Optional[ROI]
    center: QPointF
    radius: float
    # ...

    # 结果数据
    x_data: np.ndarray  # K 值或 chi 角度
    y_data: np.ndarray  # 强度

    # 精度指示
    confidence: float  # 0-1, quick 分析时标注置信度
```

---

## 实施路线图

### Phase 1: 基础摄像头 + 精确分析 (MVP)

```
Week 1-2:
├── 摄像头预览 (Level 1)
├── 单帧捕获
└── 复用现有分析代码 (Level 3)

用户可以: 看预览 → 手动捕获 → 精确分析
精度: 100%
```

### Phase 2: 快速分析

```
Week 3-4:
├── ROI 选择
├── 降采样 line scan
├── 预计算 chi scan 优化
└── 实时趋势显示 (Level 2)

用户可以: 实时看到分析趋势
精度: Level 2 约 90-95%, Level 3 仍为 100%
```

### Phase 3: 性能优化

```
Week 5-6:
├── NumPy 向量化优化
├── 可选 GPU 加速 (pycuda)
├── 多线程流水线
└── 自适应帧率

目标: Level 2 达到 15+ fps
```

---

## 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 摄像头帧与 RAW 图像色彩差异 | 分析结果可能不同 | 提供校准功能 |
| 快速分析精度不够 | 用户误判 | 明确标注"仅供参考" |
| 处理速度跟不上 | 卡顿 | 自动帧跳过 |
| 不同摄像头兼容性 | 无法使用 | 提供设备选择和测试 |

---

## 结论

**核心原则**: 分层处理，精度可控

- **预览**: 只显示，不分析（实时）
- **快速分析**: 用于调参和趋势观察（准实时，精度略降）
- **精确分析**: 捕获后完整分析（非实时，精度 100%）

这样既满足了实时反馈的需求，又保证了最终数据的准确性。用户可以根据场景选择合适的模式。
