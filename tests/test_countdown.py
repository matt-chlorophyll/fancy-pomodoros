from rich.console import Console

from pomo.models import KIND_REST, Session
from pomo.timer import FocusTimer
from pomo.ui.countdown import (
    ENCOURAGEMENTS,
    REST_ENCOURAGEMENTS,
    render_focus,
    render_rest_summary,
    render_summary,
)


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


def test_render_focus_overtime_shows_plus_prefix_and_status():
    clock = FixedClock(0.0)
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.t = 1600.0  # 100 秒加时
    out = _render(render_focus("工作", "写文档", timer, ENCOURAGEMENTS[0]))
    assert "+ 0 1 : 4 0" in out
    assert "加时中" in out


def test_render_focus_paused_shows_pause_indicator():
    clock = FixedClock(0.0)
    timer = FocusTimer(target_seconds=1500, clock=clock)
    timer.pause()
    out = _render(render_focus("工作", "写文档", timer, ENCOURAGEMENTS[0]))
    assert "已暂停" in out


def test_rest_encouragements_is_non_empty():
    assert len(REST_ENCOURAGEMENTS) >= 1


def test_render_focus_rest_kind_shows_rest_label_not_task():
    timer = FocusTimer(target_seconds=300, clock=FixedClock())
    out = _render(
        render_focus("休息", "休息", timer, REST_ENCOURAGEMENTS[0], kind=KIND_REST)
    )
    assert "休息" in out


def test_render_focus_rest_overtime_shows_back_to_work_hint():
    clock = FixedClock(0.0)
    timer = FocusTimer(target_seconds=300, clock=clock)
    clock.t = 400.0  # 100 秒休息超时
    out = _render(
        render_focus("休息", "休息", timer, REST_ENCOURAGEMENTS[0], kind=KIND_REST)
    )
    assert "+ 0 1 : 4 0" in out
    assert "回去工作" in out


def test_render_rest_summary_shows_total_rest_and_count():
    session = Session(
        id="x",
        category="休息",
        task="休息",
        started_at="2026-05-22T09:25:00",
        ended_at="2026-05-22T09:30:00",
        focus_seconds=300,
        target_seconds=300,
        reached_overtime=True,
        kind="rest",
    )
    out = _render(render_rest_summary(session, 600, 2))
    assert "休息结束" in out
    assert "5 分钟" in out
    assert "2 次" in out
    # 超时了，提示要回工作。
    assert "回去" in out


def test_render_rest_summary_under_target_shows_neutral_tail():
    session = Session(
        id="x",
        category="休息",
        task="休息",
        started_at="2026-05-22T09:25:00",
        ended_at="2026-05-22T09:28:00",
        focus_seconds=180,
        target_seconds=300,
        reached_overtime=False,
        kind="rest",
    )
    out = _render(render_rest_summary(session, 180, 1))
    assert "休息结束" in out
    assert "1 次" in out
