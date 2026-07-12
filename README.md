# prd-first

> **Vibecoding 前先写 PRD。**

prd-first 是一个轻量 CLI + AI Skill，帮你在 AI 开始写业务代码前把计划想清楚，并生成一份结构化、可追踪的 PRD。

它把"想清楚"的过程分成两种模式：

- **快速表单模式**：需求已经清晰，直接 `prd init` 按模板填空。
- **drill-first 模式**：需求模糊或风险高，让 AI 基于决策树地图逐分支追问，直到共享理解。

无论哪种模式，最终都收敛到 PRD 文件（按优先级搜索 `documents/prd/PRD.md`、`docs/PRD.md`、`PRD.md`）+ `meta.yaml`，作为后续编码、验收、需求变更的唯一事实来源。

当前版本：**0.2.0**（与 `pyproject.toml` 一致）。

## 为什么需要 prd-first

Vibecoding 最大的失败模式是"边问边做、边做边改"。一个小时的对话后，你发现：

- AI 已经写了 500 行代码，但方向和你想的不一样。
- 范围悄悄蔓延，原本说"不做"的功能被加了进来。
- 关键假设（用户是谁、失败模式、验收标准）从未被明确。

prd-first 在编码前**拦一刀**：先用结构化 PRD 固定问题、范围、非目标和验收标准，再让 AI 按 PRD 编码。

## 快速开始

### 安装

本地开发安装（推荐）：

```bash
git clone https://github.com/Miles128/prd-first.git
cd prd-first
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# 或: uv pip install -e ".[dev]"
```

确认 CLI：

```bash
prd --help
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

中途可用 `q` 退出；再次 `prd init` 会跳过已填字段并续答。

## 两种工作流

### 1. 快速表单模式

适合需求已经比较清晰的场景：

```
prd init [type] → 交互式问答 → 生成 PRD.md + meta.yaml
    ↓
AI 读取 PRD → 按范围/非目标/验收标准编码
    ↓
需求变化 → 编辑 PRD.md / meta.yaml，或重跑 prd init 补填 → 必要时再 prd check
```

### 2. drill-first 模式

适合需求模糊、风险高的场景。融合 grill-me 的主动追问思想（主要由 **Skill** 驱动对话；CLI 负责持久化）：

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

### 3. 增量开发（现有项目加功能）

由 **Skill** 执行（CLI 无单独 `prd increment` 命令）：

1. 读取现有 PRD（多路径搜索，见下）
2. 只追问新功能范围与整合问题（复用、接口、数据、依赖、测试）
3. 更新现有 PRD（标注新增/修改）并刷新验收标准

### PRD 查找路径

CLI 与 Skill 按优先级搜索：

1. `documents/prd/PRD.md`（默认写入位置）
2. `docs/PRD.md`
3. 项目根目录 `PRD.md`

同目录下的 `meta.yaml`、`drill-<topic>.md` 一并使用。

## 命令参考

当前 CLI 仅提供以下命令：

| 命令 | 说明 |
|------|------|
| `prd init [type]` | 交互式初始化 / 续填 PRD |
| `prd init --force` | 清空已有答案重新开始 |
| `prd drill <topic>` | 对某个分支书面化追问，保存 `drill-<topic>.md` |
| `prd drill` | 交互选择分支进行追问 |
| `prd check` | 校验 PRD 完整度（退出码 0=完整，2=必填缺失） |
| `prd show` | 打印当前 PRD.md |

示例：

```bash
prd drill problem
prd check
prd show
```

> 未实现：`prd edit`、`prd template list`。改字段请直接编辑 `meta.yaml` / `PRD.md`，或重跑 `prd init`；列模板见下方表格或 `src/prd_first/assets/templates/`。

## 项目类型模板

| 类型 | 说明 | 关键分支 |
|------|------|----------|
| `web-app` | Web 应用、SaaS、管理后台 | 问题、用户、范围、页面、认证、技术栈、验收 |
| `cli-tool` | 命令行工具、脚本 | 问题、命令结构、输入输出、依赖、验收 |
| `ai-agent` | AI/Agent、RAG、LLM 应用 | 问题、角色、输入输出契约、评估、失败模式 |
| `backend-data` | API 服务、数据管道 | 问题、数据来源、数据流、外部依赖、容错、监控 |

## 在 AI 编程助手中使用

将 `skill/SKILL.md` 接入助手（本机也可软链到 skills 目录）：

- **Claude Code**: `~/.claude/CLAUDE.md` 或项目 `.claude/CLAUDE.md`
- **Cursor**: `.cursor/rules/` 或 skills 目录
- **Codex**: 项目根目录 `AGENTS.md`

然后直接说：

```
帮我做个 todo 应用
```

AI 会自动检测 PRD 是否存在。没有则进入 drill-first；有则按 PRD 编码；增量需求则走增量追问流程。

## 设计原则

- **CLI 零 LLM 依赖**：不调用任何大模型 API，只负责结构化问答和文档管理。
- **模板是参考不是表单**：drill-first 模式下，AI 可以动态增删分支。
- **PRD 是唯一事实来源**：范围、非目标、验收标准是编码期间的硬约束。
- **drill 笔记可持久化**：`prd drill` 生成的追问笔记保存在 PRD 同目录的 `drill-<topic>.md`。

## License

MIT
