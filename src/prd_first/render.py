"""PRD.md 渲染器。"""

from __future__ import annotations

from typing import Any

from .models import FieldDef, PrdMeta, TemplateDef, _is_filled, _render


def _render_field(field: FieldDef, value: Any) -> str:
    """渲染单个字段为 markdown 小节。"""
    content = _render(value)
    lines = [f"### {field.label}", "", content, ""]
    if field.required and not _is_filled(value):
        lines.append("<!-- 必填项未填写 -->")
    return "\n".join(lines)


def render_prd(template: TemplateDef, meta: PrdMeta) -> str:
    """渲染完整 PRD markdown。"""
    lines: list[str] = [
        f"# {template.name} PRD",
        "",
        f"项目类型: `{template.type}`",
        f"版本: v{meta.version}" + (f" | 更新: {meta.updated_at}" if meta.updated_at else ""),
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

    if meta.changelog:
        lines.append("## 变更记录")
        lines.append("")
        for entry in reversed(meta.changelog[-10:]):
            lines.append(
                f"- v{entry['version']} ({entry.get('at', '')[:19]}): "
                f"更新「{entry['field']}」"
            )
        lines.append("")

    return "\n".join(lines)
