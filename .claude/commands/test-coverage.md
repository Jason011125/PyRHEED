# 测试覆盖率

分析测试覆盖率并生成缺失的测试:

1. 运行测试带覆盖率:
   ```bash
   pytest tests/ --cov=pyrheed --cov-report=html --cov-report=term-missing
   ```

2. 分析覆盖率报告 (htmlcov/index.html)

3. 识别低于 80% 覆盖率阈值的文件

4. 对每个覆盖不足的文件:
   - 分析未测试的代码路径
   - 生成函数的单元测试
   - 生成组件的集成测试
   - 生成关键流程的端到端测试

5. 验证新测试通过

6. 显示前后覆盖率指标

7. 确保项目达到 80%+ 总体覆盖率

## 重点关注

- 正常路径场景
- 错误处理
- 边界情况 (None, 空数组, 边界值)
- 边界条件

## 输出格式

```
测试覆盖率报告
==============

当前覆盖率: 65%
目标覆盖率: 80%

低覆盖率文件:
┌─────────────────────────┬───────┬────────────────────┐
│ 文件                    │ 覆盖率 │ 缺失行            │
├─────────────────────────┼───────┼────────────────────┤
│ src/pyrheed/process.py  │ 45%   │ 120-145, 200-220  │
│ src/pyrheed/canvas.py   │ 52%   │ 80-95, 150-180    │
│ src/pyrheed/window.py   │ 38%   │ 300-400           │
└─────────────────────────┴───────┴────────────────────┘

建议添加的测试:

1. test_process.py
   - test_get_image_with_invalid_path
   - test_get_image_with_raw_format
   - test_apply_filter_edge_cases

2. test_canvas.py
   - test_mouse_drag_selection
   - test_zoom_limits
   - test_coordinate_transform
```

## 运行命令

```bash
# 运行测试带覆盖率
pytest tests/ --cov=pyrheed --cov-report=term-missing

# 生成 HTML 报告
pytest tests/ --cov=pyrheed --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html

# 检查特定模块
pytest tests/ --cov=pyrheed.camera --cov-report=term-missing

# 最低覆盖率检查
pytest tests/ --cov=pyrheed --cov-fail-under=80
```
