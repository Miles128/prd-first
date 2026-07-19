"""prd-first CLI 入口。

命令:
  prd init [type]              交互式初始化(选类型 + 逐字段问答)
  prd new <type>               清空已有答案,按类型重新开始
  prd edit [field]             编辑字段;省略则列出可编辑字段
  prd drill <topic>            对某个分支进行 drill-down 风格书面化追问
  prd check                    校验完整度
  prd show [--section KEY]     打印 PRD 或单个字段
  prd template list            列出所有模板
  prd skill install [target]   安装 Skill 到 Claude/Cursor/Codex
"""

from __future__ import annotations

import questionary
import typer

from . import __version__, storage
from . import drill as drill_module
from .models import FieldDef, PrdMeta, TemplateDef, _is_filled, list_templates, load_template
from .prompts import QuitPrompt, apply_answer, ask_field
from .render import render_prd, render_section
from .skill_install import install_claude, install_codex, install_cursor

app = typer.Typer(
    name="prd",
    help="Vibecoding 前先写 PRD:交互式问答生成结构化 PRD。",
    no_args_is_help=True,
    add_completion=False,
)

template_app = typer.Typer(help="模板相关命令。")
app.add_typer(template_app, name="template")

skill_app = typer.Typer(help="AI 助手 Skill 安装。")
app.add_typer(skill_app, name="skill")


def _version_callback(value: bool) -> None:
    if value:
        print(__version__)
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="显示版本号。",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """prd-first CLI。"""


