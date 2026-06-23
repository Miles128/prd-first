# prd-first

**Vibecoding 前必须先写详尽 PRD。** 交互式问答生成结构化 PRD，配合 Skill 在 AI 编码前拦截。

## 安装

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

## 使用

```bash
# 交互式初始化 PRD（推荐）
prd init

# 指定项目类型直接开始
prd init web-app
prd init cli-tool
prd init ai-agent
prd init backend-data

# 重新开始（清空已有答案）
prd new web-app

# 检查 PRD 完整度
prd check

# 查看生成的 PRD
prd show

# 编辑单个字段
prd edit problem

# 列出所有模板
prd template list
```

## 在 AI 编程助手中使用

### Claude Code / Codex

在对话中输入：

```
/skill prd-first
帮我做个 todo 应用
```

AI 会自动检测 `.prd/PRD.md` 是否存在，没有就引导你走问答流程。

### Cursor

在 `.cursor/rules/` 中添加 prd-first 的 SKILL.md 内容，或直接告诉 AI：

> 先检查 .prd/PRD.md，没有就用 prd init 生成

## 工作流

```
prd init → 交互式问答 → 生成 .prd/PRD.md + .prd/meta.yaml
    ↓
AI 编程助手读取 PRD → 按范围/非目标/验收标准编码
    ↓
需求变化 → prd edit <field> 更新 → PRD 与代码同步
```

## 项目类型模板

| 类型 | 说明 | 必填字段 |
|------|------|----------|
| `web-app` | Web 应用、SaaS、管理后台 | 9 |
| `cli-tool` | 命令行工具、脚本 | 9 |
| `ai-agent` | AI/Agent、RAG、LLM 应用 | 11 |
| `backend-data` | API 服务、数据管道 | 10 |

## 作为 Skill 使用

将 `skill/SKILL.md` 的内容放入 AI 编程助手的规则文件中：

- **Claude Code**: `~/.claude/CLAUDE.md` 或项目 `.claude/CLAUDE.md`
- **Cursor**: `.cursor/rules/`
- **Codex**: 项目根目录 `AGENTS.md`

## License

MIT
