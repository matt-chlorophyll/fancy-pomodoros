from rich.console import Console

from pomo.models import KIND_REST, Session
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


def _rest(task: str, focus: int, target: int = 300) -> Session:
    return Session(
        id="id-" + task,
        category="休息",
        task="休息",
        started_at="2026-05-22T09:25:00",
        ended_at="2026-05-22T09:30:00",
        focus_seconds=focus,
        target_seconds=target,
        reached_overtime=focus >= target,
        kind=KIND_REST,
    )


def test_build_report_excludes_rest_from_focus_total():
    sessions = [
        _session("写文档", "工作", 1500),
        _rest("休息1", 600),  # 10 分钟休息
    ]
    out = _render(build_report("2026-05-22  今日复盘", sessions))
    # 总计应该只算专注的 25 分钟，不能把休息 10 分钟一起加进去。
    assert "总计 0:25" in out


def test_build_report_shows_rest_block_separately():
    sessions = [
        _session("写文档", "工作", 1500),
        _rest("休息1", 300),
        _rest("休息2", 600),
    ]
    out = _render(build_report("2026-05-22  今日复盘", sessions))
    assert "休息" in out
    # rest 块显示次数。
    assert "2 次" in out


def test_build_report_omits_rest_block_when_no_rest():
    sessions = [_session("写文档", "工作", 1500)]
    out = _render(build_report("2026-05-22  今日复盘", sessions))
    assert "次" not in out  # 没有 rest 时不出现 "N 次" 的字样


def test_build_report_handles_only_rest_sessions():
    sessions = [_rest("休息1", 300)]
    out = _render(build_report("2026-05-22  今日复盘", sessions))
    # 不应崩溃，且应能看到休息块。
    assert "休息" in out
