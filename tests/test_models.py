import re
from datetime import datetime

from pomo.models import Session, new_session_id


def test_session_roundtrip():
    s = Session(
        id="x",
        category="工作",
        task="写文档",
        started_at="2026-05-22T09:00:00",
        ended_at="2026-05-22T09:28:00",
        focus_seconds=1680,
        target_seconds=1500,
        reached_overtime=True,
    )
    assert Session.from_dict(s.to_dict()) == s


def test_new_session_id_has_timestamp_prefix():
    sid = new_session_id(datetime(2026, 5, 22, 9, 0, 0))
    assert sid.startswith("20260522T090000")
    assert re.fullmatch(r"20260522T090000-[0-9a-f]{6}", sid)


def test_new_session_id_is_unique():
    dt = datetime(2026, 5, 22, 9, 0, 0)
    assert new_session_id(dt) != new_session_id(dt)


def test_session_create_marks_overtime_when_focus_exceeds_target():
    s = Session.create(
        category="工作",
        task="写文档",
        started_at=datetime(2026, 5, 22, 9, 0, 0),
        ended_at=datetime(2026, 5, 22, 9, 30, 0),
        focus_seconds=1800,
        target_seconds=1500,
    )
    assert s.reached_overtime is True
    assert s.focus_seconds == 1800
    assert s.started_at == "2026-05-22T09:00:00"


def test_session_create_no_overtime_when_under_target():
    s = Session.create(
        category="学习",
        task="读论文",
        started_at=datetime(2026, 5, 22, 9, 0, 0),
        ended_at=datetime(2026, 5, 22, 9, 10, 0),
        focus_seconds=600,
        target_seconds=1500,
    )
    assert s.reached_overtime is False


def test_session_create_truncates_fractional_focus_seconds():
    s = Session.create(
        category="工作",
        task="写文档",
        started_at=datetime(2026, 5, 22, 9, 0, 0),
        ended_at=datetime(2026, 5, 22, 9, 25, 0),
        focus_seconds=1499.9,
        target_seconds=1500,
    )
    assert s.focus_seconds == 1499
    assert s.reached_overtime is False


def test_session_create_id_matches_timestamp_format():
    s = Session.create(
        category="工作",
        task="写文档",
        started_at=datetime(2026, 5, 22, 9, 0, 0),
        ended_at=datetime(2026, 5, 22, 9, 25, 0),
        focus_seconds=1500,
        target_seconds=1500,
    )
    assert re.fullmatch(r"20260522T090000-[0-9a-f]{6}", s.id)
