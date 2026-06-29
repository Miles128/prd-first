"""数据模型：模板字段定义、模板定义、PRD 元数据。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .const import TEMPLATES_DIR


def _is_filled(value: Any) -> bool:
    """判断值是否有效。"""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, tuple)):
        return len(value) > 0
    return True


def _render(value: Any) -> str:
    """把值渲染成 markdown 文本。"""
    if not _is_filled(value):
        return "_(待补充)_"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (list, tuple)):
        return "\n".join(f"- {item}" for item in value)
    return str(value)


@dataclass
class FieldDef:
    """模板中单个字段的定义。"""

    key: str
    label: str
    required: bool = False
    type: str = "text"  # text | single | multi | list
    prompt: str = ""
    why: str = ""
    choices: list[str] = field(default_factory=list)
    drill_questions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FieldDef:
        return cls(
            key=data["key"],
            label=data.get("label", data["key"]),
            required=bool(data.get("required", False)),
            type=data.get("type", "text"),
            prompt=data.get("prompt", ""),
            why=data.get("why", ""),
            choices=list(data.get("choices", []) or []),
            drill_questions=list(data.get("drill_questions", []) or []),
        )


@dataclass
class TemplateDef:
    """一整套模板定义。"""

    type: str
    name: str
    description: str = ""
    fields: list[FieldDef] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateDef:
        return cls(
            type=data["type"],
            name=data.get("name", data["type"]),
            description=data.get("description", ""),
            fields=[FieldDef.from_dict(f) for f in data.get("fields", [])],
        )

    def find(self, key: str) -> FieldDef | None:
        for f in self.fields:
            if f.key == key:
                return f
        return None


@dataclass
class PrdMeta:
    """PRD 元数据（对应 documents/prd/meta.yaml）。"""

    type: str
    answers: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        return self.answers.get(key)

    def set(self, key: str, value: Any) -> None:
        self.answers[key] = value

    @classmethod
    def new(cls, template_type: str) -> PrdMeta:
        return cls(type=template_type)

    def to_yaml(self) -> str:
        text: str = yaml.safe_dump(
            {"type": self.type, "answers": self.answers},
            allow_unicode=True,
            sort_keys=False,
        )
        return text

    @classmethod
    def from_yaml(cls, text: str) -> PrdMeta:
        data = yaml.safe_load(text) or {}
        return cls(
            type=data.get("type", ""),
            answers=data.get("answers", {}) or {},
        )


def load_template(template_type: str, templates_dir: Path | None = None) -> TemplateDef:
    """加载指定类型的模板定义。"""
    d = templates_dir or TEMPLATES_DIR
    path = d / f"{template_type}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"模板不存在: {template_type} (查找路径 {path})")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return TemplateDef.from_dict(data)


def list_templates(templates_dir: Path | None = None) -> list[TemplateDef]:
    """列出所有可用模板。"""
    d = templates_dir or TEMPLATES_DIR
    result: list[TemplateDef] = []
    if not d.exists():
        return result
    for yaml_path in sorted(d.glob("*.yaml")):
        if yaml_path.stem.startswith("_"):
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            result.append(TemplateDef.from_dict(data))
        except (yaml.YAMLError, KeyError, TypeError, FileNotFoundError) as exc:
            logging.getLogger("prd_first").warning("忽略损坏的模板 %s: %s", yaml_path, exc)
            continue
    return result