def _pick_template() -> TemplateDef:
    """交互式选择项目类型。"""
    templates = list_templates()
    if not templates:
        typer.secho("❌ 没有可用模板。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    choices_map = {f"{t.name} ({t.type})": t for t in templates}
    selected = questionary.select("这是什么类型的项目?", choices=list(choices_map)).ask()
    if selected is None:
        raise typer.Exit(code=0)
    return choices_map[selected]


def _resolve_template(template_type: str | None) -> TemplateDef:
    """解析模板:type 给了直接加载,否则交互选。"""
    if template_type:
        try:
            return load_template(template_type)
        except FileNotFoundError as e:
            typer.secho(f"❌ {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from e
    return _pick_template()


def _run_questions(template: TemplateDef, meta: PrdMeta) -> bool:
    """对未答字段逐个提问。返回是否被中途退出。"""
    required = sum(1 for f in template.fields if f.required)
    print(f"模板: {template.name} — 共 {len(template.fields)} 题(必填 {required})")

    total = len(template.fields)
    for i, field in enumerate(template.fields, 1):
        current = meta.get(field.key)
        if _is_filled(current):
            print(f"\n[{i}/{total}] ✓ {field.label} (已答,跳过)")
            continue
        print(f"\n[{i}/{total}]", end="")
        try:
            result = ask_field(field, meta)
        except QuitPrompt:
            print("\n⏸ 已保存当前进度,可重新运行 prd init 续答。")
            storage.save_meta(meta)
            return True

        apply_answer(meta, field, result)
        storage.save_meta(meta)

    return False


def _check_result(template: TemplateDef, meta: PrdMeta) -> tuple[bool, list[FieldDef]]:
    """返回(是否完整,缺失必填字段列表)。"""
    missing: list[FieldDef] = []
    for f in template.fields:
        if f.required and not _is_filled(meta.get(f.key)):
            missing.append(f)
    return len(missing) == 0, missing


def _format_status(template: TemplateDef, meta: PrdMeta) -> str:
    """格式化完整度状态文本。"""
    is_complete, missing = _check_result(template, meta)
    required_fields = [f for f in template.fields if f.required]
    required_filled = sum(1 for f in required_fields if _is_filled(meta.get(f.key)))
    filled = sum(1 for f in template.fields if _is_filled(meta.get(f.key)))
    total = len(template.fields)
    pct = round(filled * 100 / total) if total else 0
    status = "完整" if is_complete else "未完成"

    lines = [
        f"类型: {template.type}",
        f"必填: {required_filled}/{len(required_fields)} {status}",
        f"整体: {filled}/{total} ({pct}%)",
    ]
    if missing:
        lines.append("缺失必填:")
        for f in missing:
            lines.append(f"  • {f.label} ({f.key})  →  prd edit {f.key}")
    return "\n".join(lines)


def _render_and_report(template: TemplateDef, meta: PrdMeta, interrupted: bool) -> None:
    """渲染 PRD.md 并打印完成度报告。"""
    content = render_prd(template, meta)
    storage.save_prd(content)

    print()
    print(_format_status(template, meta))
    print(f"\n✅ PRD 已生成: {storage.prd_file()}")
    if interrupted:
        print("提示:运行 prd init 可继续未完成的字段。")


def _load_template_for_meta(meta: PrdMeta) -> TemplateDef:
    try:
        return load_template(meta.type)
    except FileNotFoundError:
        typer.secho(
            f"❌ meta 中记录的类型 {meta.type} 无对应模板。",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1) from None


def _preview(value: object) -> str:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return str(value)


def _print_editable_fields(template: TemplateDef, meta: PrdMeta) -> None:
    print(f"可编辑字段 (类型: {template.type}):")
    for f in template.fields:
        filled = _is_filled(meta.get(f.key))
        mark = "✓" if filled else "·"
        req = "必填" if f.required else "可选"
        status = "已填" if filled else "空"
        print(f"  {mark} {f.key:16} {f.label}  [{req}/{status}]  →  prd edit {f.key}")


@app.command()
def init(
    type: str | None = typer.Argument(None, help="项目类型,如 web-app。省略则交互选择。"),
    force: bool = typer.Option(False, "--force", "-f", help="清空已有 PRD 重新开始。"),
):
    """交互式初始化 PRD。"""
    existing = storage.load_meta()
    if existing and not force:
        print(f"发现已有 PRD(类型: {existing.type})。继续补充...")
        try:
            template = load_template(existing.type)
        except FileNotFoundError:
            template = _pick_template()
        meta = existing
    else:
        if storage.meta_exists() and not force:
            confirm = questionary.confirm(
                "已有 PRD,继续将清空所有答案。确定吗?", default=False
            ).ask()
            if not confirm:
                print("已取消。")
                raise typer.Exit(code=0)
        template = _resolve_template(type)
        meta = PrdMeta.new(template.type)
        storage.save_meta(meta)

    interrupted = _run_questions(template, meta)
    _render_and_report(template, meta, interrupted)


@app.command(name="new")
def new_cmd(
    type: str = typer.Argument(..., help="项目类型,如 web-app。"),
):
    """清空已有答案,按指定类型重新开始问答。"""
    if storage.meta_exists():
        confirm = questionary.confirm(
            "已有 PRD,new 将清空所有答案。确定吗?", default=False
        ).ask()
        if not confirm:
            print("已取消。")
            raise typer.Exit(code=0)

    template = _resolve_template(type)
    meta = PrdMeta.new(template.type)
    storage.save_meta(meta)
    interrupted = _run_questions(template, meta)
    _render_and_report(template, meta, interrupted)


@app.command()
def edit(
    field: str | None = typer.Argument(
        None, help="要编辑的字段 key,如 problem。省略则列出全部字段。"
    ),
):
    """编辑单个字段并重新生成 PRD;省略字段时列出可编辑项。"""
    meta = storage.require_meta()
    template = _load_template_for_meta(meta)

    if field is None:
        _print_editable_fields(template, meta)
        raise typer.Exit(code=0)

    field_def = template.find(field)
    if field_def is None:
        keys = ", ".join(f.key for f in template.fields)
        typer.secho(
            f"❌ 字段 `{field}` 不存在。可用字段: {keys}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    current = meta.get(field_def.key)
    # list 类型由 ask_list 展示当前项,避免重复打印
    if _is_filled(current) and field_def.type != "list":
        print(f"当前值: {_preview(current)}")

    try:
        result = ask_field(field_def, meta)
    except QuitPrompt:
        print("已取消编辑。")
        raise typer.Exit(code=0) from None

    apply_answer(meta, field_def, result)
    new = meta.get(field_def.key)
    if current == new:
        print("值未变化,跳过版本更新。")
    else:
        meta.bump(field_def.key, current, new)
        print(f"\n✅ 已更新「{field_def.label}」(v{meta.version})")
    storage.save_meta(meta)
    _render_and_report(template, meta, interrupted=False)


@app.command()
def check():
    """校验当前 PRD 完整度。退出码:0=完整,1=无PRD/错误,2=必填缺失。"""
    meta = storage.require_meta()
    template = _load_template_for_meta(meta)

    is_complete, _missing = _check_result(template, meta)
    print(_format_status(template, meta))
    if is_complete:
        print("\n可以开始编码。记得遵守范围 / 非目标 / 验收标准。")
    else:
        print("\n建议先补齐缺失项,或明确跳过后再编码。")

    raise typer.Exit(code=0 if is_complete else 2)


@app.command(name="show")
def show_cmd(
    section: str | None = typer.Option(
        None, "--section", "-s", help="只显示某个字段,如 problem。"
    ),
):
    """打印当前 PRD.md 内容,或单个字段小节。"""
    if section:
        meta = storage.require_meta()
        template = _load_template_for_meta(meta)
        try:
            print(render_section(template, meta, section), end="")
        except KeyError:
            keys = ", ".join(f.key for f in template.fields)
            typer.secho(
                f"❌ 字段 `{section}` 不存在。可用字段: {keys}",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1) from None
        return

    content = storage.read_prd()
    if content is None:
        typer.secho("❌ 没有 PRD。请先运行 prd init。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    print(content)


@template_app.command("list")
def template_list():
    """列出所有可用项目类型模板。"""
    templates = list_templates()
    if not templates:
        typer.secho("❌ 没有可用模板。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    for t in templates:
        required = sum(1 for f in t.fields if f.required)
        print(f"{t.type:16} {t.name}  (必填 {required} / 共 {len(t.fields)})")
        print(f"  {t.description}")
        print(f"  开始: prd init {t.type}")


@skill_app.command("install")
def skill_install(
    target: str = typer.Argument(
        "all",
        help="安装目标: claude / cursor / codex / all",
    ),
    user_global: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Claude:安装到用户目录 ~/.claude/skills/(默认装到当前项目)。",
    ),
):
    """一键把 Skill 写入 Claude Code / Cursor / Codex。"""
    from pathlib import Path

    root = Path.cwd()
    target = target.lower().strip()
    allowed = {"claude", "cursor", "codex", "all"}
    if target not in allowed:
        typer.secho(
            f"❌ 未知目标 `{target}`。可选: {', '.join(sorted(allowed))}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    written: list[Path] = []
    try:
        if target in {"claude", "all"}:
            written.append(install_claude(root, user_global=user_global))
        if target in {"cursor", "all"}:
            written.append(install_cursor(root))
        if target in {"codex", "all"}:
            written.append(install_codex(root))
    except OSError as e:
        typer.secho(f"❌ 写入失败: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e

    print("已安装 Skill:")
    for path in written:
        print(f"  ✓ {path}")
    print("\n重启或重开对话后生效。然后可以说:帮我做个 todo 应用")


@app.command()
def drill(
    topic: str | None = typer.Argument(None, help="要追问的主题或字段 key,如 problem。"),
):
    """对 PRD 的某个分支进行 drill-down 书面化追问,保存为 drill-<topic>.md。"""
    meta = storage.require_meta()
    try:
        template = load_template(meta.type)
    except FileNotFoundError:
        typer.secho(f"❌ meta 中记录的类型 {meta.type} 无对应模板。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None

    resolved_topic = topic
    if resolved_topic is None:
        choices = [f.label for f in template.fields]
        selected = questionary.select("选择要追问的分支:", choices=choices).ask()
        if selected is None:
            raise typer.Exit(code=0)
        label_to_key = {f.label: f.key for f in template.fields}
        resolved_topic = label_to_key[selected]

    guide = drill_module.load_drill_guide(meta.type)
    questions = drill_module.collect_questions(template, guide, resolved_topic)

    print(
        f"\n🔥 开始对「{resolved_topic}」进行 drill 追问。"
        f"共 {len(questions)} 个问题,输入 q 可随时退出。"
    )
    notes = drill_module.run_drill_session(questions)

    if not notes:
        print("没有记录任何内容,未保存。")
        raise typer.Exit(code=0)

    content = drill_module.render_drill_notes(resolved_topic, notes)
    path = storage.save_drill(resolved_topic, content)
    print(f"\n✅ Drill 笔记已保存: {path}")


if __name__ == "__main__":
    app()
