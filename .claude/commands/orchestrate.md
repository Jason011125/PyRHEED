# 编排命令

复杂任务的顺序代理工作流。

## 用法

`/orchestrate [workflow-type] [task-description]`

## 工作流类型

### feature
完整功能实现工作流:
```
planner -> tdd-guide -> code-reviewer -> security-reviewer
```

### bugfix
Bug 调查和修复工作流:
```
debugger -> tdd-guide -> code-reviewer
```

### refactor
安全重构工作流:
```
architect -> code-reviewer -> tdd-guide
```

### security
安全聚焦审查:
```
security-reviewer -> code-reviewer -> architect
```

## 执行模式

对工作流中的每个代理:

1. **调用代理** 带上前一代理的上下文
2. **收集输出** 作为结构化交接文档
3. **传递给下一代理**
4. **汇总结果** 生成最终报告

## 交接文档格式

代理之间创建交接文档:

```markdown
## 交接: [前一代理] -> [下一代理]

### 上下文
[已完成工作的摘要]

### 发现
[关键发现或决策]

### 修改的文件
[涉及的文件列表]

### 未解决问题
[下一代理需要处理的问题]

### 建议
[建议的下一步]
```

## 示例: 功能工作流

```
/orchestrate feature "添加摄像头实时预览"
```

执行:

1. **Planner 代理**
   - 分析需求
   - 创建实现计划
   - 识别依赖
   - 输出: `交接: planner -> tdd-guide`

2. **TDD Guide 代理**
   - 读取 planner 交接
   - 先写测试
   - 实现以通过测试
   - 输出: `交接: tdd-guide -> code-reviewer`

3. **Code Reviewer 代理**
   - 审查实现
   - 检查问题
   - 建议改进
   - 输出: `交接: code-reviewer -> security-reviewer`

4. **Security Reviewer 代理**
   - 安全审计
   - 漏洞检查
   - 最终批准
   - 输出: 最终报告

## 最终报告格式

```
编排报告
====================
工作流: feature
任务: 添加摄像头实时预览
代理: planner -> tdd-guide -> code-reviewer -> security-reviewer

摘要
-------
[一段摘要]

代理输出
-------------
Planner: [摘要]
TDD Guide: [摘要]
Code Reviewer: [摘要]
Security Reviewer: [摘要]

修改的文件
-------------
[所有修改的文件列表]

测试结果
------------
[测试通过/失败摘要]

安全状态
---------------
[安全发现]

建议
--------------
[可以发布 / 需要修改 / 被阻塞]
```

## 参数

$ARGUMENTS:
- `feature <description>` - 完整功能工作流
- `bugfix <description>` - Bug 修复工作流
- `refactor <description>` - 重构工作流
- `security <description>` - 安全审查工作流
- `custom <agents> <description>` - 自定义代理序列

## 自定义工作流示例

```
/orchestrate custom "architect,tdd-guide,code-reviewer" "重新设计图像处理管道"
```

## 提示

1. **从 planner 开始** 处理复杂功能
2. **始终包含 code-reviewer** 合并前
3. **使用 security-reviewer** 处理敏感代码
4. **保持交接简洁** - 聚焦下一代理需要的内容
5. **必要时在代理间运行 verify**
