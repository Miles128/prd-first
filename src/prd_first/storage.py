"""PRD 文件读写:统一管理 documents/prd/ 目录的持久化。

支持多个可能的 PRD 位置,按优先级搜索:
1. documents/prd/PRD.md (默认)
2. docs/PRD.md
3. PRD.md (项目根目录)
"""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

from .const import (
    DRILL_FILE_PREFIX,
    META_FILE_NAME,
    PRD_DIR_NAME,
    PRD_FILE_NAME,
)
from .models import PrdMeta

# PRD 可能存在的位置（按优先级排序）
PRD_SEARCH_PATHS = [
    "documents/prd",  # 默认位置
    "docs",           # 常见文档目录
    ".",              # 项目根目录
]


def find_prd_dir(root: Path | None = None) -> Path | None:
    """搜索 PRD 文件可能存在的目录，返回第一个找到的位置。"""
    base = root or Path.cwd()

    for dir_name in PRD_SEARCH_PATHS:
        candidate = base / dir_name
        prd_path = candidate / PRD_FILE_NAME
        if prd_path.exists():
            return candidate

    return None


def find_meta_dir(root: Path | None = None) -> Path | None:
    """搜索 meta.yaml 文件可能存在的目录，返回第一个找到的位置。"""
    base = root or Path.cwd()

    for dir_name in PRD_SEARCH_PATHS:
        candidate = base / dir_name
        meta_path = candidate / META_FILE_NAME
        if meta_path.exists():
            return candidate

    return None


def prd_dir(root: Path | None = None) -> Path:
    """返回 PRD 目录路径。

    如果已存在 PRD 文件，返回其所在目录；
    否则返回默认的 documents/prd/ 目录。
    """
    base = root or Path.cwd()

    # 先搜索已存在的 PRD
    existing = find_prd_dir(root)
    if existing is not None:
        return existing

    # 不存在则使用默认位置
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
    """检查 meta.yaml 是否存在（搜索多个位置）。"""
    return find_meta_dir(root) is not None


def prd_exists(root: Path | None = None) -> bool:
    """检查 PRD.md 是否存在（搜索多个位置）。"""
    return find_prd_dir(root) is not None


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


def drill_file(topic: str, root: Path | None = None) -> Path:
    """返回 drill 追问笔记文件路径。topic 会被规范化。"""
    safe_topic = topic.lower().replace(" ", "-")
    return prd_dir(root) / f"{DRILL_FILE_PREFIX}{safe_topic}.md"


def save_drill(topic: str, content: str, root: Path | None = None) -> Path:
    """写入 drill-<topic>.md。"""
    ensure_prd_dir(root)
    p = drill_file(topic, root)
    p.write_text(content, encoding="utf-8")
    return p
