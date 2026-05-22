"""Typer CLI：start / report 命令。"""

from datetime import date as date_cls
from datetime import datetime

import typer
from rich.console import Console

from pomo.config import sessions_file
from pomo.stats import sessions_in_week, sessions_on_date
from pomo.storage import load_sessions
from pomo.ui.report import build_report

app = typer.Typer(add_completion=False, help="Fancy Pomodoro — 专注计时与时间记录。")


@app.callback()
def _main() -> None:
    """Fancy Pomodoro — 专注计时与时间记录。"""


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
    date: str = typer.Option(
        None, "--date", help="查看指定日，格式 YYYY-MM-DD。"
    ),
) -> None:
    """查看专注复盘报表（默认今天）。"""
    if date:
        try:
            target = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            typer.echo(f"日期格式无效：{date}（应为 YYYY-MM-DD）")
            raise typer.Exit(code=1)
    else:
        target = date_cls.today()
    show_report(target, week)
