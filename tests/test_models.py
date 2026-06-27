"""Tests for prd_first.models."""

from __future__ import annotations

import pytest
import yaml

from prd_first.models import (
    FieldDef,
    PrdMeta,
    TemplateDef,
    _is_filled,
    _render,
    list_templates,
    load_template,
)


class TestIsFilled:
    def test_none_false(self):
        assert not _is_filled(None)

    def test_empty_string_false(self):
        assert not _is_filled("")

    def test_whitespace_false(self):
        assert not _is_filled("  ")

    def test_string_true(self):
        assert _is_filled("hello")

    def test_empty_list_false(self):
        assert not _is_filled([])

    def test_list_true(self):
        assert _is_filled(["a"])

    def test_bool_true(self):
        assert _is_filled(False)


class TestRender:
    def test_none_render(self):
        assert "待补充" in _render(None)

    def test_bool_render(self):
        assert _render(True) == "是"
        assert _render(False) == "否"

    def test_list_render(self):
        assert _render(["a", "b"]) == "- a\n- b"


class TestFieldDef:
    def test_from_dict_defaults(self):
        f = FieldDef.from_dict({"key": "x", "label": "X"})
        assert f.type == "text"
        assert f.required is False
        assert f.choices == []


class TestTemplateDef:
    def test_from_dict(self):
        t = TemplateDef.from_dict({
            "type": "x",
            "name": "X",
            "fields": [{"key": "a", "label": "A"}],
        })
        assert t.find("a") is not None
        assert t.find("missing") is None


class TestPrdMeta:
    def test_new(self):
        meta = PrdMeta.new("web-app")
        assert meta.type == "web-app"
        assert meta.answers == {}

    def test_get_set(self):
        meta = PrdMeta.new("x")
        assert meta.get("k") is None
        meta.set("k", "v")
        assert meta.get("k") == "v"

    def test_to_from_yaml(self):
        meta = PrdMeta.new("x")
        meta.set("k", "v")
        text = meta.to_yaml()
        restored = PrdMeta.from_yaml(text)
        assert restored.type == "x"
        assert restored.get("k") == "v"

    def test_from_yaml_invalid(self):
        with pytest.raises(yaml.YAMLError):
            PrdMeta.from_yaml("{{invalid yaml")


class TestListTemplates:
    def test_load_template_web_app(self):
        t = load_template("web-app")
        assert t.type == "web-app"
        assert len(t.fields) > 0

    def test_list_templates(self):
        templates = list_templates()
        types = {t.type for t in templates}
        assert types >= {"web-app", "cli-tool", "ai-agent", "backend-data"}
