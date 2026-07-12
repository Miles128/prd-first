# prd-first PRD

项目类型: `cli-tool` / `ai-skill`
版本: 0.2.0

## 概述

prd-first 是一个 Vibecoding 前的规划拦截工具。它通过 CLI + AI Skill 的组合，
强制开发者在 AI 开始写业务代码前先写一份结构化 PRD，并把"想清楚"的过程从死板表单升级为
**drill-first 主动追问**。

核心公式：**决策树地图 → 逐分支 drill-down → 共享理解 → 结构化 PRD → 按 PRD 编码**。

## 问题陈述

- Vibecoding 容易让团队边问边做、边做边改，范围蔓延和隐藏假设在项目后期才暴露。
- 传统 PRD 工具太重型，开发者不愿意用；轻量表单又容易"应付式填写"，填完了也没想清楚。
- 很多项目（尤其是 AI Agent、后端数据管道）的风险不在字段是否填满，而在字段之间的依赖、边界情况和失败模式。
- grill-me 等对话式追问能解决"想清楚"的问题，但缺少持久化结构和可追踪的 PRD。

## 目标用户

使用 AI 编程助手（Claude Code / Codex / Cursor）的开发者与小型团队，希望在编码前把计划想清楚，同时保留一份可演进、可验收的 PRD。

## 成功定义

- 用户能在 5 分钟内通过 CLI 或 Skill 启动 PRD 编写。
- Skill 模式下，AI 能基于模板做决策树地图，逐个分支追问到共享理解。
- 用户偏离模板时，AI 能动态添加新分支而不是拒绝或生硬拉回。
- CLI 零 LLM 依赖；`prd init / check / show / drill` 可用。
- 所有结论收敛到 PRD 文件（按优先级搜索 `documents/prd/PRD.md`、`docs/PRD.md`、`PRD.md`）+ `meta.yaml`。
- 编码期间能持续回引 PRD 的范围、非目标和验收标准。
- 增量开发时，Skill 能基于现有 PRD 只追问新增与整合问题，而不强制重写整份 PRD。

## 范围

### P0：CLI 核心能力（已实现）

- `prd init [type]`：交互式初始化 PRD，支持 4 种项目类型；支持断点续答与 `--force` 重置。
- `prd check`：校验必填完整度。
- `prd show`：打印当前 PRD。
- `prd drill [topic]`：书面化追问并保存 `drill-<topic>.md`。
- 4 套内置模板：web-app、cli-tool、ai-agent、backend-data。
- 多路径搜索 PRD：`documents/prd/` → `docs/` → 项目根目录。

### P0：drill-first 追问能力（已实现）

- `assets/drill-guides/*.yaml`：为每类项目提供决策树追问指南。
- 模板字段 `drill_questions`：为每个字段提供追问线索。
- Skill（`skill/SKILL.md`）引入 grill-me 核心指令：relentlessly interview、一次一问、推荐答案、沿决策树深挖、允许添加分支。
- Skill 增量 PRD 流程：读现有 PRD → 追问新功能与整合分支 → 更新 PRD / 验收标准。

### P1：未实现（后续）

- `prd edit <field>`：单字段 CLI 更新。
- `prd template list`：列出可用模板。
- 支持自定义模板目录。
- 支持导出 PRD 为其他格式。
- 与更多 AI 编程助手规则格式兼容。
- 独立的增量 CLI 子命令（当前增量仅由 Skill 驱动）。

## 非目标

- CLI 默认不调用任何 LLM API，不引入 `openai` / `anthropic` 依赖。
- 不做通用的项目管理或任务看板。
- 不替代用户做最终决定，只暴露假设和推荐。
- 不让 AI 在 Skill 中无限追问而不收敛，必须有明确的"结束本分支"机制。
- 不在本版本承诺 PyPI 正式发布；安装以本地 `pip install -e .` / `uv` 为准。

## 工作流

### 快速表单模式

适合需求已经比较清晰的场景：

```
prd init [type] → 交互式问答 → 生成 PRD.md + meta.yaml
    ↓
AI 读取 PRD → 按范围/非目标/验收标准编码
    ↓
需求变化 → 编辑 PRD.md / meta.yaml，或重跑 prd init 补填 → prd check
```

### drill-first 模式

适合需求模糊、风险高的场景：

```
AI 检查 PRD → 无 PRD 则展示决策树地图 → 逐分支 relentless interview
    ↓
共享理解后 → prd init 收敛结论 → 生成 PRD.md + meta.yaml
    ↓
prd drill <branch> → 对关键分支书面化深挖 → 保存 drill-<branch>.md
    ↓
AI 按 PRD 编码，持续回引范围/非目标/验收标准
```

在 drill-first 模式下，模板只是**决策树参考**：AI 基于 `assets/drill-guides/*.yaml`
和模板字段的 `drill_questions` 主动追问，并根据回答动态增删分支。

### 增量开发模式（Skill）

```
读取现有 PRD → 追问新功能价值 / MVP
    ↓
追问整合：复用、接口、数据、依赖、测试
    ↓
更新现有 PRD（标注新增与修改）→ 刷新验收标准
```

## 命令结构

| 命令 | 状态 | 说明 |
|------|------|------|
| `prd init [type]` | 已实现 | 交互式初始化 / 续填 |
| `prd init --force` | 已实现 | 清空重来 |
| `prd drill [topic]` | 已实现 | 书面化追问，保存 `drill-<topic>.md` |
| `prd check` | 已实现 | 校验完整度 |
| `prd show` | 已实现 | 打印当前 PRD.md |
| `prd edit <field>` | 未实现（P1） | — |
| `prd template list` | 未实现（P1） | — |

## 项目类型模板

| 类型 | 说明 | 关键分支 |
|------|------|----------|
| `web-app` | Web 应用、SaaS、管理后台 | 问题、用户、范围、页面、认证、技术栈、验收 |
| `cli-tool` | 命令行工具、脚本 | 问题、命令结构、输入输出、依赖、验收 |
| `ai-agent` | AI/Agent、RAG、LLM 应用 | 问题、角色、输入输出契约、评估、失败模式 |
| `backend-data` | API 服务、数据管道 | 问题、数据来源、数据流、外部依赖、容错、监控 |

## 技术栈

- Python 3.10+
- typer / questionary / jinja2 / pyyaml / rich
- 无 LLM 依赖

## 验收标准

- [x] CLI 核心命令可用：`prd init / check / show / drill`。
- [x] `skill/SKILL.md` 包含 drill-first 核心指令且明确模板为参考。
- [x] `assets/drill-guides/` 为 4 种项目类型各提供 guide。
- [x] 4 个模板均含 `drill_questions` 字段。
- [x] `prd drill <topic>` 能生成追问清单并保存到 PRD 目录。
- [x] 多路径搜索 PRD（`documents/prd`、`docs`、根目录）。
- [x] Skill 描述增量 PRD 流程。
- [x] 测试通过（含 `prd drill` / storage 相关测试）。
- [x] README 与 PRD 与实现一致：不含未实现命令的“已可用”表述；版本为 0.2.0。
- [ ] `prd edit` / `prd template list`（明确为 P1，未实现）。
- [ ] 自定义模板目录、导出格式、更多助手规则适配（P1）。
