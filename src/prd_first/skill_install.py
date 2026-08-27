"""将 prd-first Skill 安装到各 AI 助手目录。"""

from __future__ import annotations

from pathlib import Path

from .const import PACKAGE_ROOT

SKILL_ASSET = PACKAGE_ROOT / "assets" / "skill" / "SKILL.md"

CURSOR_FRONTMATTER = """\
---
description: Vibecoding 前必须先写详尽 PRD。开始编码前先检查 documents/PRD.md。
alwaysApply: true
---

"""

CODEX_BEGIN = "<!-- prd-first:begin -->"
CODEX_END = "<!-- prd-first:end -->"


def load_skill_text() -> str:
    if not SKILL_ASSET.exists():
        raise FileNotFoundError(f"找不到内置 Skill 文件: {SKILL_ASSET}")
    return SKILL_ASSET.read_text(encoding="utf-8")


def install_claude(root: Path, *, user_global: bool = False) -> Path:
    """安装到 Claude Code skills 目录。"""
    if user_global:
        base = Path.home() / ".claude" / "skills" / "prd-first"
    else:
        base = root / ".claude" / "skills" / "prd-first"
    base.mkdir(parents=True, exist_ok=True)
    target = base / "SKILL.md"
    target.write_text(load_skill_text(), encoding="utf-8")
    return target


def install_cursor(root: Path) -> Path:
    """安装到 Cursor rules。"""
    base = root / ".cursor" / "rules"
    base.mkdir(parents=True, exist_ok=True)
    target = base / "prd-first.mdc"
    # Cursor rule 用 alwaysApply;去掉 YAML frontmatter 里的 name 块冲突,保留正文
    body = load_skill_text()
    if body.startswith("---"):
        parts = body.split("---", 2)
        body = parts[2].lstrip("\n") if len(parts) >= 3 else body
    target.write_text(CURSOR_FRONTMATTER + body, encoding="utf-8")
    return target


def install_codex(root: Path) -> Path:
    """写入/更新项目根 AGENTS.md 中的 prd-first 段。"""
    target = root / "AGENTS.md"
    block = f"{CODEX_BEGIN}\n{load_skill_text().rstrip()}\n{CODEX_END}\n"
    if target.exists():
        text = target.read_text(encoding="utf-8")
        if CODEX_BEGIN in text and CODEX_END in text:
            before, rest = text.split(CODEX_BEGIN, 1)
            _, after = rest.split(CODEX_END, 1)
            text = before.rstrip() + "\n\n" + block + after.lstrip("\n")
        else:
            text = text.rstrip() + "\n\n" + block
    else:
        text = block
    target.write_text(text, encoding="utf-8")
    return target
