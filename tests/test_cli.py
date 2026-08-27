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


class TestInitEdge:
    def test_init_template_not_found(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init", "not-a-type"])
        assert result.exit_code == 1
        assert "模板不存在" in result.output

    def test_init_quit_midway_preserves_progress(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from prd_first.prompts import QuitPrompt

        def _raise(*args, **kwargs):
            raise QuitPrompt()

        with patch("prd_first.cli.ask_field", side_effect=_raise):
            result = runner.invoke(app, ["init", "web-app"])

        assert result.exit_code == 0
        assert "已保存当前进度" in result.output
        assert storage.meta_exists()

    def test_init_existing_meta_no_force_keeps_answers(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        meta.set("problem", "keep-me")
        storage.save_meta(meta)

        with patch("prd_first.cli.ask_field") as mock_ask:
            mock_ask.return_value = SKIP_SENTINEL
            result = runner.invoke(app, ["init", "web-app"])

        assert result.exit_code == 0
        assert storage.load_meta().get("problem") == "keep-me"

    def test_init_no_templates_dir(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("prd_first.cli.list_templates", return_value=[]):
            result = runner.invoke(app, ["init"])
        assert result.exit_code == 1
        assert "没有可用模板" in result.output


class TestCheckEdge:
    def test_check_meta_type_no_template(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("ghost-type")
        storage.save_meta(meta)

        result = runner.invoke(app, ["check"])
        assert result.exit_code == 1
        assert "无对应模板" in result.output


class TestDrillEdge:
    def test_drill_type_no_template(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("ghost-type")
        storage.save_meta(meta)

        result = runner.invoke(app, ["drill", "problem"])
        assert result.exit_code == 1
        assert "无对应模板" in result.output

    def test_drill_topic_select_cancel(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        storage.save_meta(meta)

        with patch("prd_first.cli.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = None
            result = runner.invoke(app, ["drill"])

        assert result.exit_code == 0


class TestInitForceConfirm:
    def test_init_corrupt_meta_confirm_cancel(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        storage.ensure_prd_dir()
        storage.meta_file().write_text("a: [unclosed", encoding="utf-8")

        with patch("prd_first.cli.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = False
            result = runner.invoke(app, ["init", "web-app"])

        assert result.exit_code == 0
        assert "已取消" in result.output

    def test_init_corrupt_meta_confirm_clear(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        storage.ensure_prd_dir()
        storage.meta_file().write_text("a: [unclosed", encoding="utf-8")

        with patch("prd_first.cli.ask_field") as mock_ask, \
             patch("prd_first.cli.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = True
            mock_ask.return_value = SKIP_SENTINEL
            result = runner.invoke(app, ["init", "web-app"])

        assert result.exit_code == 0
        assert storage.meta_exists()
        assert storage.load_meta().type == "web-app"


class TestPickTemplate:
    def test_init_interactive_pick(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from prd_first.models import load_template

        template = load_template("web-app")
        with patch("prd_first.cli.list_templates", return_value=[template]), \
             patch("prd_first.cli.ask_field") as mock_ask, \
             patch("prd_first.cli.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "Web 应用 (web-app)"
            mock_ask.return_value = SKIP_SENTINEL
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert storage.load_meta().type == "web-app"


class TestEdit:
    def test_edit_field_bumps_version(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        meta.set("problem", "old")
        storage.save_meta(meta)

        with patch("prd_first.cli.ask_field") as mock_ask:
            mock_ask.return_value = "new value"
            result = runner.invoke(app, ["edit", "problem"])

        assert result.exit_code == 0
        assert "已更新" in result.output
        saved = storage.load_meta()
        assert saved.get("problem") == "new value"
        assert saved.version == 2
        assert len(saved.changelog) == 1
        assert saved.changelog[0]["field"] == "problem"

    def test_edit_no_change_no_bump(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        meta.set("problem", "same")
        storage.save_meta(meta)

        with patch("prd_first.cli.ask_field") as mock_ask:
            mock_ask.return_value = "same"
            result = runner.invoke(app, ["edit", "problem"])

        assert result.exit_code == 0
        assert "未变化" in result.output
        assert storage.load_meta().version == 1

    def test_edit_unknown_field(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        storage.save_meta(PrdMeta.new("web-app"))

        result = runner.invoke(app, ["edit", "not-a-field"])
        assert result.exit_code == 1
        assert "不存在" in result.output

    def test_edit_no_prd(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["edit", "problem"])
        assert result.exit_code == 1

    def test_edit_quit_cancels(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        meta.set("problem", "old")
        storage.save_meta(meta)

        from prd_first.prompts import QuitPrompt

        def _raise(*args, **kwargs):
            raise QuitPrompt()

        with patch("prd_first.cli.ask_field", side_effect=_raise):
            result = runner.invoke(app, ["edit", "problem"])

        assert result.exit_code == 0
        assert "已取消" in result.output
        assert storage.load_meta().version == 1
class TestNew:
    def test_new_starts_fresh(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = PrdMeta.new("web-app")
        meta.set("problem", "old")
        storage.save_meta(meta)

        with (
            patch("prd_first.cli.questionary.confirm") as mock_confirm,
            patch("prd_first.cli.ask_field") as mock_ask,
        ):
            mock_confirm.return_value.ask.return_value = True
            mock_ask.return_value = SKIP_SENTINEL
            result = runner.invoke(app, ["new", "cli-tool"])

        assert result.exit_code == 0
        loaded = storage.load_meta()
        assert loaded is not None
        assert loaded.type == "cli-tool"
        assert loaded.get("problem") is None

    def test_new_cancel(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        storage.save_meta(PrdMeta.new("web-app"))

        with patch("prd_first.cli.questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = False
            result = runner.invoke(app, ["new", "web-app"])

        assert result.exit_code == 0
        assert "已取消" in result.output


class TestTemplateList:
    def test_template_list(self):
        result = runner.invoke(app, ["template", "list"])
        assert result.exit_code == 0
        assert "web-app" in result.output
        assert "backend-data" in result.output
        assert "必填" in result.output
