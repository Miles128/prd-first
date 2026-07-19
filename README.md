# prd-first

**Vibecoding 前必须先写详尽 PRD。** 交互式问答生成结构化 PRD，配合 Skill 在 AI 编码前拦截。

## 安装

```bash
pip install prd-first
```

或本地开发安装：

```bash
git clone https://github.com/Miles128/prd-first.git
cd prd-first
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 使用

```bash
prd --version

# 交互式初始化 PRD（推荐）
prd init

# 指定项目类型直接开始
prd init web-app
prd init cli-tool
prd init ai-agent
prd init backend-data
prd init mobile-app
prd init api-service
prd init data-pipeline
prd init browser-extension

# 重新开始（清空已有答案）
prd new web-app

# 检查 PRD 完整度
prd check

# 查看生成的 PRD / 单个字段
prd show
prd show --section problem

# 编辑单个字段（自动 bump 版本 + 记录变更；不带参数进入交互选择）
prd edit
prd edit problem

# 对某个分支做 drill-down 追问，保存为 drill-<topic>.md
prd drill problem

# 列出所有模板
prd template list
```

## 在 AI 编程助手中使用（一键接入）

先安装 CLI，再在项目根执行：

```bash
# 一次装齐 Claude Code + Cursor + Codex
prd skill install

# 或按目标安装
prd skill install claude
prd skill install cursor
prd skill install codex

# Claude Code 装到用户级 skills
prd skill install claude --global
```

| 目标 | 写入位置 |
|------|----------|
| `claude` | `.claude/skills/prd-first/SKILL.md`（`--global` → `~/.claude/skills/...`） |
| `cursor` | `.cursor/rules/prd-first.mdc`（`alwaysApply: true`） |
| `codex` | 项目根 `AGENTS.md`（`<!-- prd-first -->` 标记段，可重复更新） |

装好后重开对话，直接说：

```
帮我做个 todo 应用
```

或显式：`/skill prd-first`。AI 会先检查 `documents/PRD.md`。

源文件也在仓库 `skill/SKILL.md`（与包内 `assets/skill/SKILL.md` 同步）。

## 工作流

```
prd init → 交互式问答 → 生成 documents/PRD.md + documents/meta.yaml
    ↓
prd skill install → AI 助手读取 PRD → 按范围/非目标/验收标准编码
    ↓
需求变化 → prd edit <field> 更新（自动版本号 + changelog）→ PRD 与代码同步
    ↓
字段含糊 → prd drill <topic> 追问 → 保存 drill-<topic>.md 补充说明
```

## 项目类型模板

| 类型 | 说明 | 必填字段 |
|------|------|----------|
| `web-app` | Web 应用、SaaS、管理后台 | 8 |
| `cli-tool` | 命令行工具、脚本 | 9 |
| `ai-agent` | AI/Agent、RAG、LLM 应用 | 10 |
| `backend-data` | API 服务、数据管道 | 11 |
| `mobile-app` | iOS/Android/跨端移动应用 | 9 |
| `api-service` | REST/GraphQL 后端服务、微服务 | 10 |
| `data-pipeline` | ETL/ELT、批处理、实时流 | 12 |
| `browser-extension` | Chrome/Edge 扩展、插件 | 10 |

每种类型都有配套的 drill-guide（追问指南），`prd drill` 时自动加载。

## 发布到 PyPI

维护者发布新版本：

1. 更新 `pyproject.toml` / `__init__.py` 版本号与 `CHANGELOG.md`
2. 合并到 `main` 后打 tag 并创建 GitHub Release：

```bash
git tag v0.3.0
git push origin v0.3.0
gh release create v0.3.0 --generate-notes
```

3. 在 [PyPI](https://pypi.org) 为项目配置 **Trusted Publisher**（GitHub Actions，workflow：`publish.yml`，environment：`pypi`）
4. Release 发布后，`Publish` workflow 会自动 `python -m build` 并上传

也可在 Actions 里手动跑 `Publish`（`workflow_dispatch`）。

## License

MIT
