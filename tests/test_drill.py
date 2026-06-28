"""Tests for prd_first.drill."""

from __future__ import annotations

from prd_first import drill
from prd_first.models import TemplateDef


def _template_with_drill() -> TemplateDef:
    return TemplateDef.from_dict({
        "type": "test",
        "name": "Test",
        "fields": [
            {
                "key": "problem",
                "label": "问题陈述",
                "required": True,
                "type": "text",
                "drill_questions": ["模板字段问题 A", "模板字段问题 B"],
            },
            {
                "key": "other",
                "label": "其他",
                "type": "text",
            },
        ],
    })


def _guide() -> drill.DrillGuide:
    return drill.DrillGuide.from_dict({
        "type": "test",
        "name": "Test Guide",
        "branches": [
            {
                "key": "other",
                "label": "其他",
                "drill": ["guide 问题 A", "guide 问题 B"],
            },
        ],
    })


class TestLoadDrillGuide:
    def test_load_existing(self):
        guide = drill.load_drill_guide("web-app")
        assert guide is not None
        assert guide.type == "web-app"
        assert len(guide.branches) > 0

    def test_load_missing(self):
        assert drill.load_drill_guide("not-a-type") is None


class TestCollectQuestions:
    def test_template_field_takes_priority(self):
        template = _template_with_drill()
        guide = _guide()
        questions = drill.collect_questions(template, guide, "problem")
        assert questions == ["模板字段问题 A", "模板字段问题 B"]

    def test_guide_fallback(self):
        template = _template_with_drill()
        guide = _guide()
        questions = drill.collect_questions(template, guide, "other")
        assert questions == ["guide 问题 A", "guide 问题 B"]

    def test_generic_fallback(self):
        template = _template_with_drill()
        guide = _guide()
        questions = drill.collect_questions(template, guide, "unknown")
        assert all("unknown" in q for q in questions)


class TestRenderDrillNotes:
    def test_contains_topic_and_qa(self):
        md = drill.render_drill_notes("problem", [("Q1", "A1"), ("Q2", "A2")])
        assert "# Drill 笔记: problem" in md
        assert "Q1" in md
        assert "A1" in md
        assert "Q2" in md
        assert "A2" in md
