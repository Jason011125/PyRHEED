# 重构清理

安全地识别和删除死代码，带测试验证:

1. 运行死代码分析:
   - 使用 `vulture` 查找未使用的代码
   - 使用 `ruff` 查找未使用的导入
   - 手动检查未引用的文件

2. 生成报告到 `.reports/dead-code-analysis.md`

3. 按严重程度分类发现:
   - 安全: 测试文件、未使用的工具函数
   - 谨慎: 公共 API、组件
   - 危险: 配置文件、主入口点

4. 仅提议安全的删除

5. 每次删除前:
   - 运行完整测试套件
   - 验证测试通过
   - 应用更改
   - 重新运行测试
   - 测试失败则回滚

6. 显示清理摘要

## 运行命令

```bash
# 安装 vulture
pip install vulture

# 查找未使用代码
vulture src/pyrheed/ --min-confidence 80

# 查找未使用导入
ruff check src/ --select F401

# 查找未使用变量
ruff check src/ --select F841
```

## 输出格式

```
死代码分析报告
==============

扫描文件: 45
发现问题: 12

安全删除 (5):
- src/pyrheed/utils.py:45 - unused function 'deprecated_helper'
- src/pyrheed/old_canvas.py - 整个文件未使用
- src/pyrheed/process.py:120 - unused import 'json'

谨慎删除 (4):
- src/pyrheed/api.py:30 - function 'get_data' 可能被外部调用
- src/pyrheed/window.py:200 - method '_on_legacy_event'

危险 - 不建议删除 (3):
- src/pyrheed/__main__.py - 入口点
- src/pyrheed/config.py - 配置文件
- tests/conftest.py - pytest 配置

建议:
1. 先删除"安全删除"列表中的项目
2. 对"谨慎删除"项目进行人工审查
3. 不要删除"危险"列表中的项目
```

## 清理步骤

```bash
# 1. 创建检查点
/checkpoint create "before-cleanup"

# 2. 运行分析
vulture src/pyrheed/ --min-confidence 80 > .reports/vulture.txt

# 3. 删除确认安全的代码
# (手动或使用编辑器)

# 4. 运行测试验证
pytest tests/ -v

# 5. 如果测试失败，回滚
git checkout -- src/

# 6. 如果成功，提交
git add -A && git commit -m "refactor: remove dead code"
```

删除代码前务必先运行测试!
