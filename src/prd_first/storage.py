"""PRD 文件读写:统一管理 documents/prd/ 目录的持久化。"""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

from .const import (
    META_FILE_NAME,
    PRD_DIR_NAME,
    PRD_FILE_NAME,
)
from .models import PrdMeta


def prd_dir(root: Path | None = None) -> Path:
    """返回 documents/prd 目录路径。root 默认为当前工作目录。"""
    base = root or Path.cwd()
    return base / PRD_DIR_NAME


def prd_file(root: Path | None = None) -> Path:
    return prd_dir(root) / PRD_FILE_NAME


def meta_file(root: Path | None = None) -> Path:
    return prd_dir(root) / META_FILE_NAME


def ensure_prd_dir(root: Path | None = None) -> Path:
    """创建 documents/prd 目录(若不存在),返回路径。"""
    d = prd_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    return d


def meta_exists(root: Path | None = None) -> bool:
    return meta_file(root).exists()


def prd_exists(root: Path | None = None) -> bool:
    return prd_file(root).exists()


def load_meta(root: Path | None = None) -> PrdMeta | None:
    """读取 meta.yaml。不存在或损坏返回 None。"""
    p = meta_file(root)
    if not p.exists():
        return None
    try:
        text = p.read_text(encoding="utf-8")
        return PrdMeta.from_yaml(text)
    except (yaml.YAMLError, KeyError, ValueError):
        return None


def save_meta(meta: PrdMeta, root: Path | None = None) -> Path:
    """写入 meta.yaml。"""
    ensure_prd_dir(root)
    p = meta_file(root)
    p.write_text(meta.to_yaml(), encoding="utf-8")
    return p


def save_prd(content: str, root: Path | None = None) -> Path:
    """写入 PRD.md。"""
    ensure_prd_dir(root)
    p = prd_file(root)
    p.write_text(content, encoding="utf-8")
    return p


def read_prd(root: Path | None = None) -> str | None:
    """读取 PRD.md 内容。不存在返回 None。"""
    p = prd_file(root)
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def require_meta(root: Path | None = None) -> PrdMeta:
    """必须有 meta,否则报错退出。"""
    meta = load_meta(root)
    if meta is None:
        typer.secho(
            "❌ 当前目录没有 PRD。请先运行: prd init",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    return meta
