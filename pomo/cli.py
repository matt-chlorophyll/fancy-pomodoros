"""Typer CLI：start / report 命令。"""

import random
import time
from datetime import date as date_cls
from datetime import datetime

import typer
from rich.console import Console
from rich.live import Live
from rich.prompt import Confirm

from pomo.config import DEFAULT_FOCUS_MINUTES, sessions_file
from pomo.keyboard import KEY_ENTER, KEY_ESC, KEY_SPACE, read_key
from pomo.models import Session
from pomo.stats import (
    aggregate_by_category,
    sessions_in_week,
    sessions_on_date,
    total_focus_seconds,
)
from pomo.storage import append_session, load_sessions
from pomo.timer import FocusTimer, Phase
from pomo.ui.countdown import ENCOURAGEMENTS, render_focus, render_summary
from pomo.ui.prompts import pick_category, pick_task, ready_ritual
from pomo.ui.report import build_report

app = typer.Typer(add_completion=False, help="Fancy Pomodoro — 专注计时与时间记录。")


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
) -> str:
    """运行实时倒计时画面。返回 'finished' 或 'abandoned'。"""
    belled = False
    with Live(
        render_focus(category, task, timer, encouragement),
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
                live.update(render_focus(category, task, timer, encouragement))
                time.sleep(0.2)
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
    )
    append_session(path, session)

    today = sessions_on_date(load_sessions(path), started_at.date())
    console.print()
    console.print(
        render_summary(
            session,
            total_focus_seconds(today),
            aggregate_by_category(today),
        )
    )
    console.print()


@app.command()
def start(
    minutes: int = typer.Option(
        DEFAULT_FOCUS_MINUTES, "--minutes", "-m", help="本次专注目标时长（分钟）。"
    ),
) -> None:
    """开一次专注 session。"""
    run_session(minutes)
