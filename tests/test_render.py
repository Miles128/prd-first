"""Tests for prd_first.render."""

from __future__ import annotations

from prd_first.models import PrdMeta, TemplateDef
from prd_first.render import render_prd


def _make_template(fields: list[dict]) -> TemplateDef:
    return TemplateDef.from_dict({
        "type": "test",
        "name": "Test",
        "description": "测试模板",
        "fields": fields,
    })


def test_render_basic():
    template = _make_template([
        {"key": "title", "label": "标题", "required": True, "type": "text"},
        {"key": "tags", "label": "标签", "required": False, "type": "list"},
    ])
    meta = PrdMeta.new("test")
    meta.set("title", "Hello")
    meta.set("tags", ["a", "b"])

    md = render_prd(template, meta)
    assert "# Test PRD" in md
    assert "Hello" in md
    assert "- a" in md
    assert "- b" in md


def test_render_placeholder():
    template = _make_template([
        {"key": "title", "label": "标题", "required": True, "type": "text"},
    ])
    meta = PrdMeta.new("test")
    md = render_prd(template, meta)
    assert "待补充" in md
    assert "必填项未填写" in md


def test_render_bool():
    template = _make_template([
        {"key": "ok", "label": "确认", "required": False, "type": "text"},
    ])
    meta = PrdMeta.new("test")
    meta.set("ok", True)
    md = render_prd(template, meta)
    assert "是" in md
