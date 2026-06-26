"""Tests for prd_first.checker."""

from __future__ import annotations

from prd_first.checker import CheckResult, check
from prd_first.models import FieldDef, PrdMeta, TemplateDef


def _make_template(fields: list[dict]) -> TemplateDef:
    return TemplateDef(
        type="test",
        name="Test",
        fields=[FieldDef.from_dict(f) for f in fields],
    )


class TestCheckResult:
    def test_completeness_pct_empty(self):
        r = CheckResult(template_type="test")
        assert r.completeness_pct == 0

    def test_completeness_pct_half(self):
        r = CheckResult(template_type="test", total=10, filled=5)
        assert r.completeness_pct == 50

    def test_required_pct_no_required(self):
        r = CheckResult(template_type="test", required_total=0, required_filled=0)
        assert r.required_pct == 100

    def test_required_pct_partial(self):
        r = CheckResult(template_type="test", required_total=4, required_filled=2)
        assert r.required_pct == 50

    def test_is_complete_all_filled(self):
        r = CheckResult(template_type="test", required_total=3, required_filled=3)
        assert r.is_complete is True

    def test_is_complete_partial(self):
        r = CheckResult(template_type="test", required_total=3, required_filled=2)
        assert r.is_complete is False

    def test_is_complete_no_required(self):
        """无必填字段时也应视为完整。"""
        r = CheckResult(template_type="test", required_total=0, required_filled=0)
        assert r.is_complete is True


class TestCheck:
    def test_all_filled(self):
        template = _make_template([
            {"key": "a", "label": "A", "required": True},
            {"key": "b", "label": "B", "required": False},
        ])
        meta = PrdMeta(type="test")
        meta.set_answer("a", "value a")
        meta.set_answer("b", "value b")

        result = check(template, meta)
        assert result.is_complete is True
        assert result.required_filled == 1
        assert result.required_total == 1
        assert result.filled == 2
        assert result.total == 2
        assert len(result.missing_required) == 0

    def test_some_missing(self):
        template = _make_template([
            {"key": "a", "label": "A", "required": True},
            {"key": "b", "label": "B", "required": True},
            {"key": "c", "label": "C", "required": False},
        ])
        meta = PrdMeta(type="test")
        meta.set_answer("a", "value a")
        # b is missing

        result = check(template, meta)
        assert result.is_complete is False
        assert result.required_filled == 1
        assert result.required_total == 2
        assert len(result.missing_required) == 1
        assert result.missing_required[0].key == "b"

    def test_no_required_fields(self):
        """无必填字段的模板应视为完整。"""
        template = _make_template([
            {"key": "a", "label": "A", "required": False},
            {"key": "b", "label": "B", "required": False},
        ])
        meta = PrdMeta(type="test")

        result = check(template, meta)
        assert result.is_complete is True
        assert result.required_total == 0
        assert result.required_filled == 0

    def test_skipped_not_counted(self):
        template = _make_template([
            {"key": "a", "label": "A", "required": True},
        ])
        meta = PrdMeta(type="test")
        meta.set_answer("a", None, status="skipped")

        result = check(template, meta)
        assert result.is_complete is False
        assert result.filled == 0

    def test_all_fields_tracked(self):
        template = _make_template([
            {"key": "a", "label": "A", "required": True},
            {"key": "b", "label": "B", "required": False},
        ])
        meta = PrdMeta(type="test")
        meta.set_answer("a", "val")

        result = check(template, meta)
        assert len(result.all_fields) == 2
        assert result.all_fields[0].filled is True
        assert result.all_fields[1].filled is False
