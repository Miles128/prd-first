"""Tests for prd_first.render."""

from __future__ import annotations

from pathlib import Path

from prd_first.models import FieldDef, PrdMeta, TemplateDef
from prd_first.render import render_prd


def _make_template(fields: list[dict] | None = None) -> TemplateDef:
    if fields is None:
        fields = [
            {"key": "problem", "label": "问题陈述", "required": True, "section": "问题与目标"},
            {"key": "goal", "label": "成功定义", "required": True, "section": "问题与目标"},
            {"key": "scope", "label": "MVP 范围", "required": False, "section": "范围"},
        ]
    return TemplateDef(
        type="test",
        name="测试模板",
        fields=[FieldDef.from_dict(f) for f in fields],
    )


class TestRenderPrd:
    def test_renders_filled_fields(self):
        template = _make_template()
        meta = PrdMeta(type="test")
        meta.set_answer("problem", "这是一个问题")
        meta.set_answer("goal", "这是成功标准")

        result = render_prd(template, meta)
        assert "测试模板" in result
        assert "这是一个问题" in result
        assert "这是成功标准" in result
        assert "_(待补充)_" in result  # scope 未填

    def test_renders_empty_fields(self):
        template = _make_template()
        meta = PrdMeta(type="test")

        result = render_prd(template, meta)
        assert "_(待补充)_" in result

    def test_renders_list_fields(self):
        template = _make_template([
            {"key": "items", "label": "项目列表", "required": False, "type": "list", "section": "列表"},
        ])
        meta = PrdMeta(type="test")
        meta.set_answer("items", ["item1", "item2", "item3"])

        result = render_prd(template, meta)
        assert "- item1" in result
        assert "- item2" in result
        assert "- item3" in result

    def test_renders_bool_fields(self):
        template = _make_template([
            {"key": "yesno", "label": "确认", "required": False, "type": "confirm", "section": "确认"},
        ])
        meta = PrdMeta(type="test")
        meta.set_answer("yesno", True)

        result = render_prd(template, meta)
        assert "是" in result

    def test_sections_grouped(self):
        template = _make_template()
        meta = PrdMeta(type="test")

        result = render_prd(template, meta)
        assert "## 问题与目标" in result
        assert "## 范围" in result
