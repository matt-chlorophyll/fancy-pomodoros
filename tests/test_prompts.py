from pomo.models import Session
from pomo.ui.prompts import known_categories, recent_tasks


def _session(task: str, category: str) -> Session:
    return Session(
        id="id-" + task,
        category=category,
        task=task,
        started_at="2026-05-22T09:00:00",
        ended_at="2026-05-22T09:28:00",
        focus_seconds=1500,
        target_seconds=1500,
        reached_overtime=False,
    )


def test_known_categories_most_recent_first_no_dupes():
    # sessions 按时间正序存储；最近的在末尾。
    sessions = [
        _session("a", "工作"),
        _session("b", "学习"),
        _session("c", "工作"),
    ]
    assert known_categories(sessions) == ["工作", "学习"]


def test_known_categories_empty():
    assert known_categories([]) == []


def test_recent_tasks_filters_by_category_most_recent_first():
    sessions = [
        _session("写文档", "工作"),
        _session("读论文", "学习"),
        _session("写代码", "工作"),
    ]
    assert recent_tasks(sessions, "工作") == ["写代码", "写文档"]


def test_recent_tasks_respects_limit():
    sessions = [_session(f"t{i}", "工作") for i in range(10)]
    assert recent_tasks(sessions, "工作", limit=3) == ["t9", "t8", "t7"]


def test_recent_tasks_dedupes():
    sessions = [
        _session("写文档", "工作"),
        _session("写文档", "工作"),
    ]
    assert recent_tasks(sessions, "工作") == ["写文档"]
