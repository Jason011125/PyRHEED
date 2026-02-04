---
name: analyze-frame
description: 分析图像帧处理流程
arguments:
  - name: type
    description: 分析类型 (line-scan/integral/chi-scan)
    required: false
---

# /analyze-frame 命令

分析 PyRHEED 中图像帧的处理流程。

## 用法

```
/analyze-frame              # 分析完整流程
/analyze-frame line-scan    # 分析线扫描流程
/analyze-frame integral     # 分析积分流程
/analyze-frame chi-scan     # 分析 chi 扫描流程
```

## 分析内容

### 数据流

```
输入 (文件/摄像头)
    ↓
process.Image.get_image() / get_image_from_frame()
    ↓
numpy.ndarray (灰度图像)
    ↓
canvas.Canvas.set_photo()
    ↓
用户交互 (画线/框/弧)
    ↓
process.Image.get_line_scan() / get_integral() / get_chi_scan()
    ↓
profile_chart.ProfileChart (显示结果)
```

### 关键函数

- `process.py:get_line_scan()` - 提取线剖面
- `process.py:get_integral()` - 矩形积分
- `process.py:get_chi_scan()` - 弧形扫描

### 性能瓶颈

- `get_chi_scan()` 计算量大，需要优化
- 可考虑 ROI 裁剪减少计算量
- 可考虑 GPU 加速 (已有 pycuda 支持)
