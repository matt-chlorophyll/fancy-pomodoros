from pomo.models import Session
from pomo.storage import append_session, load_sessions, save_sessions


def _sample(task: str = "写文档") -> Session:
    return Session(
        id="id-" + task,
        category="工作",
        task=task,
        started_at="2026-05-22T09:00:00",
        ended_at="2026-05-22T09:28:00",
        focus_seconds=1680,
        target_seconds=1500,
        reached_overtime=True,
    )


def test_load_missing_file_returns_empty(tmp_path):
    assert load_sessions(tmp_path / "sessions.json") == []


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "sessions.json"
    save_sessions(path, [_sample("a"), _sample("b")])
    loaded = load_sessions(path)
    assert [s.task for s in loaded] == ["a", "b"]


def test_save_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "sessions.json"
    save_sessions(path, [_sample()])
    assert path.exists()


def test_append_adds_one_session(tmp_path):
    path = tmp_path / "sessions.json"
    append_session(path, _sample("first"))
    append_session(path, _sample("second"))
    assert [s.task for s in load_sessions(path)] == ["first", "second"]


def test_load_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text("{ this is not valid json", encoding="utf-8")
    assert load_sessions(path) == []


def test_save_backs_up_corrupt_file(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text("{ corrupt", encoding="utf-8")
    save_sessions(path, [_sample("new")])
    backup = tmp_path / "sessions.json.bak"
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "{ corrupt"
    assert [s.task for s in load_sessions(path)] == ["new"]


def test_load_unreadable_path_returns_empty(tmp_path):
    # 会话路径意外是一个目录 -> 不应崩溃，返回空列表。
    path = tmp_path / "sessions.json"
    path.mkdir()
    assert load_sessions(path) == []
