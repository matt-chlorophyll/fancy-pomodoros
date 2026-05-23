import re
from datetime import datetime

from pomo.models import KIND_FOCUS, KIND_REST, Session, new_session_id


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


def test_session_create_defaults_to_focus_kind():
    s = Session.create(
        category="工作",
        task="写文档",
        started_at=datetime(2026, 5, 22, 9, 0, 0),
        ended_at=datetime(2026, 5, 22, 9, 25, 0),
        focus_seconds=1500,
        target_seconds=1500,
    )
    assert s.kind == KIND_FOCUS


def test_session_create_accepts_rest_kind():
    s = Session.create(
        category="休息",
        task="休息",
        started_at=datetime(2026, 5, 22, 9, 25, 0),
        ended_at=datetime(2026, 5, 22, 9, 30, 0),
        focus_seconds=300,
        target_seconds=300,
        kind=KIND_REST,
    )
    assert s.kind == KIND_REST


def test_from_dict_defaults_kind_to_focus_for_legacy_records():
    # 旧 JSON 没有 kind 字段时，应当被当作 focus session。
    raw = {
        "id": "x",
        "category": "工作",
        "task": "写文档",
        "started_at": "2026-05-22T09:00:00",
        "ended_at": "2026-05-22T09:25:00",
        "focus_seconds": 1500,
        "target_seconds": 1500,
        "reached_overtime": False,
    }
    s = Session.from_dict(raw)
    assert s.kind == KIND_FOCUS


def test_to_dict_includes_kind():
    s = Session.create(
        category="休息",
        task="休息",
        started_at=datetime(2026, 5, 22, 9, 25, 0),
        ended_at=datetime(2026, 5, 22, 9, 30, 0),
        focus_seconds=300,
        target_seconds=300,
        kind=KIND_REST,
    )
    assert s.to_dict()["kind"] == KIND_REST
