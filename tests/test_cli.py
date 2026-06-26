"""Tests for prd_first.cli."""

from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from prd_first.cli import app
from prd_first.models import PrdMeta
from prd_first import storage

runner = CliRunner()


class TestTemplateList:
    def test_template_list(self):
        result = runner.invoke(app, ["template", "list"])
        assert result.exit_code == 0
        assert "web-app" in result.output
        assert "cli-tool" in result.output
        assert "ai-agent" in result.output
        assert "backend-data" in result.output


class TestCheck:
    def test_check_no_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 1
        assert "没有 PRD" in result.output

    def test_check_with_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        meta.set_answer("problem", "test problem")
        meta.set_answer("users", "test users")
        meta.set_answer("goal", "test goal")
        meta.set_answer("scope", ["feature1"])
        meta.set_answer("non_goals", ["no auth"])
        meta.set_answer("core_scenarios", ["scenario1"])
        meta.set_answer("pages", ["/home"])
        meta.set_answer("tech_stack", "React + Node")
        meta.set_answer("acceptance", ["it works"])
        storage.save_meta(meta)

        result = runner.invoke(app, ["check"])
        assert "PRD 完整度" in result.output


class TestShow:
    def test_show_no_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["show"])
        assert result.exit_code == 1
        assert "没有 PRD" in result.output

    def test_show_with_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        storage.save_prd("# Test PRD\nHello world")
        result = runner.invoke(app, ["show"])
        assert result.exit_code == 0
        assert "Test PRD" in result.output


class TestEdit:
    def test_edit_no_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["edit", "problem"])
        assert result.exit_code == 1

    def test_edit_nonexistent_field(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        storage.save_meta(meta)
        result = runner.invoke(app, ["edit", "nonexistent"])
        assert result.exit_code == 1
        assert "不存在" in result.output


class TestInit:
    def test_init_help(self):
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "交互式初始化" in result.output

    def test_new_help(self):
        result = runner.invoke(app, ["new", "--help"])
        assert result.exit_code == 0
