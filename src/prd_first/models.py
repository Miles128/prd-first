"""数据模型:模板字段定义、模板定义、PRD 元数据。

用 dataclass 而非 pydantic,避免新增依赖。所有模型可从 YAML 构建。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, cast

import yaml

from .const import PENDING_PLACEHOLDER


@dataclass
class FieldDef:
    """模板中单个字段的定义。"""

    key: str  # 字段标识,如 "problem"
    label: str  # 中文展示名,如 "问题陈述"
    required: bool = False
    type: str = "text"  # text | single | multi | confirm | list
    prompt: str = ""  # 问用户的问题
    why: str = ""  # 为什么这个问题重要(引导提示)
    placeholder: str = ""  # 输入示例
    choices: list[str] = field(default_factory=list)  # single/multi 的候选
    section: str = ""  # 所属章节,用于渲染分组

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FieldDef":
        return cls(
            key=data["key"],
            label=data.get("label", data["key"]),
            required=bool(data.get("required", False)),
            type=data.get("type", "text"),
            prompt=data.get("prompt", ""),
            why=data.get("why", ""),
            placeholder=data.get("placeholder", ""),
            choices=list(data.get("choices", []) or []),
            section=data.get("section", ""),
        )


@dataclass
class TemplateDef:
    """一整套模板定义(对应 assets/templates/<type>.yaml)。"""

    type: str  # 模板标识,如 "web-app"
    name: str  # 中文展示名
    description: str = ""
    fields: list[FieldDef] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateDef":
        return cls(
            type=data["type"],
            name=data.get("name", data["type"]),
            description=data.get("description", ""),
            fields=[FieldDef.from_dict(f) for f in data.get("fields", [])],
        )

    @property
    def required_fields(self) -> list[FieldDef]:
        return [f for f in self.fields if f.required]

    def find(self, key: str) -> Optional[FieldDef]:
        for f in self.fields:
            if f.key == key:
                return f
        return None


@dataclass
class Answer:
    """单个字段的当前作答。"""

    value: Any  # str / list[str] / bool / None
    status: str = "pending"  # pending | answered | skipped

    @property
    def is_filled(self) -> bool:
        """是否已填入有效内容(skipped 不算)。"""
        if self.status != "answered":
            return False
        if self.value is None:
            return False
        if isinstance(self.value, str):
            return self.value.strip() != ""
        if isinstance(self.value, (list, tuple)):
            return len(self.value) > 0
        return True

    def render(self) -> str:
        """渲染成 markdown 文本。"""
        if not self.is_filled:
            return PENDING_PLACEHOLDER
        if isinstance(self.value, bool):
            return "是" if self.value else "否"
        if isinstance(self.value, (list, tuple)):
            return "\n".join(f"- {item}" for item in self.value)
        return str(self.value)


@dataclass
class PrdMeta:
    """PRD 元数据(对应 .prd/meta.yaml)。

    记录项目类型、各字段作答状态、创建/更新时间。
    answers 的 key 是字段 key,value 是原始值;status 单独存在 statuses 里。
    """

    type: str
    answers: dict[str, Any] = field(default_factory=dict)
    statuses: dict[str, str] = field(default_factory=dict)  # key -> pending/answered/skipped
    created_at: str = ""
    updated_at: str = ""

    def get_answer(self, key: str) -> Answer:
        return Answer(
            value=self.answers.get(key),
            status=self.statuses.get(key, "pending"),
        )

    def set_answer(self, key: str, value: Any, status: str = "answered") -> None:
        self.answers[key] = value
        self.statuses[key] = status
        self.updated_at = datetime.now().isoformat(timespec="seconds")

    @classmethod
    def new(cls, template_type: str) -> "PrdMeta":
        now = datetime.now().isoformat(timespec="seconds")
        return cls(type=template_type, created_at=now, updated_at=now)

    def to_yaml(self) -> str:
        data = {
            "type": self.type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "answers": self.answers,
            "statuses": self.statuses,
        }
        return cast(str, yaml.safe_dump(data, allow_unicode=True, sort_keys=False))

    @classmethod
    def from_yaml(cls, text: str) -> "PrdMeta":
        data = yaml.safe_load(text) or {}
        return cls(
            type=data.get("type", ""),
            answers=data.get("answers", {}) or {},
            statuses=data.get("statuses", {}) or {},
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


def load_template(template_type: str, templates_dir: Optional[Path] = None) -> TemplateDef:
    """从模板目录加载指定类型的模板定义。"""
    from .const import TEMPLATES_DIR

    d = templates_dir or TEMPLATES_DIR
    path = d / f"{template_type}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"模板不存在: {template_type} (查找路径 {path})")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return TemplateDef.from_dict(data)


def list_templates(templates_dir: Optional[Path] = None) -> list[TemplateDef]:
    """列出所有可用模板。"""
    from .const import TEMPLATES_DIR

    d = templates_dir or TEMPLATES_DIR
    result: list[TemplateDef] = []
    if not d.exists():
        return result
    for yaml_path in sorted(d.glob("*.yaml")):
        # 跳过下划线开头的(如 _generic 不直接出现在 init 列表)
        if yaml_path.stem.startswith("_"):
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            result.append(TemplateDef.from_dict(data))
        except (yaml.YAMLError, KeyError, TypeError, FileNotFoundError) as exc:
            logging.getLogger("prd_first").warning("忽略损坏的模板 %s: %s", yaml_path, exc)
            continue
    return result
