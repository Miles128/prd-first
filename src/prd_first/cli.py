"""prd-first CLI 入口。

命令:
  prd init [type]      交互式初始化(选类型 + 逐字段问答)
  prd new <type>       直接用指定模板开始空白 PRD(等同 init 且指定 type)
  prd check            校验完整度
  prd show             打印当前 PRD.md
  prd edit [field]     重问指定字段
  prd template list    列出内置模板
"""

from __future__ import annotations

from typing import Optional

import questionary
import typer
from rich.table import Table

from . import storage
from .checker import check as run_check
from .models import PrdMeta, TemplateDef, list_templates, load_template
from .prompts import QuitPrompt, apply_answer, ask_field, _get_console
from .render import render_prd

app = typer.Typer(
    name="prd",
    help="Vibecoding 前先写详尽 PRD:交互式问答生成结构化 PRD。",
    no_args_is_help=True,
    add_completion=False,
)
template_app = typer.Typer(help="模板管理。")
app.add_typer(template_app, name="template")


def _pick_template() -> TemplateDef:
    """交互式选择项目类型。"""
    templates = list_templates()
    if not templates:
        typer.secho("❌ 没有可用模板。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    choices = [f"{t.name}  ({t.type})  — {t.description}" for t in templates]
    selected = questionary.select(
        "这是什么类型的项目?",
        choices=choices,
    ).ask()
    if selected is None:
        raise typer.Exit(code=0)

    # 从选项反查 type
    idx = choices.index(selected)
    return templates[idx]


def _resolve_template(template_type: Optional[str]) -> TemplateDef:
    """解析模板:type 给了直接加载,否则交互选。"""
    if template_type:
        try:
            return load_template(template_type)
        except FileNotFoundError as e:
            typer.secho(f"❌ {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    return _pick_template()


def _run_questions(template: TemplateDef, meta: PrdMeta) -> bool:
    """对所有字段逐个提问。返回是否被中途退出(quit)。

    每答完一题即持久化 meta.yaml(断点续答)。
    """
    console = _get_console()
    total = len(template.fields)
    for i, field in enumerate(template.fields, 1):
        console.print(f"\n[bold cyan][{i}/{total}][/bold cyan]", end="")
        try:
            result = ask_field(field, meta)
        except QuitPrompt:
            console.print(
                "\n[yellow]⏸  已保存当前进度,"
                "可重新运行 prd init 或 prd new 续答。[/yellow]"
            )
            storage.save_meta(meta)
            return True  # 被中断

        apply_answer(meta, field, result)
        storage.save_meta(meta)  # 每题持久化

    return False  # 正常完成


def _render_and_report(template: TemplateDef, meta: PrdMeta, interrupted: bool) -> None:
    """渲染 PRD.md 并打印完成度报告。"""
    console = _get_console()
    content = render_prd(template, meta)
    storage.save_prd(content)

    result = run_check(template, meta)
    console.print()
    console.rule("[bold]PRD 完整度[/bold]")
    console.print(
        f"必填:[bold {'green' if result.is_complete else 'red'}]"
        f"{result.required_filled}/{result.required_total}[/bold]  "
        f"整体:[bold]{result.filled}/{result.total}[/bold]  "
        f"完成度:[bold]{result.completeness_pct}%[/bold]"
    )

    if result.missing_required:
        console.print("\n[red]⚠ 缺失的必填项:[/red]")
        for fs in result.missing_required:
            console.print(f"   • {fs.label} [dim]({fs.key})[/dim]")

    console.print(f"\n✅ PRD 已生成:[blue]{storage.prd_file()}[/blue]")
    if interrupted:
        console.print(
            "[dim]提示:运行 prd init 或 prd new 可继续未完成的字段。[/dim]"
        )


@app.command()
def init(
    type: Optional[str] = typer.Argument(
        None, help="项目类型,如 web-app。省略则交互选择。"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="即使已有 PRD 也重新开始(保留与新模板同 key 的已填答案)。"
    ),
):
    """交互式初始化 PRD:选类型 → 逐字段问答 → 生成 PRD.md。"""
    console = _get_console()
    # 续答判断
    existing = storage.load_meta()
    if existing and not force:
        console.print(f"[dim]发现已有 PRD(meta 类型: {existing.type})。继续补充...[/dim]")
        try:
            template = load_template(existing.type)
        except FileNotFoundError:
            template = _pick_template()
        meta = existing
    else:
        template = _resolve_template(type)
        if existing is None:
            meta = PrdMeta.new(template.type)
            storage.save_meta(meta)
        else:
            # --force: 重置 meta 但保留与新模板同 key 的已填答案
            meta = PrdMeta.new(template.type)
            for field in template.fields:
                key = field.key
                if (
                    key in existing.answers
                    and existing.statuses.get(key) == "answered"
                ):
                    meta.set_answer(key, existing.answers[key], status="answered")
            storage.save_meta(meta)

    interrupted = _run_questions(template, meta)
    _render_and_report(template, meta, interrupted)


@app.command()
def new(
    type: str = typer.Argument(..., help="项目类型,如 web-app"),
):
    """用指定模板开始一个新的空白 PRD(清空已有答案)。"""
    template = _resolve_template(type)
    meta = PrdMeta.new(template.type)
    storage.save_meta(meta)
    console = _get_console()
    console.print(f"[green]✓ 已用模板 {template.name} 初始化空白 PRD。开始问答...[/green]")
    interrupted = _run_questions(template, meta)
    _render_and_report(template, meta, interrupted)


@app.command()
def check():
    """校验当前 PRD 完整度。"""
    meta = storage.require_meta()
    try:
        template = load_template(meta.type)
    except FileNotFoundError:
        typer.secho(f"❌ meta 中记录的类型 {meta.type} 无对应模板。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    result = run_check(template, meta)
    console = _get_console()

    console.rule("[bold]PRD 完整度[/bold]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("类别", style="cyan")
    table.add_column("完成", justify="right")
    table.add_column("总计", justify="right")
    table.add_column("百分比", justify="right")
    table.add_row(
        "必填",
        str(result.required_filled),
        str(result.required_total),
        f"{result.required_pct}%",
    )
    table.add_row(
        "全部",
        str(result.filled),
        str(result.total),
        f"{result.completeness_pct}%",
    )
    console.print(table)

    if result.missing_required:
        console.print("\n[red]⚠ 缺失的必填项(运行 prd edit <key> 补全):[/red]")
        for fs in result.missing_required:
            console.print(f"   • {fs.label} [dim](prd edit {fs.key})[/dim]")
    else:
        console.print("\n[green]✓ 所有必填项已就绪,可以开始编码。[/green]")

    raise typer.Exit(code=0 if result.is_complete else 2)


@app.command(name="show")
def show_cmd():
    """打印当前 PRD.md 内容。"""
    content = storage.read_prd()
    if content is None:
        typer.secho("❌ 没有 PRD。请先运行 prd init。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    console = _get_console()
    console.print(content, highlight=False)


@app.command()
def edit(
    field: str = typer.Argument(..., help="要重新作答的字段 key(见 prd check 输出)。"),
):
    """重新作答单个字段。"""
    meta = storage.require_meta()
    try:
        template = load_template(meta.type)
    except FileNotFoundError:
        typer.secho(f"❌ meta 类型 {meta.type} 无对应模板。", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    fd = template.find(field)
    if fd is None:
        typer.secho(
            f"❌ 字段 {field} 不存在于模板 {template.type}。", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=1)

    try:
        result = ask_field(fd, meta)
    except QuitPrompt:
        console = _get_console()
        console.print("[yellow]⏸  未修改。[/yellow]")
        return

    apply_answer(meta, fd, result)
    storage.save_meta(meta)

    # 重新渲染 PRD
    content = render_prd(template, meta)
    storage.save_prd(content)
    console = _get_console()
    console.print(f"[green]✓ 已更新 {fd.label},PRD 已重新生成。[/green]")


@template_app.command(name="list")
def template_list():
    """列出所有内置模板。"""
    templates = list_templates()
    if not templates:
        typer.secho("没有可用模板。", fg=typer.colors.YELLOW)
        return

    console = _get_console()
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("类型", style="cyan")
    table.add_column("名称")
    table.add_column("字段数", justify="right")
    table.add_column("说明")
    for t in templates:
        table.add_row(t.type, t.name, str(len(t.fields)), t.description)
    console.print(table)


if __name__ == "__main__":
    app()
