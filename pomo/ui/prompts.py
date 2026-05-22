"""会话开始前的交互：分类选择、任务输入、3·2·1 仪式。"""

import time

from rich.align import Align
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text

from pomo.models import Session


def known_categories(sessions: list[Session]) -> list[str]:
    """历史出现过的分类，最近使用的在前，去重。"""
    seen: list[str] = []
    for s in reversed(sessions):
        if s.category not in seen:
            seen.append(s.category)
    return seen


def recent_tasks(
    sessions: list[Session],
    category: str,
    limit: int = 5,
) -> list[str]:
    """指定分类下最近用过的任务名，最近的在前，去重，最多 limit 个。"""
    seen: list[str] = []
    for s in reversed(sessions):
        if s.category == category and s.task not in seen:
            seen.append(s.task)
            if len(seen) >= limit:
                break
    return seen


def _pick_from_list(console: Console, prompt: str, options: list[str]) -> str:
    """展示编号选项，让用户输入编号选择，或直接输入新值。空输入会重问。"""
    for i, opt in enumerate(options, 1):
        console.print(f"  [cyan]{i}[/cyan]  {opt}")
    if options:
        console.print("  [dim]或直接输入一个新的[/dim]")
    while True:
        raw = Prompt.ask(prompt, console=console).strip()
        if raw.isdigit() and options and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw:
            return raw


def pick_category(console: Console, sessions: list[Session]) -> str:
    """选择或输入一个分类。"""
    console.print("[dim]选择分类：[/dim]")
    return _pick_from_list(console, "分类", known_categories(sessions))


def pick_task(console: Console, sessions: list[Session], category: str) -> str:
    """选择或输入这次要做的任务。"""
    console.print(f"[dim]这次在「{category}」里做什么？[/dim]")
    return _pick_from_list(console, "任务", recent_tasks(sessions, category))


def ready_ritual(console: Console) -> None:
    """开始前约 3.5 秒的 3·2·1 仪式。"""
    console.print()
    for n in ("3", "2", "1"):
        console.print(Align.center(Text(n, style="bold cyan")))
        time.sleep(0.7)
    console.print(Align.center(Text("开始 ·", style="dim")))
    time.sleep(0.5)
