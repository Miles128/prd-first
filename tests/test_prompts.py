"""Tests for prd_first.prompts."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from prd_first.const import SKIP_SENTINEL
from prd_first.models import FieldDef, PrdMeta
from prd_first.prompts import (
    QuitPrompt,
    apply_answer,
    ask_field,
    ask_list,
    ask_multi,
    ask_single,
    ask_text,
)


def _field(**kwargs) -> FieldDef:
    defaults = {"key": "test", "label": "测试", "prompt": "请输入"}
    defaults.update(kwargs)
    return FieldDef.from_dict(defaults)


class TestAskText:
    @patch("prd_first.prompts.questionary")
    def test_normal(self, mock_q):
        mock_q.text.return_value.ask.return_value = "hello"
        assert ask_text(_field(type="text"), None) == "hello"

    @patch("prd_first.prompts.questionary")
    def test_skip(self, mock_q):
        mock_q.text.return_value.ask.return_value = "s"
        assert ask_text(_field(type="text"), None) == SKIP_SENTINEL

    @patch("prd_first.prompts.questionary")
    def test_quit(self, mock_q):
        mock_q.text.return_value.ask.return_value = "q"
        with pytest.raises(QuitPrompt):
            ask_text(_field(type="text"), None)

    @patch("prd_first.prompts.questionary")
    def test_none_quit(self, mock_q):
        mock_q.text.return_value.ask.return_value = None
        with pytest.raises(QuitPrompt):
            ask_text(_field(type="text"), None)


class TestAskSingle:
    @patch("prd_first.prompts.questionary")
    def test_normal(self, mock_q):
        mock_q.select.return_value.ask.return_value = "A"
        assert ask_single(_field(type="single", choices=["A", "B"]), None) == "A"

    @patch("prd_first.prompts.questionary")
    def test_skip(self, mock_q):
        mock_q.select.return_value.ask.return_value = "⏭️ 跳过"
        assert ask_single(_field(type="single", choices=["A", "B"]), None) == SKIP_SENTINEL

    @patch("prd_first.prompts.questionary")
    def test_quit(self, mock_q):
        mock_q.select.return_value.ask.return_value = "🚪 退出"
        with pytest.raises(QuitPrompt):
            ask_single(_field(type="single", choices=["A", "B"]), None)


class TestAskMulti:
    @patch("prd_first.prompts.questionary")
    def test_normal(self, mock_q):
        mock_q.checkbox.return_value.ask.return_value = ["A"]
        assert ask_multi(_field(type="multi", choices=["A", "B"]), None) == ["A"]

    @patch("prd_first.prompts.questionary")
    def test_skip(self, mock_q):
        mock_q.checkbox.return_value.ask.return_value = ["⏭️ 跳过"]
        assert ask_multi(_field(type="multi", choices=["A", "B"]), None) == SKIP_SENTINEL

    @patch("prd_first.prompts.questionary")
    def test_quit(self, mock_q):
        mock_q.checkbox.return_value.ask.return_value = ["🚪 退出"]
        with pytest.raises(QuitPrompt):
            ask_multi(_field(type="multi", choices=["A", "B"]), None)

    @patch("prd_first.prompts.questionary")
    def test_empty_skip(self, mock_q):
        mock_q.checkbox.return_value.ask.return_value = []
        assert ask_multi(_field(type="multi", choices=["A", "B"]), None) == SKIP_SENTINEL


class TestAskList:
    @patch("prd_first.prompts.questionary")
    def test_normal(self, mock_q):
        mock_q.text.return_value.ask.side_effect = ["a", "b", ""]
        assert ask_list(_field(type="list"), None) == ["a", "b"]

    @patch("prd_first.prompts.questionary")
    def test_empty(self, mock_q):
        mock_q.text.return_value.ask.return_value = ""
        assert ask_list(_field(type="list"), None) == []

    @patch("prd_first.prompts.questionary")
    def test_skip(self, mock_q):
        mock_q.text.return_value.ask.return_value = "s"
        assert ask_list(_field(type="list"), None) == SKIP_SENTINEL


class TestAskField:
    @patch("prd_first.prompts.questionary")
    def test_dispatch_text(self, mock_q):
        mock_q.text.return_value.ask.return_value = "hi"
        assert ask_field(_field(type="text"), PrdMeta.new("x")) == "hi"

    @patch("prd_first.prompts.questionary")
    def test_dispatch_unknown_as_text(self, mock_q):
        mock_q.text.return_value.ask.return_value = "fallback"
        assert ask_field(_field(type="unknown"), PrdMeta.new("x")) == "fallback"


class TestApplyAnswer:
    def test_string(self):
        meta = PrdMeta.new("x")
        apply_answer(meta, _field(), "v")
        assert meta.get("test") == "v"

    def test_list(self):
        meta = PrdMeta.new("x")
        apply_answer(meta, _field(), ["a"])
        assert meta.get("test") == ["a"]

    def test_skip(self):
        meta = PrdMeta.new("x")
        apply_answer(meta, _field(), SKIP_SENTINEL)
        assert meta.get("test") is None

    def test_empty_string_ignored(self):
        meta = PrdMeta.new("x")
        apply_answer(meta, _field(), "  ")
        assert meta.get("test") is None

    def test_empty_list_ignored(self):
        meta = PrdMeta.new("x")
        apply_answer(meta, _field(), [])
        assert meta.get("test") is None
