# 验证命令

对当前代码库状态运行全面验证。

## 指令

按以下顺序执行验证:

1. **类型检查**
   - 运行 `mypy src/pyrheed/`
   - 报告所有错误及 file:line

2. **代码检查**
   - 运行 `ruff check src/`
   - 报告警告和错误

3. **测试套件**
   - 运行 `pytest tests/ -v --cov=pyrheed`
   - 报告通过/失败数量
   - 报告覆盖率百分比

4. **print 语句审计**
   - 在源文件中搜索 print()
   - 报告位置

5. **Git 状态**
   - 显示未提交的更改
   - 显示自上次提交以来修改的文件

## 输出格式

生成简洁的验证报告:

```
验证结果: [通过/失败]

类型检查:  [OK/X 个错误]
代码检查:  [OK/X 个问题]
测试:      [X/Y 通过, Z% 覆盖率]
Print语句: [OK/发现 X 个]
Git状态:   [干净/X 个文件已修改]

可以提交 PR: [是/否]
```

如有关键问题，列出并提供修复建议。

## 参数

$ARGUMENTS 可以是:
- `quick` - 仅类型检查 + 代码检查
- `full` - 所有检查 (默认)
- `pre-commit` - 提交前相关检查
- `pre-pr` - 完整检查加安全扫描

## 快速命令

```bash
# 类型检查
mypy src/pyrheed/

# 代码检查
ruff check src/

# 运行测试带覆盖率
pytest tests/ -v --cov=pyrheed --cov-report=term-missing

# 查找 print 语句
grep -rn "print(" src/pyrheed/ --include="*.py"

# Git 状态
git status
git diff --stat
```
