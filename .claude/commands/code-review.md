# 代码审查

对未提交更改进行全面的安全和质量审查:

1. 获取更改的文件: `git diff --name-only HEAD`

2. 对每个更改的文件检查:

**安全问题 (关键):**
- 硬编码的凭证、API 密钥、令牌
- SQL 注入漏洞
- 命令注入漏洞
- 缺少输入验证
- 不安全的依赖
- 路径遍历风险
- 不安全的 pickle/yaml 加载

**代码质量 (高):**
- 函数超过 50 行
- 文件超过 800 行
- 嵌套深度超过 4 层
- 缺少错误处理
- print() 语句
- TODO/FIXME 注释
- 公共 API 缺少类型注解

**最佳实践 (中):**
- 可变默认参数 `def foo(items=[])`
- 裸 except 子句
- 代码/注释中使用 emoji
- 新代码缺少测试
- 未使用上下文管理器

**PyQt6 特定:**
- 信号未在类级别定义
- 线程安全问题
- 未正确释放资源
- closeEvent 未调用 super()

3. 生成报告:
   - 严重程度: 关键, 高, 中, 低
   - 文件位置和行号
   - 问题描述
   - 建议修复

4. 如果发现关键或高优先级问题则阻止提交

绝不批准有安全漏洞的代码!

## 输出格式

```
代码审查报告
============

审查文件:
- src/pyrheed/camera/worker.py (修改)
- src/pyrheed/window.py (修改)

发现问题:

[关键] 命令注入漏洞
文件: src/pyrheed/utils.py:42
问题: 用户输入直接传递给 os.system()
```python
os.system(f"convert {user_input}")  # 危险
```
修复: 使用 subprocess 并转义参数
```python
subprocess.run(["convert", user_input], check=True)
```

[高] 可变默认参数
文件: src/pyrheed/process.py:18
问题: 可变默认参数导致共享状态
```python
def process_frames(frames=[]):  # 危险
```
修复: 使用 None 作为默认值
```python
def process_frames(frames=None):
    if frames is None:
        frames = []
```

摘要:
- 关键: 1
- 高: 1
- 中: 0

建议: ❌ 阻止合并直到关键问题修复
```
