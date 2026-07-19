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
    """单行文本输入。已有值时作为默认预填。"""
    default = str(current) if isinstance(current, str) and current.strip() else ""
    return _ask_with_skip(field.prompt, default=default)


def ask_single(field: FieldDef, current: Any) -> str:
    """单选。已有值时在提示中标明。"""
    prompt = field.prompt
    if isinstance(current, str) and current.strip():
        prompt = f"{field.prompt} (当前: {current})"
    choices = list(field.choices) + ["⏭️ 跳过", "🚪 退出"]
    answer = questionary.select(prompt, choices=choices).ask()
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


def _collect_list_items(start: list[str] | None = None) -> list[str] | Any:
    """逐项输入列表,空行结束。返回 SKIP_SENTINEL 表示跳过。"""
    items: list[str] = list(start or [])
    while True:
        item = _ask_with_skip(f"第 {len(items) + 1} 项(空行结束):")
        if item == SKIP_SENTINEL:
            return SKIP_SENTINEL
        if item == "":
            break
        items.append(item)
    return items


def ask_list(field: FieldDef, current: Any) -> list[str]:
    """列表:逐项输入,空行结束。已有值时可替换/追加/保持。"""
    existing = list(current) if isinstance(current, list) and current else []
    if existing:
        print("当前列表:")
        for i, item in enumerate(existing, 1):
            print(f"  {i}. {item}")
        mode = questionary.select(
            "如何编辑这份列表?",
            choices=["替换全部", "追加", "保持不变"],
        ).ask()
        if mode is None:
            raise QuitPrompt()
        if mode == "保持不变":
            return existing
        if mode == "追加":
            return _collect_list_items(existing)  # type: ignore[return-value]
        # 替换全部
        return _collect_list_items()  # type: ignore[return-value]

    return _collect_list_items()  # type: ignore[return-value]


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
