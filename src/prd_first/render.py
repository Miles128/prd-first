"""Jinja2 渲染器:把 TemplateDef + PrdMeta 渲染成 PRD.md。

支持按 section 分组,未填字段渲染为占位符。
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .const import TEMPLATES_DIR
from .models import FieldDef, PrdMeta, TemplateDef


def _group_by_section(template: TemplateDef) -> OrderedDict[str, list[FieldDef]]:
    """把字段按 section 分组,保留定义顺序。无 section 的归到'其他'。"""
    groups: OrderedDict[str, list[FieldDef]] = OrderedDict()
    for f in template.fields:
        sec = f.section or "其他"
        groups.setdefault(sec, []).append(f)
    return groups


def render_prd(
    template: TemplateDef,
    meta: PrdMeta,
    templates_dir: Optional[Path] = None,
) -> str:
    """渲染完整 PRD markdown。"""
    d = templates_dir or TEMPLATES_DIR
    env = Environment(
        loader=FileSystemLoader(str(d)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=select_autoescape(enabled_extensions=("j2", "html", "xml")),
    )
    # 模板文件名:<type>.md.j2;若不存在则回退到 _generic.md.j2
    specific = d / f"{template.type}.md.j2"
    template_name = specific.name if specific.exists() else "_generic.md.j2"
    j2 = env.get_template(template_name)

    def get_render(key: str) -> str:
        answer = meta.get_answer(key)
        return answer.render()

    sections = _group_by_section(template)
    return j2.render(
        template=template,
        meta=meta,
        sections=sections,
        get_render=get_render,
    )
