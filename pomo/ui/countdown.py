"""专注/休息倒计时画面与 session 结束卡片的渲染。"""

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pomo.models import KIND_FOCUS, KIND_REST, Session
from pomo.timer import FocusTimer, Phase
from pomo.ui.format import format_clock, format_minutes, format_span, progress_bar
from pomo.ui.theme import FOCUS, REST, palette_for

ENCOURAGEMENTS = [
    "保持专注，你做得很好",
    "一次只做一件事",
    "深呼吸，继续",
    "此刻就是最好的时机",
    "专注是一种温柔的力量",
]

REST_ENCOURAGEMENTS = [
    "舒展一下，喝口水",
    "看看远方，放松眼睛",
    "深呼吸几下",
    "起来走走，活动一下",
    "让大脑歇一会儿",
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
    kind: str = KIND_FOCUS,
) -> RenderableType:
    """渲染一帧 session 倒计时画面。专注与休息共用，靠 kind 区分配色与文案。"""
    phase = timer.phase
    pal = palette_for(phase, kind)
    is_rest = kind == KIND_REST

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

    if is_rest:
        label_text = "休息"
    else:
        label_text = f"{task} · {category}"
    label = Text(label_text, style=pal.label, justify="center")

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
        if is_rest:
            status_text = "休息超时 · 该回去工作啦"
        else:
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
    """渲染专注 session 结束卡片。"""
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


def render_rest_summary(
    session: Session,
    today_rest_total_seconds: int,
    today_rest_count: int,
) -> RenderableType:
    """渲染休息 session 结束卡片。"""
    overtime = session.reached_overtime
    pal = REST  # 用暖色收尾；即便超时了，这里也不再红，避免徒增焦虑。

    head = Text(justify="left")
    head.append("✓ 休息结束  ", style=f"bold {pal.accent}")
    head.append(format_minutes(session.focus_seconds), style=pal.label)
    if overtime:
        head.append("（超出了目标）", style=pal.label)

    total = Text(
        f"  今日累计休息  {format_span(today_rest_total_seconds)} · {today_rest_count} 次",
        style=f"bold {pal.accent}",
    )

    tail_text = "  该回去专注啦 ✦" if overtime else "  回去继续 ✦"
    body = Group(
        head,
        Text(""),
        total,
        Text(""),
        Text(tail_text, style=pal.dim),
    )
    return Panel(
        body,
        title="休息完成",
        border_style=pal.dim,
        padding=(1, 3),
        expand=False,
    )
