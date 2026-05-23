from datetime import date

from pomo.models import KIND_FOCUS, KIND_REST, Session
from pomo.stats import (
    aggregate_by_category,
    focus_sessions,
    longest_session,
    rest_sessions,
    sessions_in_week,
    sessions_on_date,
    total_focus_seconds,
    week_bounds,
)


def _session(
    task: str, category: str, day: str, focus: int, kind: str = KIND_FOCUS
) -> Session:
    return Session(
        id="id-" + task,
        category=category,
        task=task,
        started_at=f"{day}T09:00:00",
        ended_at=f"{day}T09:30:00",
        focus_seconds=focus,
        target_seconds=1500,
        reached_overtime=focus >= 1500,
        kind=kind,
    )


def test_sessions_on_date_filters_by_day():
    sessions = [
        _session("a", "工作", "2026-05-22", 1500),
        _session("b", "工作", "2026-05-21", 1500),
    ]
    result = sessions_on_date(sessions, date(2026, 5, 22))
    assert [s.task for s in result] == ["a"]


def test_week_bounds_returns_monday_to_sunday():
    monday, sunday = week_bounds(date(2026, 5, 22))  # 周五
    assert monday == date(2026, 5, 18)
    assert sunday == date(2026, 5, 24)


def test_sessions_in_week_includes_whole_week():
    sessions = [
        _session("mon", "工作", "2026-05-18", 1500),
        _session("sun", "工作", "2026-05-24", 1500),
        _session("next", "工作", "2026-05-25", 1500),
    ]
    result = sessions_in_week(sessions, date(2026, 5, 22))
    assert sorted(s.task for s in result) == ["mon", "sun"]


def test_total_focus_seconds_sums_all():
    sessions = [
        _session("a", "工作", "2026-05-22", 1500),
        _session("b", "学习", "2026-05-22", 600),
    ]
    assert total_focus_seconds(sessions) == 2100


def test_aggregate_by_category_sorts_by_seconds_desc():
    sessions = [
        _session("a", "学习", "2026-05-22", 600),
        _session("b", "工作", "2026-05-22", 1500),
        _session("c", "工作", "2026-05-22", 900),
    ]
    rows = aggregate_by_category(sessions)
    assert rows == [("工作", 2400, 2), ("学习", 600, 1)]


def test_longest_session_returns_max_focus():
    sessions = [
        _session("short", "工作", "2026-05-22", 600),
        _session("long", "工作", "2026-05-22", 3000),
    ]
    assert longest_session(sessions).task == "long"


def test_longest_session_of_empty_is_none():
    assert longest_session([]) is None


def test_focus_sessions_filters_out_rest():
    sessions = [
        _session("a", "工作", "2026-05-22", 1500),
        _session("rest1", "休息", "2026-05-22", 300, kind=KIND_REST),
        _session("b", "学习", "2026-05-22", 1500),
    ]
    assert [s.task for s in focus_sessions(sessions)] == ["a", "b"]


def test_rest_sessions_filters_to_rest_only():
    sessions = [
        _session("a", "工作", "2026-05-22", 1500),
        _session("rest1", "休息", "2026-05-22", 300, kind=KIND_REST),
        _session("rest2", "休息", "2026-05-22", 600, kind=KIND_REST),
    ]
    assert [s.task for s in rest_sessions(sessions)] == ["rest1", "rest2"]
