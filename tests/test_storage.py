"""Tests for prd_first.storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from prd_first import storage
from prd_first.models import PrdMeta


@pytest.fixture
def tmp_prd_dir(tmp_path: Path):
    """Create a temporary directory with documents/prd/ structure."""
    prd = tmp_path / "documents" / "prd"
    prd.mkdir(parents=True)
    return tmp_path


class TestPrdDir:
    def test_default_when_no_prd_exists(self, monkeypatch, tmp_path: Path):
        monkeypatch.chdir(tmp_path)
        assert storage.prd_dir() == tmp_path / "documents" / "prd"

    def test_custom_root_when_no_prd_exists(self, tmp_path: Path):
        assert storage.prd_dir(tmp_path) == tmp_path / "documents" / "prd"

    def test_finds_prd_in_documents_prd(self, tmp_path: Path):
        prd = tmp_path / "documents" / "prd"
        prd.mkdir(parents=True)
        (prd / "PRD.md").write_text("# PRD", encoding="utf-8")
        assert storage.prd_dir(tmp_path) == prd

    def test_finds_prd_in_docs(self, tmp_path: Path):
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        (docs / "PRD.md").write_text("# PRD", encoding="utf-8")
        assert storage.prd_dir(tmp_path) == docs

    def test_finds_prd_in_root(self, tmp_path: Path):
        (tmp_path / "PRD.md").write_text("# PRD", encoding="utf-8")
        assert storage.prd_dir(tmp_path) == tmp_path


class TestFindPrdDir:
    def test_returns_none_when_no_prd(self, tmp_path: Path):
        assert storage.find_prd_dir(tmp_path) is None

    def test_finds_in_documents_prd(self, tmp_path: Path):
        prd = tmp_path / "documents" / "prd"
        prd.mkdir(parents=True)
        (prd / "PRD.md").write_text("# PRD", encoding="utf-8")
        assert storage.find_prd_dir(tmp_path) == prd

    def test_finds_in_docs(self, tmp_path: Path):
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        (docs / "PRD.md").write_text("# PRD", encoding="utf-8")
        assert storage.find_prd_dir(tmp_path) == docs

    def test_finds_in_root(self, tmp_path: Path):
        (tmp_path / "PRD.md").write_text("# PRD", encoding="utf-8")
        assert storage.find_prd_dir(tmp_path) == tmp_path

    def test_priority_documents_prd_over_docs(self, tmp_path: Path):
        # Create PRD in both locations
        documents_prd = tmp_path / "documents" / "prd"
        documents_prd.mkdir(parents=True)
        (documents_prd / "PRD.md").write_text("# PRD", encoding="utf-8")
        
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        (docs / "PRD.md").write_text("# PRD", encoding="utf-8")
        
        # Should find documents/prd first
        assert storage.find_prd_dir(tmp_path) == documents_prd


class TestFindMetaDir:
    def test_returns_none_when_no_meta(self, tmp_path: Path):
        assert storage.find_meta_dir(tmp_path) is None

    def test_finds_in_documents_prd(self, tmp_path: Path):
        prd = tmp_path / "documents" / "prd"
        prd.mkdir(parents=True)
        (prd / "meta.yaml").write_text("type: web-app", encoding="utf-8")
        assert storage.find_meta_dir(tmp_path) == prd

    def test_finds_in_docs(self, tmp_path: Path):
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        (docs / "meta.yaml").write_text("type: web-app", encoding="utf-8")
        assert storage.find_meta_dir(tmp_path) == docs


class TestEnsurePrdDir:
    def test_creates_dir(self, tmp_path: Path):
        storage.ensure_prd_dir(tmp_path)
        assert (tmp_path / "documents" / "prd").exists()

    def test_idempotent(self, tmp_path: Path):
        storage.ensure_prd_dir(tmp_path)
        storage.ensure_prd_dir(tmp_path)  # no error


class TestMetaOperations:
    def test_meta_not_exists(self, tmp_path: Path):
        assert storage.meta_exists(tmp_path) is False

    def test_meta_exists_after_save(self, tmp_path: Path):
        meta = PrdMeta.new("web-app")
        storage.save_meta(meta, tmp_path)
        assert storage.meta_exists(tmp_path) is True

    def test_load_meta_not_exists(self, tmp_path: Path):
        assert storage.load_meta(tmp_path) is None

    def test_load_meta_corrupt(self, tmp_path: Path):
        """Corrupt meta.yaml should return None, not crash."""
        prd = tmp_path / "documents" / "prd"
        prd.mkdir(parents=True)
        (prd / "meta.yaml").write_text("{{invalid yaml", encoding="utf-8")
        assert storage.load_meta(tmp_path) is None

    def test_load_meta_empty(self, tmp_path: Path):
        """Empty meta.yaml should return a default PrdMeta."""
        prd = tmp_path / "documents" / "prd"
        prd.mkdir(parents=True)
        (prd / "meta.yaml").write_text("", encoding="utf-8")
        meta = storage.load_meta(tmp_path)
        assert meta is not None
        assert meta.type == ""

    def test_save_load_roundtrip(self, tmp_path: Path):
        meta = PrdMeta.new("web-app")
        meta.set("problem", "test problem")
        storage.save_meta(meta, tmp_path)
        loaded = storage.load_meta(tmp_path)
        assert loaded is not None
        assert loaded.type == "web-app"
        assert loaded.answers["problem"] == "test problem"


class TestPrdOperations:
    def test_prd_not_exists(self, tmp_path: Path):
        assert storage.prd_exists(tmp_path) is False

    def test_save_read_prd(self, tmp_path: Path):
        storage.save_prd("# Hello", tmp_path)
        assert storage.prd_exists(tmp_path) is True
        content = storage.read_prd(tmp_path)
        assert content == "# Hello"

    def test_read_prd_not_exists(self, tmp_path: Path):
        assert storage.read_prd(tmp_path) is None


class TestRequireMeta:
    def test_require_meta_missing(self, tmp_path: Path):
        import typer
        with pytest.raises(typer.Exit):
            storage.require_meta(tmp_path)
