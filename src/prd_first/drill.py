"""Drill-down 风格的书面化追问会话。

CLI 保持零 LLM 依赖：把模板字段的 drill_questions 和 drill-guides 中的 drill
作为追问清单，引导用户逐个回答并保存为 Markdown 笔记。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import questionary
import yaml

from .const import TEMPLATES_DIR
from .models import TemplateDef


def _drill_guides_dir() -> Path:
    return TEMPLATES_DIR.parent / "drill-guides"


@dataclass
class DrillBranch:
    """drill-guide 中的单个分支。"""

    key: str
    label: str
    drill: list[str] = field(default_factory=list)
    trigger: str = ""


@dataclass
class DrillGuide:
    """某项目类型的完整追问指南。"""

    type: str
    name: str
    description: str = ""
    branches: list[DrillBranch] = field(default_factory=list)
    optional_branches: list[DrillBranch] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DrillGuide:
        return cls(
            type=data["type"],
            name=data.get("name", data["type"]),
            description=data.get("description", ""),
            branches=[DrillBranch(**b) for b in data.get("branches", [])],
            optional_branches=[DrillBranch(**b) for b in data.get("optional_branches", [])],
        )


def load_drill_guide(template_type: str) -> DrillGuide | None:
    """加载指定类型的 drill-guide。不存在返回 None。"""
    path = _drill_guides_dir() / f"{template_type}.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return DrillGuide.from_dict(data)


def collect_questions(
    template: TemplateDef,
    guide: DrillGuide | None,
    topic: str,
) -> list[str]:
    """为指定 topic 收集追问问题。

    优先级：
    1. 模板中匹配字段的 drill_questions
    2. drill-guide 中匹配分支的 drill
    3. 通用 fallback 问题
    """
    topic_lower = topic.lower()

    # 1. 模板字段
    for f in template.fields:
        if f.key.lower() == topic_lower and f.drill_questions:
            return list(f.drill_questions)

    # 2. drill-guide 分支
    if guide is not None:
        all_branches = list(guide.branches) + list(guide.optional_branches)
        for b in all_branches:
            if b.key.lower() == topic_lower and b.drill:
                return list(b.drill)

    # 3. fallback
    return [
        f"关于「{topic}」，用户现在的做法或痛点是什么？",
        f"如果不处理「{topic}」，最坏结果是什么？",
        f"关于「{topic}」有没有隐含的假设或依赖？",
    ]


def run_drill_session(questions: list[str]) -> list[tuple[str, str]]:
    """逐个提问，返回 (question, answer) 列表。"""
    notes: list[tuple[str, str]] = []
    total = len(questions)
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{total}] {q}")
        print("  (输入 q 退出保存)")
        answer = questionary.text("你的回答:").ask()
        if answer is None or answer.strip().lower() == "q":
            break
        notes.append((q, answer.strip()))
    return notes


def render_drill_notes(topic: str, notes: list[tuple[str, str]]) -> str:
    """把追问笔记渲染为 Markdown。"""
    lines = [
        f"# Drill 笔记: {topic}",
        "",
        f"生成时间: {datetime.now(timezone.utc).astimezone().isoformat()}",
        "",
        "## 追问与回答",
        "",
    ]
    for q, a in notes:
        lines.append(f"### Q: {q}")
        lines.append("")
        lines.append(a)
        lines.append("")
    return "\n".join(lines)
