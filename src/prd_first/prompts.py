"""交互式问答引擎。

基于 questionary,逐字段提问。支持:
- text (多行)/ single / multi / confirm / list
- 输入 's' 跳过,'q' 退出保存进度
- 已有答案作为默认值,支持断点续答
"""

from __future__ import annotations

from typing import Any, Union

import questionary

from .const import QUIT_TOKEN, SKIP_SENTINEL, SKIP_TOKEN
from .models import Answer, FieldDef, PrdMeta

# 共享 Console 实例
_console = None


def _get_console():
    global _console
    if _console is None:
        from rich.console import Console
        _console = Console()
    return _console


class QuitPrompt(Exception):
    """用户中途选择退出。"""


def _show_field_header(field: FieldDef) -> None:
    """在提问前打印字段头:label、必填标记、为什么。"""
    console = _get_console()
    required_tag = "[red]*必填[/red]" if field.required else "[dim]可选[/dim]"
    console.print()
    console.rule(f"[bold]{field.label}[/bold] {required_tag}")
    if field.why:
        console.print(f"[dim]💡 {field.why}[/dim]")


def _show_skip_quit_hint(field_type: str = "text") -> None:
    """显示跳过/退出提示。confirm 类型不显示跳过提示。"""
    if field_type == "confirm":
        return
    console = _get_console()
    console.print("[dim]  (输入 s 跳过本字段,q 保存并退出)[/dim]")


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


def ask_text(field: FieldDef, current: Answer) -> str:
    """多行文本输入。questionary.text 是单行,我们用多次提示模拟多行。

    简化:用单次 questionary.text,但接受换行(questionary 支持)。
    实测 questionary.text 不支持多行回车(回车即提交),
    所以改为:第一次输入后问'还要补充吗'。
    """
    console = _get_console()
    # 拿到当前已有值作为默认
    default_text = current.value if isinstance(current.value, str) else ""
    parts: list[str] = []
    if default_text:
        parts.append(default_text)
        console.print(f"[dim]当前内容:[/dim]\n{default_text}")
        action = questionary.select(
            "如何处理已有内容?",
            choices=["保留并追加", "覆盖重写", "跳过本字段", "退出保存"],
            default="保留并追加",
        ).ask()
        if action == "跳过本字段":
            return SKIP_SENTINEL
        if action == "退出保存":
            raise QuitPrompt()
        if action == "覆盖重写":
            parts = []

    placeholder = field.placeholder or ""
    first = questionary.text(
        field.prompt,
        default="",
    ).ask()
    if first is None:
        raise QuitPrompt()
    ctrl = _is_control_token(first)
    if ctrl == "skip":
        return SKIP_SENTINEL
    if ctrl == "quit":
        raise QuitPrompt()
    if first.strip():
        parts.append(first.strip())

    # 多行:继续问
    while True:
        more = questionary.text(
            "继续补充(直接回车结束):",
            default="",
        ).ask()
        if more is None:
            raise QuitPrompt()
        ctrl = _is_control_token(more)
        if ctrl == "quit":
            raise QuitPrompt()
        if more.strip() == "":
            break
        parts.append(more.strip())

    return "\n".join(parts)


def ask_single(field: FieldDef, current: Answer) -> str:
    """单选。"""
    default = current.value if isinstance(current.value, str) and current.value in field.choices else None
    choices = list(field.choices)
    # 提供跳过/退出选项
    choices_with_ctrl = list(field.choices) + ["⏭️  跳过本字段", "🚪 退出保存"]
    answer = questionary.select(
        field.prompt,
        choices=choices_with_ctrl,
        default=default if default is not None else choices_with_ctrl[0],
    ).ask()
    if answer is None:
        raise QuitPrompt()
    if answer == "⏭️  跳过本字段":
        return SKIP_SENTINEL
    if answer == "🚪 退出保存":
        raise QuitPrompt()
    return answer


def ask_multi(field: FieldDef, current: Answer) -> list[str]:
    """多选。"""
    default = current.value if isinstance(current.value, (list, tuple)) else []
    choices = list(field.choices)
    answer = questionary.checkbox(
        field.prompt,
        choices=choices,
        default=[c for c in default if c in choices],
    ).ask()
    if answer is None:
        raise QuitPrompt()
    return answer


def ask_confirm(field: FieldDef, current: Answer) -> bool:
    """是/否确认。"""
    default = bool(current.value) if isinstance(current.value, bool) else True
    answer = questionary.confirm(field.prompt, default=default).ask()
    if answer is None:
        raise QuitPrompt()
    return answer


def ask_list(field: FieldDef, current: Answer) -> list[str]:
    """列表:逐项输入,空行结束。"""
    console = _get_console()
    items: list[str] = []
    existing = current.value if isinstance(current.value, (list, tuple)) else []
    if existing:
        console.print(f"[dim]当前已有 {len(existing)} 项:[/dim]")
        for i, it in enumerate(existing, 1):
            console.print(f"[dim]  {i}. {it}[/dim]")
        action = questionary.select(
            "如何处理?",
            choices=["追加到现有", "全部覆盖重写", "跳过本字段", "退出保存"],
            default="追加到现有",
        ).ask()
        if action == "跳过本字段":
            return [SKIP_SENTINEL]
        if action == "退出保存":
            raise QuitPrompt()
        if action == "追加到现有":
            items = list(existing)

    idx = len(items) + 1
    while True:
        item = questionary.text(
            f"第 {idx} 项(空行结束):",
            default="",
        ).ask()
        if item is None:
            raise QuitPrompt()
        ctrl = _is_control_token(item)
        if ctrl == "quit":
            raise QuitPrompt()
        if item.strip() == "":
            break
        items.append(item.strip())
        idx += 1

    return items


def ask_field(
    field: FieldDef, meta: PrdMeta
) -> Union[str, list[str], bool, None]:
    """对单个字段提问,返回新值。

    返回:
      - str / list[str] / bool: 已作答
      - SKIP_SENTINEL: 用户选择跳过
      - None: 用户未输入(空)
    """
    current = meta.get_answer(field.key)
    _show_field_header(field)
    _show_skip_quit_hint(field.type)

    ftype = field.type
    if ftype == "text":
        return ask_text(field, current)
    if ftype == "single":
        return ask_single(field, current)
    if ftype == "multi":
        return ask_multi(field, current)
    if ftype == "confirm":
        return ask_confirm(field, current)
    if ftype == "list":
        return ask_list(field, current)
    # 默认按 text 处理
    return ask_text(field, current)


def apply_answer(meta: PrdMeta, field: FieldDef, result: Any) -> None:
    """把问答结果写入 meta。处理 SKIP/空值。"""
    # list 类型跳过返回 [SKIP_SENTINEL]
    if isinstance(result, list) and result == [SKIP_SENTINEL]:
        meta.set_answer(field.key, None, status="skipped")
        return
    if result == SKIP_SENTINEL:
        meta.set_answer(field.key, None, status="skipped")
        return
    # 空文本
    if isinstance(result, str) and result.strip() == "":
        meta.set_answer(field.key, None, status="skipped")
        return
    # 空列表
    if isinstance(result, list) and len(result) == 0:
        meta.set_answer(field.key, None, status="skipped")
        return
    meta.set_answer(field.key, result, status="answered")
