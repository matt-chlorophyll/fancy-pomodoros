"""复盘报表渲染。"""

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pomo.models import Session
from pomo.stats import aggregate_by_category, longest_session, total_focus_seconds
from pomo.ui.format import format_minutes, format_span, progress_bar
from pomo.ui.theme import FOCUS


def build_report(title: str, sessions: list[Session]) -> RenderableType:
    """根据一组 session 构建报表面板。"""
    pal = FOCUS

    if not sessions:
        empty = Text(
            "这段时间还没有记录。开一次 pomo 吧。",
            style=pal.dim,
            justify="center",
        )
        return Panel(
            empty,
            title=title,
            border_style=pal.dim,
            padding=(1, 3),
            expand=False,
        )

    total = total_focus_seconds(sessions)
    rows = aggregate_by_category(sessions)
    max_secs = max(secs for _, secs, _ in rows)
    longest = longest_session(sessions)

    header = Text()
    header.append(title, style=f"bold {pal.label}")
    header.append(f"        总计 {format_span(total)}", style=f"bold {pal.accent}")

    grid = Table.grid(padding=(0, 2))
    grid.add_column()  # 分类
    grid.add_column()  # 条形图
    grid.add_column()  # 时长 · session 数
    for cat, secs, count in rows:
        bar = progress_bar(secs / max_secs if max_secs else 0.0, width=22)
        grid.add_row(
            Text(cat, style=pal.label),
            Text(bar, style=pal.accent),
            Text(f"{format_span(secs)}  · {count} 个 session", style=pal.dim),
        )

    longest_line = Text(
        f"最长一段   {longest.task} · {longest.category} · "
        f"{format_minutes(longest.focus_seconds)}",
        style=pal.dim,
    )

    body = Group(header, Text(""), grid, Text(""), longest_line)
    return Panel(body, border_style=pal.dim, padding=(1, 2), expand=False)
