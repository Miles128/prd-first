# prd-first

> **Vibecoding 前先写 PRD。**

prd-first 是一个轻量 CLI + AI Skill，帮你在 AI 开始写业务代码前把计划想清楚，并生成一份结构化、可追踪的 PRD。

它把"想清楚"的过程分成两种模式：

- **快速表单模式**：需求已经清晰，直接 `prd init` 按模板填空。
- **drill-first 模式**：需求模糊或风险高，让 AI 基于决策树地图逐分支追问，直到共享理解。

无论哪种模式，最终都收敛到 `documents/prd/PRD.md` + `documents/prd/meta.yaml`，作为后续编码、验收、需求变更的唯一事实来源。

## 为什么需要 prd-first

Vibecoding 最大的失败模式是"边问边做、边做边改"。一个小时的对话后，你发现：

- AI 已经写了 500 行代码，但方向和你想的不一样。
- 范围悄悄蔓延，原本说"不做"的功能被加了进来。
- 关键假设（用户是谁、失败模式、验收标准）从未被明确。

prd-first 在编码前**拦一刀**：先用结构化 PRD 固定问题、范围、非目标和验收标准，再让 AI 按 PRD 编码。

## 快速开始

### 安装

```bash
pip install prd-first
```

或本地开发安装：

```bash
git clone <repo-url>
cd prd-first
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 生成第一份 PRD

```bash
# 交互式选择项目类型并问答
prd init

# 或直接指定类型
prd init web-app
prd init cli-tool
prd init ai-agent
prd init backend-data
```

生成后查看：

```bash
prd show
prd check
```

## 两种工作流

### 1. 快速表单模式

适合需求已经比较清晰的场景：

```
prd init [type] → 交互式问答 → 生成 PRD.md + meta.yaml
    ↓
AI 读取 PRD → 按范围/非目标/验收标准编码
    ↓
需求变化 → prd edit <field> 更新 → PRD 与代码同步
```

### 2. drill-first 模式

适合需求模糊、风险高的场景。融合 grill-me 的主动追问思想：

```
AI 检查 PRD → 无 PRD 则展示决策树地图 → 逐分支 relentless interview
    ↓
共享理解后 → prd init 收敛结论 → 生成 PRD.md + meta.yaml
    ↓
prd drill <branch> → 对关键分支书面化深挖 → 保存 drill-<branch>.md
    ↓
AI 按 PRD 编码，持续回引范围/非目标/验收标准
```

在 drill-first 模式下，模板只是**决策树参考**：AI 会基于 `assets/drill-guides/*.yaml`
和模板字段的 `drill_questions` 主动追问，并根据你的回答动态增删分支。

## 命令参考

| 命令 | 说明 |
|------|------|
| `prd init [type]` | 交互式初始化 PRD |
| `prd drill <topic>` | 对某个分支书面化追问，保存 `drill-<topic>.md` |
| `prd drill` | 交互选择分支进行追问 |
| `prd check` | 校验 PRD 完整度 |
| `prd show` | 打印当前 PRD.md |
| `prd edit <field>` | 更新单个字段 |
| `prd template list` | 列出所有模板 |

示例：

```bash
# 对"问题陈述"分支深挖
prd drill problem

# 检查 PRD 是否完整
prd check

# 修改某个字段
prd edit goal
```

## 项目类型模板

| 类型 | 说明 | 关键分支 |
|------|------|----------|
| `web-app` | Web 应用、SaaS、管理后台 | 问题、用户、范围、页面、认证、技术栈、验收 |
| `cli-tool` | 命令行工具、脚本 | 问题、命令结构、输入输出、依赖、验收 |
| `ai-agent` | AI/Agent、RAG、LLM 应用 | 问题、角色、输入输出契约、评估、失败模式 |
| `backend-data` | API 服务、数据管道 | 问题、数据来源、数据流、外部依赖、容错、监控 |

## 在 AI 编程助手中使用

将 `skill/SKILL.md` 的内容放入 AI 编程助手的规则文件中：

- **Claude Code**: `~/.claude/CLAUDE.md` 或项目 `.claude/CLAUDE.md`
- **Cursor**: `.cursor/rules/`
- **Codex**: 项目根目录 `AGENTS.md`

然后直接说：

```
帮我做个 todo 应用
```

AI 会自动检测 `documents/prd/PRD.md` 是否存在。没有则进入 drill-first 流程，有则按 PRD 编码。

## 设计原则

- **CLI 零 LLM 依赖**：不调用任何大模型 API，只负责结构化问答和文档管理。
- **模板是参考不是表单**：drill-first 模式下，AI 可以动态增删分支。
- **PRD 是唯一事实来源**：范围、非目标、验收标准是编码期间的硬约束。
- **drill 笔记可持久化**：`prd drill` 生成的追问笔记保存在 `documents/prd/drill-<topic>.md`，供后续回顾。

## License

MIT
