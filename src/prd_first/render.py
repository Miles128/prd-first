"""PRD.md 渲染器。"""

from __future__ import annotations

from typing import Any

from .models import FieldDef, PrdMeta, TemplateDef, _is_filled, _render


def _render_field(field: FieldDef, value: Any) -> str:
    """渲染单个字段为 markdown 小节。"""
    content = _render(value)
    lines = [f"### {field.label}", "", content, ""]
    if not _is_filled(value):
        lines.append("<!-- 必填项未填写 -->")
    return "\n".join(lines)


def render_prd(template: TemplateDef, meta: PrdMeta) -> str:
    """渲染完整 PRD markdown。"""
    lines: list[str] = [
        f"# {template.name} PRD",
        "",
        f"项目类型: `{template.type}`",
        "",
        "## 概述",
        "",
        template.description,
        "",
        "## 需求详情",
        "",
    ]

    for f in template.fields:
        lines.append(_render_field(f, meta.get(f.key)))
        lines.append("")

    return "\n".join(lines)
