"""交互式问答引擎。"""

from __future__ import annotations

from typing import Any, cast

import questionary

from .const import QUIT_TOKEN, SKIP_SENTINEL, SKIP_TOKEN
from .models import FieldDef, PrdMeta


class QuitPrompt(Exception):
    """用户中途选择退出。"""


def _is_control_token(text: str | None) -> str | None:
    """识别控制 token。"""
    if text is None:
        return None
    t = text.strip().lower()
    if t == SKIP_TOKEN:
        return "skip"
    if t == QUIT_TOKEN:
        return "quit"
    return None


def _ask_with_skip(prompt: str, default: str = "") -> str:
    """单行输入,支持 s/q 控制。"""
    answer = questionary.text(prompt, default=default).ask()
    if answer is None:
        raise QuitPrompt()
    text = cast(str, answer)
    ctrl = _is_control_token(text)
    if ctrl == "skip":
        return SKIP_SENTINEL
    if ctrl == "quit":
        raise QuitPrompt()
    return text.strip()


def ask_text(field: FieldDef, current: Any) -> str:
    """单行文本输入。"""
    return _ask_with_skip(field.prompt)


def ask_single(field: FieldDef, current: Any) -> str:
    """单选。"""
    choices = list(field.choices) + ["⏭️ 跳过", "🚪 退出"]
    answer = questionary.select(field.prompt, choices=choices).ask()
    if answer is None:
        raise QuitPrompt()
    if answer == "⏭️ 跳过":
        return SKIP_SENTINEL
    if answer == "🚪 退出":
        raise QuitPrompt()
    return cast(str, answer)


def ask_multi(field: FieldDef, current: Any) -> list[str]:
    """多选。"""
    choices = list(field.choices) + ["⏭️ 跳过", "🚪 退出"]
    answer = questionary.checkbox(field.prompt, choices=choices).ask()
    if answer is None:
        raise QuitPrompt()
    if "🚪 退出" in answer:
        raise QuitPrompt()
    if "⏭️ 跳过" in answer or not answer:
        return SKIP_SENTINEL  # type: ignore[return-value]
    return [a for a in answer if a in field.choices]


def ask_list(field: FieldDef, current: Any) -> list[str]:
    """列表:逐项输入,空行结束。"""
    items: list[str] = []
    while True:
        item = _ask_with_skip(f"第 {len(items) + 1} 项(空行结束):")
        if item == SKIP_SENTINEL:
            return SKIP_SENTINEL  # type: ignore[return-value]
        if item == "":
            break
        items.append(item)
    return items


def ask_field(field: FieldDef, meta: PrdMeta) -> Any:
    """对单个字段提问。"""
    current = meta.get(field.key)
    print()
    required_tag = "*必填" if field.required else "可选"
    print(f"[{required_tag}] {field.label}")
    if field.why:
        print(f"  {field.why}")
    print("  (输入 s 跳过,q 退出保存)")

    ftype = field.type
    if ftype == "single":
        return ask_single(field, current)
    if ftype == "multi":
        return ask_multi(field, current)
    if ftype == "list":
        return ask_list(field, current)
    return ask_text(field, current)


def apply_answer(meta: PrdMeta, field: FieldDef, result: Any) -> None:
    """把问答结果写入 meta。"""
    if result == SKIP_SENTINEL:
        return
    if isinstance(result, str) and result.strip() == "":
        return
    if isinstance(result, list) and len(result) == 0:
        return
    meta.set(field.key, result)
