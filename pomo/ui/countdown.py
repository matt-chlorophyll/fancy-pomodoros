"""专注/加时实时画面与 session 结束卡片的渲染。"""

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pomo.models import Session
from pomo.timer import FocusTimer, Phase
from pomo.ui.format import format_clock, format_minutes, format_span, progress_bar
from pomo.ui.theme import FOCUS, palette_for

ENCOURAGEMENTS = [
    "保持专注，你做得很好",
    "一次只做一件事",
    "深呼吸，继续",
    "此刻就是最好的时机",
    "专注是一种温柔的力量",
]

_KEYS_HINT = "空格 暂停 / 继续      s 完成      Esc 放弃"


def _spaced(text: str) -> str:
    """'25:00' -> '2 5 : 0 0'，营造极简的大号数字感。"""
    return " ".join(text)


def render_focus(
    category: str,
    task: str,
    timer: FocusTimer,
    encouragement: str,
) -> RenderableType:
    """渲染一帧专注/加时画面。"""
    phase = timer.phase
    pal = palette_for(phase)

    if phase is Phase.FOCUS:
        clock_text = format_clock(timer.remaining())
        fraction = (
            timer.elapsed_focus() / timer.target_seconds
            if timer.target_seconds
            else 1.0
        )
    else:
        clock_text = "+" + format_clock(timer.overtime())
        fraction = 1.0

    label = Text(f"{task} · {category}", style=pal.label, justify="center")

    big = Text(_spaced(clock_text), style=f"bold {pal.accent}", justify="center")
    panel = Panel(big, border_style=pal.dim, padding=(1, 4), expand=False)

    pct = int(min(1.0, max(0.0, fraction)) * 100)
    bar = Text(
        f"{progress_bar(fraction)}  {pct}%",
        style=pal.accent,
        justify="center",
    )

    if timer.is_paused:
        status_text = "⏸  已暂停"
    elif phase is Phase.OVERTIME:
        status_text = "加时中 · 做完按 s 收尾"
    else:
        status_text = f"· {encouragement} ·"
    status = Text(status_text, style=pal.dim, justify="center")

    keys = Text(_KEYS_HINT, style=pal.dim, justify="center")

    group = Group(
        label,
        Text(""),
        Align.center(panel),
        Text(""),
        bar,
        Text(""),
        status,
        Text(""),
        keys,
    )
    return Align.center(group)


def render_summary(
    session: Session,
    today_total_seconds: int,
    today_category_rows: list[tuple[str, int, int]],
) -> RenderableType:
    """渲染 session 结束卡片。"""
    pal = FOCUS

    head = Text(justify="left")
    head.append("✓ 本次  ", style=f"bold {pal.accent}")
    head.append(f"{session.task} · {session.category}", style=pal.label)

    dur_text = f"  专注 {format_minutes(session.focus_seconds)}"
    if session.reached_overtime:
        dur_text += "（含加时）"
    dur = Text(dur_text, style=pal.label)

    total = Text(
        f"  今日累计  {format_span(today_total_seconds)}",
        style=f"bold {pal.accent}",
    )

    breakdown = Table.grid(padding=(0, 2))
    breakdown.add_column()
    breakdown.add_column()
    breakdown.add_column()
    for cat, secs, count in today_category_rows:
        breakdown.add_row(
            Text(f"  {cat}", style=pal.dim),
            Text(format_span(secs), style=pal.dim),
            Text(f"· {count} 个", style=pal.dim),
        )

    body = Group(
        head,
        dur,
        Text(""),
        total,
        Text(""),
        breakdown,
        Text(""),
        Text("  好好休息一下 ☕", style=pal.dim),
    )
    return Panel(
        body,
        title="session 完成",
        border_style=pal.dim,
        padding=(1, 3),
        expand=False,
    )
