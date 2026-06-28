"""Tests for prd_first.cli."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from prd_first import storage
from prd_first.cli import app
from prd_first.const import SKIP_SENTINEL
from prd_first.models import PrdMeta

runner = CliRunner()


class TestInit:
    def test_init_no_existing(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("prd_first.cli.ask_field") as mock_ask:
            mock_ask.return_value = SKIP_SENTINEL
            result = runner.invoke(app, ["init", "web-app"])
        assert result.exit_code == 0
        assert "PRD 已生成" in result.output
        assert storage.meta_exists()

    def test_init_continue_existing(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        meta.set("problem", "p")
        storage.save_meta(meta)

        with patch("prd_first.cli.ask_field") as mock_ask:
            mock_ask.return_value = SKIP_SENTINEL
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "继续补充" in result.output
        assert storage.load_meta().get("problem") == "p"

    def test_init_force_clears(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        meta.set("problem", "p")
        storage.save_meta(meta)

        with patch("prd_first.cli.ask_field") as mock_ask:
            mock_ask.return_value = SKIP_SENTINEL
            result = runner.invoke(app, ["init", "web-app", "--force"])

        assert result.exit_code == 0
        assert storage.load_meta().get("problem") is None


class TestCheck:
    def test_check_complete(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        text_keys = {"problem", "users", "goal", "tech_stack"}
        required = [
            "problem", "users", "goal", "scope",
            "non_goals", "pages", "tech_stack", "acceptance",
        ]
        for key in required:
            meta.set(key, "x" if key in text_keys else ["x"])
        storage.save_meta(meta)

        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0

    def test_check_incomplete(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        storage.save_meta(PrdMeta.new("web-app"))

        result = runner.invoke(app, ["check"])
        assert result.exit_code == 2

    def test_check_no_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 1


class TestShow:
    def test_show(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        storage.save_prd("# Test")
        result = runner.invoke(app, ["show"])
        assert result.exit_code == 0
        assert "# Test" in result.output

    def test_show_no_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["show"])
        assert result.exit_code == 1


class TestDrill:
    def test_drill_with_topic(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        storage.save_meta(meta)

        with patch("prd_first.drill.questionary") as mock_q:
            mock_q.text.return_value.ask.side_effect = ["ans1", "ans2", ""]
            result = runner.invoke(app, ["drill", "problem"])

        assert result.exit_code == 0
        assert "Drill 笔记已保存" in result.output
        assert storage.drill_file("problem").exists()

    def test_drill_no_topic_interactive(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        storage.save_meta(meta)

        with patch("prd_first.cli.questionary") as mock_cli_q, \
             patch("prd_first.drill.questionary") as mock_drill_q:
            mock_cli_q.select.return_value.ask.return_value = "问题陈述"
            mock_drill_q.text.return_value.ask.side_effect = ["ans1", "ans2", ""]
            result = runner.invoke(app, ["drill"])

        assert result.exit_code == 0
        assert "Drill 笔记已保存" in result.output
        assert storage.drill_file("problem").exists()

    def test_drill_no_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["drill", "problem"])
        assert result.exit_code == 1
        assert "请先运行: prd init" in result.output

    def test_drill_quit_without_saving(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        storage.save_meta(meta)

        with patch("prd_first.drill.questionary") as mock_q:
            mock_q.text.return_value.ask.return_value = "q"
            result = runner.invoke(app, ["drill", "problem"])

        assert result.exit_code == 0
        assert "没有记录任何内容" in result.output
        assert not storage.drill_file("problem").exists()
