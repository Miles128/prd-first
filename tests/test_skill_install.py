"""Tests for skill installation helpers and CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from prd_first.cli import app
from prd_first.skill_install import (
    CODEX_BEGIN,
    CODEX_END,
    install_claude,
    install_codex,
    install_cursor,
    load_skill_text,
)

runner = CliRunner()


def test_load_skill_text():
    text = load_skill_text()
    assert "prd-first" in text
    assert "documents/PRD.md" in text


def test_install_claude_project(tmp_path: Path):
    path = install_claude(tmp_path)
    assert path == tmp_path / ".claude" / "skills" / "prd-first" / "SKILL.md"
    assert path.exists()
    assert "编码前先写 PRD" in path.read_text(encoding="utf-8")


def test_install_claude_global(tmp_path: Path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    path = install_claude(tmp_path, user_global=True)
    assert path == home / ".claude" / "skills" / "prd-first" / "SKILL.md"
    assert path.exists()


def test_install_cursor(tmp_path: Path):
    path = install_cursor(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert path.name == "prd-first.mdc"
    assert "alwaysApply: true" in text
    assert "编码前先写 PRD" in text
    # original skill yaml name frontmatter should not remain as dual ---
    assert text.count("name: prd-first") == 0


def test_install_codex_create_and_update(tmp_path: Path):
    path = install_codex(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert CODEX_BEGIN in text and CODEX_END in text

    # second install replaces block, keeps surrounding content
    path.write_text("HEADER\n\n" + text + "\nFOOTER\n", encoding="utf-8")
    install_codex(tmp_path)
    updated = path.read_text(encoding="utf-8")
    assert updated.startswith("HEADER")
    assert "FOOTER" in updated
    assert updated.count(CODEX_BEGIN) == 1


def test_cli_skill_install_all(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["skill", "install", "all"])
    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "skills" / "prd-first" / "SKILL.md").exists()
    assert (tmp_path / ".cursor" / "rules" / "prd-first.mdc").exists()
    assert (tmp_path / "AGENTS.md").exists()


def test_cli_skill_install_bad_target(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["skill", "install", "nope"])
    assert result.exit_code == 1
