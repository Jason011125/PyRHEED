# Commit 格式规范

基于 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)

## 格式

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

## Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(video): add FrameSource abstract base class` |
| `fix` | Bug 修复 | `fix(canvas): resolve memory leak on frame update` |
| `docs` | 文档变更 | `docs(readme): update installation instructions` |
| `style` | 代码格式 (不影响功能) | `style(source): fix import order` |
| `refactor` | 重构 (不是新功能也不是修复) | `refactor(roi): simplify intensity calculation` |
| `perf` | 性能优化 | `perf(video): use numpy vectorization for frame processing` |
| `test` | 添加测试 | `test(source): add edge case tests for seek` |
| `build` | 构建系统或外部依赖 | `build: add opencv-python to dependencies` |
| `ci` | CI 配置 | `ci: add GitHub Actions workflow` |
| `chore` | 其他杂项 | `chore: update .gitignore` |
| `revert` | 回退 | `revert: revert "feat(video): add camera support"` |

## Scope 范围 (PyRHEED 项目)

| Scope | 说明 |
|-------|------|
| `video` | 视频/摄像头模块 (`src/pyrheed/video/`) |
| `intensity` | 光强分析模块 (`src/pyrheed/intensity/`) |
| `roi` | ROI 管理 |
| `canvas` | 画布组件 |
| `window` | 主窗口 |
| `process` | 图像处理 |
| `chart` | 图表组件 |
| `config` | 配置系统 |

## 示例

### 简单提交
```
feat(video): add ImageSequenceSource implementation
```

### 带正文的提交
```
feat(roi): add multi-ROI support

- Support adding multiple ROI regions on canvas
- Each ROI has independent color and label
- ROI intensity history tracked separately
```

### 带 Breaking Change 的提交
```
feat(video)!: change FrameSource.open() signature

BREAKING CHANGE: open() now returns FrameInfo instead of bool
```

### 带 footer 的提交
```
fix(intensity): correct average calculation for empty ROI

Fixes #123
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## 规则

1. **type 必须小写**: `feat` 不是 `Feat`
2. **scope 可选但推荐**: 帮助快速定位改动范围
3. **description 用祈使句**: "add" 不是 "added" 或 "adds"
4. **description 不要句号结尾**
5. **body 和 footer 用空行分隔**
6. **Breaking Change 用 `!` 或 `BREAKING CHANGE:` 标注**

## Git 命令

```bash
# 简单提交
git commit -m "feat(video): add camera support"

# 多行提交 (使用 heredoc)
git commit -m "$(cat <<'EOF'
feat(video): add camera support

- Add CameraSource class
- Support device enumeration
- Add FPS control

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

## 自动化检查

可选：安装 commitlint 进行自动检查

```bash
npm install -g @commitlint/cli @commitlint/config-conventional
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js
```
