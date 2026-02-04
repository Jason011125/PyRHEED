# 更新文档

从代码源同步文档:

1. 读取 pyproject.toml 或 setup.py
   - 提取项目元数据
   - 提取依赖列表
   - 提取脚本命令

2. 读取 .env.example (如果存在)
   - 提取所有环境变量
   - 记录用途和格式

3. 扫描代码中的 docstring
   - 提取公共 API 文档
   - 识别缺失的 docstring

4. 生成/更新文档:
   - README.md 中的安装说明
   - API 文档
   - 配置说明

5. 识别过时文档:
   - 查找 90+ 天未修改的文档
   - 列出以供人工审查

6. 显示差异摘要

## 文档检查项

### README.md
- [ ] 安装说明是最新的
- [ ] 依赖列表完整
- [ ] 使用示例可运行
- [ ] 截图是最新的

### CLAUDE.md
- [ ] 项目结构准确
- [ ] 开发命令正确
- [ ] 规范与代码一致

### Docstrings
- [ ] 所有公共函数有 docstring
- [ ] 参数类型和描述完整
- [ ] 返回值有说明
- [ ] 示例代码可运行

## 输出格式

```
文档更新报告
============

检查文件: 15
需要更新: 4

更新项:
1. README.md
   - 依赖版本过时 (opencv-python 4.8 -> 4.9)
   - 添加新的开发命令

2. src/pyrheed/process.py
   - 3 个公共函数缺少 docstring

3. CLAUDE.md
   - 项目结构需要添加 camera/ 目录

过时文档 (90+ 天未更新):
- docs/old_api.md (180 天)
- docs/deprecated.md (120 天)

建议:
1. 运行 `pip freeze > requirements.txt` 更新依赖
2. 为标记的函数添加 docstring
3. 考虑删除过时文档
```

## 运行命令

```bash
# 检查 docstring 覆盖率
pydocstyle src/pyrheed/

# 生成 API 文档
pdoc --html src/pyrheed/ --output-dir docs/api

# 检查 README 中的代码块
# (手动验证示例代码)
```

单一信息源: pyproject.toml 和代码
