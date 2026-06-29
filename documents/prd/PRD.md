# prd-first PRD

项目类型: `cli-tool` / `ai-skill`
版本: 0.3.0

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
- CLI 零 LLM 依赖，原有 `prd init / check / show` 流程 100% 兼容。
- 所有结论收敛到 PRD 文件（按优先级搜索 `documents/prd/PRD.md`、`docs/PRD.md`、`PRD.md`）+ `meta.yaml`。
- 编码期间能持续回引 PRD 的范围、非目标和验收标准。

## 范围

### P0：CLI 核心能力

- `prd init [type]`：交互式初始化 PRD，支持 4 种项目类型。
- `prd check`：校验必填完整度。
- `prd show`：打印当前 PRD。
- `prd edit <field>`：更新单个字段。
- `prd template list`：列出可用模板。
- 4 套内置模板：web-app、cli-tool、ai-agent、backend-data。

### P0：drill-first 追问能力

- `prd drill <topic>`：对某个字段或主题进行书面化追问清单，保存为 `documents/prd/drill-<topic>.md`。
- `assets/drill-guides/*.yaml`：为每类项目提供决策树追问指南。
- 模板字段 `drill_questions`：为每个字段提供追问线索。
- Skill 中引入 grill-me 核心指令： relentlessly interview、一次一问、推荐答案、沿决策树深挖、允许添加分支。

### P1：扩展与集成

- 支持自定义模板目录。
- 支持导出 PRD 为其他格式。
- 与更多 AI 编程助手规则格式兼容。

## 非目标

- CLI 默认不调用任何 LLM API，不引入 `openai` / `anthropic` 依赖。
- 不做通用的项目管理或任务看板。
- 不替代用户做最终决定，只暴露假设和推荐。
- 不让 AI 在 Skill 中无限追问而不收敛，必须有明确的"结束本分支"机制。

## 工作流

### 快速表单模式

适合需求已经比较清晰的场景：

```
prd init [type] → 交互式问答 → 生成 PRD.md + meta.yaml
    ↓
AI 读取 PRD → 按范围/非目标/验收标准编码
    ↓
需求变化 → prd edit <field> 更新 → PRD 与代码同步
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

## 命令结构

| 命令 | 说明 |
|------|------|
| `prd init [type]` | 交互式初始化 PRD |
| `prd drill <topic>` | 对某个分支进行书面化追问，保存 `drill-<topic>.md` |
| `prd check` | 校验 PRD 完整度 |
| `prd show` | 打印当前 PRD.md |
| `prd edit <field>` | 更新单个字段 |
| `prd template list` | 列出所有模板 |

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

- [x] CLI 核心命令稳定可用，`prd init / check / show` 流程兼容。
- [x] `skill/SKILL.md` 包含 drill-first 核心指令且明确模板为参考。
- [x] 新增 `assets/drill-guides/` 并为 4 种项目类型各提供 guide。
- [x] 4 个模板均增加 `drill_questions` 字段。
- [x] `prd drill <topic>` 能生成追问清单并保存到 `documents/prd/`。
- [x] 全部测试通过，新增 `prd drill` 的 CLI 测试。
- [x] README 与 PRD 同步更新。
