"""按日期过滤与按分类/任务聚合 session 数据。"""

from collections import defaultdict
from datetime import date, datetime, timedelta

from pomo.models import Session


def _session_date(session: Session) -> date:
    return datetime.fromisoformat(session.started_at).date()


def sessions_on_date(sessions: list[Session], day: date) -> list[Session]:
    """筛出指定日期的 session。"""
    return [s for s in sessions if _session_date(s) == day]


def week_bounds(day: date) -> tuple[date, date]:
    """返回包含 day 的那一周的周一与周日。"""
    monday = day - timedelta(days=day.weekday())
    return monday, monday + timedelta(days=6)


def sessions_in_week(sessions: list[Session], day: date) -> list[Session]:
    """筛出与 day 同一周（周一至周日）的 session。"""
    monday, sunday = week_bounds(day)
    return [s for s in sessions if monday <= _session_date(s) <= sunday]


def total_focus_seconds(sessions: list[Session]) -> int:
    """所有 session 的专注秒数之和。"""
    return sum(s.focus_seconds for s in sessions)


def aggregate_by_category(sessions: list[Session]) -> list[tuple[str, int, int]]:
    """按分类聚合，返回 [(分类, 总秒数, session 数)]，按总秒数降序。"""
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for s in sessions:
        totals[s.category][0] += s.focus_seconds
        totals[s.category][1] += 1
    rows = [(cat, secs, count) for cat, (secs, count) in totals.items()]
    return sorted(rows, key=lambda row: row[1], reverse=True)


def longest_session(sessions: list[Session]) -> Session | None:
    """专注时长最长的 session；列表为空时返回 None。"""
    return max(sessions, default=None, key=lambda s: s.focus_seconds)
