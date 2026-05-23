"""Typer CLI：start / rest / report 命令。"""

import random
import sys
import time
from datetime import date as date_cls
from datetime import datetime

import typer
from rich.console import Console
from rich.live import Live
from rich.prompt import Confirm

from pomo.config import DEFAULT_FOCUS_MINUTES, DEFAULT_REST_MINUTES, sessions_file
from pomo.keyboard import KEY_ENTER, KEY_ESC, KEY_SPACE, read_key
from pomo.models import KIND_FOCUS, KIND_REST, Session
from pomo.stats import (
    aggregate_by_category,
    focus_sessions,
    rest_sessions,
    sessions_in_week,
    sessions_on_date,
    total_focus_seconds,
)
from pomo.storage import append_session, load_sessions
from pomo.timer import FocusTimer, Phase
from pomo.ui.countdown import (
    ENCOURAGEMENTS,
    REST_ENCOURAGEMENTS,
    render_focus,
    render_rest_summary,
    render_summary,
)
from pomo.ui.prompts import pick_category, pick_task, ready_ritual
from pomo.ui.report import build_report

app = typer.Typer(add_completion=False, help="Fancy Pomodoro — 专注计时与时间记录。")

# 休息 session 在记录里固定的 category / task 名。
_REST_CATEGORY = "休息"
_REST_TASK = "休息"


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    """不带子命令时直接开始一次默认时长的 session。"""
    if ctx.invoked_subcommand is None:
        run_session(DEFAULT_FOCUS_MINUTES)


def show_report(target_day: date_cls, week: bool) -> None:
    """渲染并打印复盘报表。"""
    console = Console()
    sessions = load_sessions(sessions_file())
    if week:
        scope = sessions_in_week(sessions, target_day)
        title = f"{target_day.isoformat()} 所在周  本周复盘"
    else:
        scope = sessions_on_date(sessions, target_day)
        title = f"{target_day.isoformat()}  当日复盘"
    console.print()
    console.print(build_report(title, scope))
    console.print()


@app.command()
def report(
    week: bool = typer.Option(False, "--week", help="查看本周（周一至周日）。"),
    date_str: str = typer.Option(
        None, "--date", help="查看指定日，格式 YYYY-MM-DD。"
    ),
) -> None:
    """查看专注复盘报表（默认今天）。"""
    if date_str:
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo(f"日期格式无效：{date_str}（应为 YYYY-MM-DD）")
            raise typer.Exit(code=1)
    else:
        target = date_cls.today()
    show_report(target, week)


def _countdown_loop(
    console: Console,
    category: str,
    task: str,
    timer: FocusTimer,
    encouragement: str,
    kind: str = KIND_FOCUS,
) -> str:
    """运行实时倒计时画面。返回 'finished' 或 'abandoned'。"""
    belled = False
    with Live(
        render_focus(category, task, timer, encouragement, kind),
        console=console,
        transient=True,
        refresh_per_second=8,
    ) as live:
        try:
            while True:
                key = read_key()
                if key == KEY_SPACE:
                    timer.toggle_pause()
                elif key in (KEY_ENTER, "s"):
                    return "finished"
                elif key == KEY_ESC:
                    live.stop()
                    timer.pause()
                    if Confirm.ask("确定放弃本次吗？将不会记录", default=False):
                        return "abandoned"
                    timer.resume()
                    live.start()
                if not belled and timer.phase is Phase.OVERTIME:
                    console.bell()
                    belled = True
                live.update(render_focus(category, task, timer, encouragement, kind))
                time.sleep(0.05)
        except KeyboardInterrupt:
            return "finished"


def run_session(minutes: int) -> None:
    """完整跑一次专注 session：选任务 → 计时 → 记录 → 小结。"""
    console = Console()
    path = sessions_file()
    sessions = load_sessions(path)

    category = pick_category(console, sessions)
    task = pick_task(console, sessions, category)
    ready_ritual(console)

    started_at = datetime.now()
    timer = FocusTimer(target_seconds=minutes * 60)
    encouragement = random.choice(ENCOURAGEMENTS)

    outcome = _countdown_loop(console, category, task, timer, encouragement)
    ended_at = datetime.now()

    if outcome == "abandoned":
        console.print("[dim]已放弃本次，未记录。[/dim]")
        return

    session = Session.create(
        category=category,
        task=task,
        started_at=started_at,
        ended_at=ended_at,
        focus_seconds=timer.elapsed_focus(),
        target_seconds=minutes * 60,
        kind=KIND_FOCUS,
    )
    append_session(path, session)

    today_focus = focus_sessions(sessions_on_date(load_sessions(path), started_at.date()))
    console.print()
    console.print(
        render_summary(
            session,
            total_focus_seconds(today_focus),
            aggregate_by_category(today_focus),
        )
    )
    console.print()


def run_rest_session(minutes: int) -> None:
    """完整跑一次休息 session：3·2·1 → 计时 → 记录 → 休息小结。"""
    console = Console()
    path = sessions_file()

    ready_ritual(console)

    started_at = datetime.now()
    timer = FocusTimer(target_seconds=minutes * 60)
    encouragement = random.choice(REST_ENCOURAGEMENTS)

    outcome = _countdown_loop(
        console, _REST_CATEGORY, _REST_TASK, timer, encouragement, kind=KIND_REST
    )
    ended_at = datetime.now()

    if outcome == "abandoned":
        console.print("[dim]已放弃本次休息，未记录。[/dim]")
        return

    session = Session.create(
        category=_REST_CATEGORY,
        task=_REST_TASK,
        started_at=started_at,
        ended_at=ended_at,
        focus_seconds=timer.elapsed_focus(),
        target_seconds=minutes * 60,
        kind=KIND_REST,
    )
    append_session(path, session)

    today_rest = rest_sessions(sessions_on_date(load_sessions(path), started_at.date()))
    today_rest_total = sum(s.focus_seconds for s in today_rest)
    console.print()
    console.print(render_rest_summary(session, today_rest_total, len(today_rest)))
    console.print()


@app.command()
def start(
    minutes: int = typer.Option(
        DEFAULT_FOCUS_MINUTES, "--minutes", "-m", min=1, help="本次专注目标时长（分钟）。"
    ),
) -> None:
    """开一次专注 session。"""
    run_session(minutes)


@app.command()
def rest(
    minutes: int = typer.Option(
        DEFAULT_REST_MINUTES, "--minutes", "-m", min=1, help="本次休息目标时长（分钟）。"
    ),
) -> None:
    """开一次休息 session。"""
    run_rest_session(minutes)


def _ensure_utf8_stdio() -> None:
    """非 UTF-8 的 Windows 控制台下把 stdout/stderr 切到 UTF-8，避免中文输出崩溃。"""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        encoding = (getattr(stream, "encoding", "") or "").lower()
        if (
            stream is not None
            and hasattr(stream, "reconfigure")
            and encoding not in ("utf-8", "utf8")
        ):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def main() -> None:
    """控制台入口：先确保 UTF-8 输出，再运行 CLI。"""
    _ensure_utf8_stdio()
    app()
