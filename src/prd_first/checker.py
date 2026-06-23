"""PRD 完整度校验。

计算必填字段完成度、列出缺失项,给出整体评分。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import PrdMeta, TemplateDef


@dataclass
class FieldStatus:
    key: str
    label: str
    required: bool
    filled: bool
    status: str  # pending | answered | skipped


@dataclass
class CheckResult:
    template_type: str
    total: int = 0
    filled: int = 0
    required_total: int = 0
    required_filled: int = 0
    missing_required: list[FieldStatus] = field(default_factory=list)
    missing_optional: list[FieldStatus] = field(default_factory=list)
    all_fields: list[FieldStatus] = field(default_factory=list)

    @property
    def completeness_pct(self) -> int:
        """整体完成度百分比(按所有字段算)。"""
        if self.total == 0:
            return 0
        return round(self.filled * 100 / self.total)

    @property
    def required_pct(self) -> int:
        """必填完成度百分比。"""
        if self.required_total == 0:
            return 100
        return round(self.required_filled * 100 / self.required_total)

    @property
    def is_complete(self) -> bool:
        """必填全部填完即视为完整。无必填字段时也视为完整。"""
        return self.required_filled == self.required_total


def check(template: TemplateDef, meta: PrdMeta) -> CheckResult:
    """对一份 PRD 做完整度检查。"""
    result = CheckResult(template_type=template.type)
    for f in template.fields:
        answer = meta.get_answer(f.key)
        filled = answer.is_filled
        status = FieldStatus(
            key=f.key,
            label=f.label,
            required=f.required,
            filled=filled,
            status=answer.status,
        )
        result.all_fields.append(status)
        result.total += 1
        if filled:
            result.filled += 1
        if f.required:
            result.required_total += 1
            if filled:
                result.required_filled += 1
            else:
                result.missing_required.append(status)
        elif not filled:
            result.missing_optional.append(status)
    return result
