"""Tests for prd_first.models."""

from __future__ import annotations

import pytest

from prd_first.models import Answer, FieldDef, PrdMeta, TemplateDef, load_template, list_templates


class TestFieldDef:
    def test_from_dict_minimal(self):
        fd = FieldDef.from_dict({"key": "problem"})
        assert fd.key == "problem"
        assert fd.label == "problem"
        assert fd.required is False
        assert fd.type == "text"

    def test_from_dict_full(self):
        fd = FieldDef.from_dict({
            "key": "goal",
            "label": "成功定义",
            "required": True,
            "type": "single",
            "prompt": "怎么做?",
            "why": "因为",
            "placeholder": "xxx",
            "choices": ["A", "B"],
            "section": "目标",
        })
        assert fd.key == "goal"
        assert fd.label == "成功定义"
        assert fd.required is True
        assert fd.type == "single"
        assert fd.choices == ["A", "B"]
        assert fd.section == "目标"


class TestAnswer:
    def test_pending_not_filled(self):
        a = Answer(value=None, status="pending")
        assert a.is_filled is False

    def test_skipped_not_filled(self):
        a = Answer(value="hello", status="skipped")
        assert a.is_filled is False

    def test_empty_string_not_filled(self):
        a = Answer(value="", status="answered")
        assert a.is_filled is False

    def test_whitespace_string_not_filled(self):
        a = Answer(value="   ", status="answered")
        assert a.is_filled is False

    def test_string_filled(self):
        a = Answer(value="hello", status="answered")
        assert a.is_filled is True

    def test_bool_filled(self):
        a = Answer(value=True, status="answered")
        assert a.is_filled is True

    def test_list_filled(self):
        a = Answer(value=["a", "b"], status="answered")
        assert a.is_filled is True

    def test_empty_list_not_filled(self):
        a = Answer(value=[], status="answered")
        assert a.is_filled is False

    def test_render_pending(self):
        a = Answer(value=None, status="pending")
        assert a.render() == "_(待补充)_"

    def test_render_bool(self):
        assert Answer(value=True, status="answered").render() == "是"
        assert Answer(value=False, status="answered").render() == "否"

    def test_render_list(self):
        a = Answer(value=["a", "b"], status="answered")
        assert a.render() == "- a\n- b"

    def test_render_string(self):
        a = Answer(value="hello", status="answered")
        assert a.render() == "hello"


class TestPrdMeta:
    def test_new(self):
        meta = PrdMeta.new("web-app")
        assert meta.type == "web-app"
        assert meta.created_at != ""
        assert meta.updated_at != ""
        assert meta.answers == {}

    def test_set_get_answer(self):
        meta = PrdMeta.new("web-app")
        meta.set_answer("problem", "test problem")
        a = meta.get_answer("problem")
        assert a.value == "test problem"
        assert a.status == "answered"

    def test_set_answer_skipped(self):
        meta = PrdMeta.new("web-app")
        meta.set_answer("problem", None, status="skipped")
        a = meta.get_answer("problem")
        assert a.value is None
        assert a.status == "skipped"

    def test_yaml_roundtrip(self):
        meta = PrdMeta.new("web-app")
        meta.set_answer("problem", "test problem")
        meta.set_answer("goal", ["a", "b"])
        yaml_str = meta.to_yaml()
        restored = PrdMeta.from_yaml(yaml_str)
        assert restored.type == "web-app"
        assert restored.answers["problem"] == "test problem"
        assert restored.answers["goal"] == ["a", "b"]

    def test_from_yaml_empty(self):
        meta = PrdMeta.from_yaml("")
        assert meta.type == ""
        assert meta.answers == {}

    def test_from_yaml_invalid(self):
        with pytest.raises(Exception):
            PrdMeta.from_yaml("{{invalid yaml")


class TestTemplateDef:
    def test_find_existing(self):
        t = TemplateDef(
            type="test",
            name="Test",
            fields=[FieldDef(key="a", label="A"), FieldDef(key="b", label="B")],
        )
        assert t.find("a") is not None
        assert t.find("a").key == "a"

    def test_find_missing(self):
        t = TemplateDef(type="test", name="Test", fields=[])
        assert t.find("nonexistent") is None

    def test_required_fields(self):
        t = TemplateDef(
            type="test",
            name="Test",
            fields=[
                FieldDef(key="a", label="A", required=True),
                FieldDef(key="b", label="B", required=False),
                FieldDef(key="c", label="C", required=True),
            ],
        )
        assert len(t.required_fields) == 2
        assert [f.key for f in t.required_fields] == ["a", "c"]


class TestLoadTemplate:
    def test_load_web_app(self):
        t = load_template("web-app")
        assert t.type == "web-app"
        assert t.name == "Web 应用"
        assert len(t.fields) > 0

    def test_load_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            load_template("nonexistent-type")


class TestListTemplates:
    def test_list_all(self):
        templates = list_templates()
        types = [t.type for t in templates]
        assert "web-app" in types
        assert "cli-tool" in types
        assert "ai-agent" in types
        assert "backend-data" in types

    def test_count(self):
        templates = list_templates()
        assert len(templates) == 4
