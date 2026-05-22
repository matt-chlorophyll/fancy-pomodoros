from rich.console import Console

from pomo.models import Session
from pomo.ui.report import build_report


def _render(renderable) -> str:
    console = Console(width=80, no_color=True)
    with console.capture() as cap:
        console.print(renderable)
    return cap.get()


def _session(task: str, category: str, focus: int) -> Session:
    return Session(
        id="id-" + task,
        category=category,
        task=task,
        started_at="2026-05-22T09:00:00",
        ended_at="2026-05-22T09:30:00",
        focus_seconds=focus,
        target_seconds=1500,
        reached_overtime=focus >= 1500,
    )


def test_build_report_empty_state():
    out = _render(build_report("2026-05-22  今日复盘", []))
    assert "还没有记录" in out


def test_build_report_shows_categories_and_total():
    sessions = [
        _session("写文档", "工作", 9000),
        _session("读论文", "学习", 2100),
    ]
    out = _render(build_report("2026-05-22  今日复盘", sessions))
    assert "工作" in out
    assert "学习" in out
    assert "总计 3:05" in out


def test_build_report_shows_longest_session():
    sessions = [
        _session("写文档", "工作", 9000),
        _session("读论文", "学习", 2100),
    ]
    out = _render(build_report("2026-05-22  今日复盘", sessions))
    assert "最长一段" in out
    assert "写文档" in out
