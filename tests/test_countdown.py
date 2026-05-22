from rich.console import Console

from pomo.timer import FocusTimer
from pomo.ui.countdown import ENCOURAGEMENTS, render_focus, render_summary


class FixedClock:
    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def _render(renderable) -> str:
    console = Console(width=72, no_color=True)
    with console.capture() as cap:
        console.print(renderable)
    return cap.get()


def test_encouragements_is_non_empty():
    assert len(ENCOURAGEMENTS) >= 1


def test_render_focus_shows_task_and_category():
    timer = FocusTimer(target_seconds=1500, clock=FixedClock())
    out = _render(render_focus("工作", "写文档", timer, ENCOURAGEMENTS[0]))
    assert "写文档" in out
    assert "工作" in out


def test_render_focus_shows_remaining_clock():
    timer = FocusTimer(target_seconds=1500, clock=FixedClock())
    out = _render(render_focus("工作", "写文档", timer, ENCOURAGEMENTS[0]))
    # 倒计时数字以空格间隔展示，剩余 25:00。
    assert "2 5 : 0 0" in out


def test_render_summary_shows_total_and_task():
    from pomo.models import Session

    session = Session(
        id="x",
        category="工作",
        task="写文档",
        started_at="2026-05-22T09:00:00",
        ended_at="2026-05-22T09:28:00",
        focus_seconds=1680,
        target_seconds=1500,
        reached_overtime=True,
    )
    out = _render(render_summary(session, 8100, [("工作", 8100, 3)]))
    assert "写文档" in out
    assert "今日累计" in out
    assert "2:15" in out
