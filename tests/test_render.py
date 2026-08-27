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


def test_render_optional_empty_has_no_required_comment():
    template = _make_template([
        {"key": "note", "label": "备注", "required": False, "type": "text"},
    ])
    meta = PrdMeta.new("test")
    md = render_prd(template, meta)
    assert "待补充" in md
    assert "必填项未填写" not in md


def test_render_bool():
    template = _make_template([
        {"key": "ok", "label": "确认", "required": False, "type": "text"},
    ])
    meta = PrdMeta.new("test")
    meta.set("ok", True)
    md = render_prd(template, meta)
    assert "是" in md


class TestRenderVersion:
    def test_render_includes_version(self, tmp_path):
        from prd_first.models import PrdMeta, load_template

        template = load_template("web-app")
        meta = PrdMeta.new("web-app")
        meta.bump("problem", None, "p")

        md = render_prd(template, meta)
        assert "版本: v2" in md
        assert "## 变更记录" in md
        assert "更新「problem」" in md

    def test_render_no_changelog(self, tmp_path):
        from prd_first.models import PrdMeta, load_template

        template = load_template("web-app")
        meta = PrdMeta.new("web-app")

        md = render_prd(template, meta)
        assert "版本: v1" in md
        assert "## 变更记录" not in md
