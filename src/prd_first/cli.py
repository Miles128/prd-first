"""prd-first CLI 入口。

命令:
  prd init [type]      交互式初始化(选类型 + 逐字段问答)
  prd check            校验完整度
  prd show             打印当前 PRD.md
"""

from __future__ import annotations

import questionary
import typer

from . import storage
from .models import FieldDef, PrdMeta, TemplateDef, _is_filled, list_templates, load_template
from .prompts import QuitPrompt, apply_answer, ask_field
from .render import render_prd

app = typer.Typer(
    name="prd",
    help="Vibecoding 前先写 PRD:交互式问答生成结构化 PRD。",
    no_args_is_help=True,
    add_completion=False,
)


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


def _render_and_report(template: TemplateDef, meta: PrdMeta, interrupted: bool) -> None:
    """渲染 PRD.md 并打印完成度报告。"""
    content = render_prd(template, meta)
    storage.save_prd(content)

    is_complete, missing = _check_result(template, meta)
    filled = sum(1 for f in template.fields if _is_filled(meta.get(f.key)))
    total = len(template.fields)
    pct = round(filled * 100 / total) if total else 0

    print()
    print(f"必填: {'OK' if is_complete else '未完成'} | 整体: {filled}/{total} | 完成度: {pct}%")
    if missing:
        print("缺失的必填项:")
        for f in missing:
            print(f"  • {f.label} ({f.key})")

    print(f"\n✅ PRD 已生成: {storage.prd_file()}")
    if interrupted:
        print("提示:运行 prd init 可继续未完成的字段。")


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


@app.command()
def check():
    """校验当前 PRD 完整度。退出码:0=完整,1=无PRD/错误,2=必填缺失。"""
    meta = storage.require_meta()
    try:
        template = load_template(meta.type)
    except FileNotFoundError:
        typer.secho(f"❌ meta 中记录的类型 {meta.type} 无对应模板。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None

    is_complete, missing = _check_result(template, meta)
    print(f"必填完整: {'是' if is_complete else '否'}")
    if missing:
        print("缺失必填项:")
        for f in missing:
            print(f"  • {f.label}")

    raise typer.Exit(code=0 if is_complete else 2)


@app.command(name="show")
def show_cmd():
    """打印当前 PRD.md 内容。"""
    content = storage.read_prd()
    if content is None:
        typer.secho("❌ 没有 PRD。请先运行 prd init。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    print(content)


if __name__ == "__main__":
    app()
