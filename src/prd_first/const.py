"""路径与版本常量。"""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "PRD_DIR_NAME",
    "PRD_FILE_NAME",
    "META_FILE_NAME",
    "SKIP_TOKEN",
    "QUIT_TOKEN",
    "SKIP_SENTINEL",
    "PENDING_PLACEHOLDER",
    "TEMPLATES_DIR",
    "PACKAGE_ROOT",
]

# PRD 文件布局(在项目根目录下的 .prd/)
PRD_DIR_NAME = ".prd"
PRD_FILE_NAME = "PRD.md"
META_FILE_NAME = "meta.yaml"

# 问答控制 token（用户输入）
SKIP_TOKEN = "s"
QUIT_TOKEN = "q"

# 内部哨兵值（函数间传递跳过信号）
SKIP_SENTINEL = "__PRD_SKIP__"

# 未填写字段的占位符
PENDING_PLACEHOLDER = "_(待补充)_"

# 内置模板目录
PACKAGE_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_ROOT / "assets" / "templates"
