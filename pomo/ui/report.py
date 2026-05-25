"""复盘报表渲染。"""

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pomo.models import Session
from pomo.ratings import Rating
from pomo.stats import (
    aggregate_by_category,
    focus_sessions,
    longest_session,
    rest_sessions,
    total_focus_seconds,
)
from pomo.ui.format import format_minutes, format_span, progress_bar
from pomo.ui.theme import FOCUS, REST


def _build_focus_body(focus: list[Session]) -> RenderableType:
    """报表主体：专注分类条形图 + 最长一段。"""
    pal = FOCUS
    total = total_focus_seconds(focus)
    rows = aggregate_by_category(focus)
    max_secs = max(secs for _, secs, _ in rows)
    longest = longest_session(focus)

    header = Text()
    header.append("专注", style=f"bold {pal.label}")
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

    return Group(header, Text(""), grid, Text(""), longest_line)


def _build_rest_block(rest: list[Session]) -> RenderableType:
    """报表中独立的休息条带。"""
    pal = REST
    total = sum(s.focus_seconds for s in rest)
    over = sum(1 for s in rest if s.reached_overtime)

    line = Text()
    line.append("休息", style=f"bold {pal.label}")
    line.append(
        f"        累计 {format_span(total)} · {len(rest)} 次",
        style=f"bold {pal.accent}",
    )
    if over:
        line.append(f"        其中 {over} 次超时", style=pal.dim)
    return line


def _stars(score: int) -> str:
    return "★" * score + "☆" * (5 - score)


def _build_ratings_block(ratings: list[Rating]) -> RenderableType:
    """评分区块：1 条 = 单日紧凑展示；多条 = 每天一行的小表。"""
    pal = FOCUS
    if len(ratings) == 1:
        r = ratings[0]
        line = Text()
        line.append("评分", style=f"bold {pal.label}")
        line.append(f"        {_stars(r.score)}", style=f"bold {pal.accent}")
        if r.comment:
            return Group(line, Text(f"        {r.comment}", style=pal.dim))
        return line

    header = Text("评分", style=f"bold {pal.label}")
    grid = Table.grid(padding=(0, 2))
    grid.add_column()  # 日期
    grid.add_column()  # 星
    grid.add_column()  # comment
    for r in ratings:
        grid.add_row(
            Text(r.date, style=pal.dim),
            Text(_stars(r.score), style=pal.accent),
            Text(r.comment, style=pal.dim),
        )
    return Group(header, Text(""), grid)


def build_report(
    title: str,
    sessions: list[Session],
    ratings: list[Rating] | None = None,
) -> RenderableType:
    """根据一组 session 构建报表面板。专注与休息分块展示，可选附带评分。"""
    focus = focus_sessions(sessions)
    rest = rest_sessions(sessions)
    ratings = ratings or []

    pal = FOCUS
    title_line = Text(title, style=f"bold {pal.label}")

    if not focus and not rest and not ratings:
        empty = Text(
            "这段时间还没有记录。开一次 pomo 吧。",
            style=pal.dim,
            justify="center",
        )
        body = Group(title_line, Text(""), empty)
        return Panel(body, border_style=pal.dim, padding=(1, 3), expand=False)

    parts: list[RenderableType] = [title_line, Text("")]
    if focus:
        parts.append(_build_focus_body(focus))
    elif rest or ratings:
        parts.append(Text("（这段时间还没有专注 session）", style=pal.dim))
    if rest:
        parts.append(Text(""))
        parts.append(_build_rest_block(rest))
    if ratings:
        parts.append(Text(""))
        parts.append(_build_ratings_block(ratings))

    return Panel(Group(*parts), border_style=pal.dim, padding=(1, 2), expand=False)
