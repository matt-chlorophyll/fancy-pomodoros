# Fancy Pomodoro CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个极简优雅的命令行番茄钟 `pomo`，辅助专注（25 分钟起、可加时）并自动记录每个 session 的任务/分类/耗时供复盘。

**Architecture:** 纯逻辑模块（计时状态机、存储、聚合）与渲染层（Rich 界面）分离，CLI 层用 Typer 把两者接起来。专注画面用 Rich `Live` 原地刷新，键盘输入用 Windows `msvcrt` 非阻塞轮询。数据存为带版本号的 JSON。

**Tech Stack:** Python 3.11+，`rich`（界面），`typer`（命令），标准库 `msvcrt`（键盘），`pytest`（测试）。

**约定：**
- 每条 commit 信息结尾追加一行 trailer：`Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
- 所有测试/运行命令用虚拟环境内的解释器：`.venv/Scripts/python`（Windows）。
- 设计文档见 `docs/superpowers/specs/2026-05-22-fancy-pomodoro-cli-design.md`。

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `pyproject.toml` | 包元数据、依赖、`pomo` 入口、pytest 配置 |
| `pomo/__init__.py` | 包标识、`__version__` |
| `pomo/__main__.py` | `python -m pomo` 入口 |
| `pomo/config.py` | 数据目录解析、默认常量 |
| `pomo/models.py` | `Session` 数据类与序列化、id 生成 |
| `pomo/storage.py` | `sessions.json` 原子读写、损坏处理 |
| `pomo/timer.py` | `FocusTimer` 计时状态机（注入时钟） |
| `pomo/stats.py` | 日期过滤与分类/任务聚合 |
| `pomo/keyboard.py` | Windows 非阻塞按键读取与归一化 |
| `pomo/ui/__init__.py` | UI 子包标识 |
| `pomo/ui/format.py` | 时长格式化与进度条字符串（纯函数） |
| `pomo/ui/theme.py` | 极简优雅配色（冷/暖两套调色板） |
| `pomo/ui/countdown.py` | 专注/加时实时画面 + 结束卡片渲染 |
| `pomo/ui/prompts.py` | 分类/任务选择、3·2·1 仪式 |
| `pomo/ui/report.py` | 复盘报表渲染 |
| `pomo/cli.py` | Typer app：`start` / `report` 命令与会话主循环 |
| `tests/*` | 各纯逻辑模块的单元测试 |
| `README.md` | 安装与使用说明 |

---

## Task 1: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `pomo/__init__.py`
- Create: `pomo/ui/__init__.py`

- [ ] **Step 1: 确认 Python 版本**

Run: `python --version`
Expected: `Python 3.11.x` 或更高。若低于 3.11，先安装 3.11+ 再继续。

- [ ] **Step 2: 创建 `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "fancy-pomodoro"
version = "0.1.0"
description = "A fancy CLI pomodoro timer with time tracking"
requires-python = ">=3.11"
dependencies = [
    "rich>=13.7",
    "typer>=0.12",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
pomo = "pomo.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["pomo"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: 创建包标识文件**

`pomo/__init__.py`:
```python
"""Fancy Pomodoro CLI — 专注计时与时间记录。"""

__version__ = "0.1.0"
```

`pomo/ui/__init__.py`:
```python
"""UI 渲染层（Rich）。"""
```

- [ ] **Step 4: 创建虚拟环境并安装**

Run:
```
python -m venv .venv
.venv/Scripts/python -m pip install --upgrade pip
.venv/Scripts/python -m pip install -e ".[dev]"
```
Expected: 安装成功，结尾出现 `Successfully installed ... fancy-pomodoro-0.1.0 ...`。

- [ ] **Step 5: 验证包可导入**

Run: `.venv/Scripts/python -c "import pomo; print(pomo.__version__)"`
Expected: `0.1.0`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml pomo/__init__.py pomo/ui/__init__.py
git commit -m "chore: scaffold fancy-pomodoro package"
```

---

## Task 2: config.py — 数据目录与常量

**Files:**
- Create: `pomo/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_config.py`:
```python
from pathlib import Path

from pomo import config


def test_data_dir_uses_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    assert config.data_dir() == tmp_path


def test_data_dir_defaults_to_home(monkeypatch, tmp_path):
    monkeypatch.delenv("POMO_DATA_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert config.data_dir() == tmp_path / ".fancy-pomodoro"


def test_sessions_file_lives_under_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    assert config.sessions_file() == tmp_path / "sessions.json"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.config'`

- [ ] **Step 3: 实现 `pomo/config.py`**

```python
"""数据目录解析与全局常量。"""

import os
from pathlib import Path

DEFAULT_FOCUS_MINUTES = 25
APP_DIR_NAME = ".fancy-pomodoro"
SESSIONS_FILENAME = "sessions.json"


def data_dir() -> Path:
    """返回数据目录。环境变量 POMO_DATA_DIR 优先，否则用 home 下的应用目录。"""
    override = os.environ.get("POMO_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / APP_DIR_NAME


def sessions_file() -> Path:
    """返回 sessions.json 的完整路径。"""
    return data_dir() / SESSIONS_FILENAME
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_config.py -v`
Expected: PASS — 3 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/config.py tests/test_config.py
git commit -m "feat: add config module for data dir resolution"
```

---

## Task 3: models.py — Session 数据类

**Files:**
- Create: `pomo/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_models.py`:
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.models'`

- [ ] **Step 3: 实现 `pomo/models.py`**

```python
"""Session 数据模型与序列化。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import uuid4


def new_session_id(started_at: datetime) -> str:
    """生成时间戳前缀 + 随机后缀的唯一 id，便于肉眼浏览 JSON。"""
    return f"{started_at:%Y%m%dT%H%M%S}-{uuid4().hex[:6]}"


@dataclass
class Session:
    """一次专注 session 的记录。"""

    id: str
    category: str
    task: str
    started_at: str  # ISO8601 本地时间
    ended_at: str  # ISO8601 本地时间
    focus_seconds: int
    target_seconds: int
    reached_overtime: bool

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> "Session":
        return cls(
            id=raw["id"],
            category=raw["category"],
            task=raw["task"],
            started_at=raw["started_at"],
            ended_at=raw["ended_at"],
            focus_seconds=int(raw["focus_seconds"]),
            target_seconds=int(raw["target_seconds"]),
            reached_overtime=bool(raw["reached_overtime"]),
        )

    @classmethod
    def create(
        cls,
        *,
        category: str,
        task: str,
        started_at: datetime,
        ended_at: datetime,
        focus_seconds: float,
        target_seconds: int,
    ) -> "Session":
        """从原始计时数据构造一条 Session 记录。"""
        focus = int(focus_seconds)
        return cls(
            id=new_session_id(started_at),
            category=category,
            task=task,
            started_at=started_at.isoformat(timespec="seconds"),
            ended_at=ended_at.isoformat(timespec="seconds"),
            focus_seconds=focus,
            target_seconds=int(target_seconds),
            reached_overtime=focus >= int(target_seconds),
        )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_models.py -v`
Expected: PASS — 5 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/models.py tests/test_models.py
git commit -m "feat: add Session model with serialization"
```

---

## Task 4: storage.py — JSON 原子读写

**Files:**
- Create: `pomo/storage.py`
- Test: `tests/test_storage.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_storage.py`:
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_storage.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.storage'`

- [ ] **Step 3: 实现 `pomo/storage.py`**

```python
"""sessions.json 的原子读写与损坏处理。"""

import json
from pathlib import Path

from pomo.models import Session

SCHEMA_VERSION = 1


def _is_corrupt(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return False
    except (json.JSONDecodeError, ValueError, OSError):
        return True


def load_sessions(path: Path) -> list[Session]:
    """读取所有 session。文件不存在或损坏时返回空列表。"""
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [Session.from_dict(item) for item in raw.get("sessions", [])]
    except (json.JSONDecodeError, ValueError, KeyError, TypeError):
        return []


def save_sessions(path: Path, sessions: list[Session]) -> None:
    """原子写入全部 session。若已存在的文件损坏，先备份为 .bak。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and _is_corrupt(path):
        path.replace(path.with_name(path.name + ".bak"))
    payload = {
        "version": SCHEMA_VERSION,
        "sessions": [s.to_dict() for s in sessions],
    }
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def append_session(path: Path, session: Session) -> None:
    """追加一条 session 并落盘。"""
    sessions = load_sessions(path)
    sessions.append(session)
    save_sessions(path, sessions)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_storage.py -v`
Expected: PASS — 6 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/storage.py tests/test_storage.py
git commit -m "feat: add atomic JSON storage for sessions"
```

---

## Task 5: timer.py — 计时状态机

**Files:**
- Create: `pomo/timer.py`
- Test: `tests/test_timer.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_timer.py`:
```python
from pomo.timer import FocusTimer, Phase


class FakeClock:
    """可手动推进的假时钟，用于测试计时逻辑。"""

    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def test_new_timer_starts_in_focus_phase():
    timer = FocusTimer(target_seconds=1500, clock=FakeClock())
    assert timer.phase is Phase.FOCUS
    assert timer.remaining() == 1500
    assert timer.overtime() == 0


def test_elapsed_focus_tracks_clock():
    clock = FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(60)
    assert timer.elapsed_focus() == 60
    assert timer.remaining() == 1440


def test_crossing_target_switches_to_overtime():
    clock = FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(1501)
    assert timer.phase is Phase.OVERTIME
    assert timer.remaining() == 0
    assert timer.overtime() == 1


def test_pause_freezes_elapsed_time():
    clock = FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(100)
    timer.pause()
    assert timer.is_paused is True
    clock.advance(300)  # 暂停期间不应计入
    assert timer.elapsed_focus() == 100


def test_resume_continues_counting_without_paused_gap():
    clock = FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(100)
    timer.pause()
    clock.advance(300)
    timer.resume()
    assert timer.is_paused is False
    clock.advance(50)
    assert timer.elapsed_focus() == 150


def test_toggle_pause_flips_state():
    timer = FocusTimer(target_seconds=1500, clock=FakeClock())
    timer.toggle_pause()
    assert timer.is_paused is True
    timer.toggle_pause()
    assert timer.is_paused is False
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_timer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.timer'`

- [ ] **Step 3: 实现 `pomo/timer.py`**

```python
"""专注计时状态机。"""

import time
from enum import Enum
from typing import Callable


class Phase(Enum):
    """计时阶段。"""

    FOCUS = "focus"
    OVERTIME = "overtime"


class FocusTimer:
    """从构造时刻开始计时，跨过目标时长后进入加时阶段。

    时钟通过 ``clock`` 注入（默认 ``time.monotonic``），便于测试。
    暂停期间的时间不计入专注时长。
    """

    def __init__(
        self,
        target_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._target = target_seconds
        self._clock = clock
        self._start = clock()
        self._paused_total = 0.0
        self._pause_started_at: float | None = None

    @property
    def target_seconds(self) -> int:
        return self._target

    @property
    def is_paused(self) -> bool:
        return self._pause_started_at is not None

    def pause(self) -> None:
        if not self.is_paused:
            self._pause_started_at = self._clock()

    def resume(self) -> None:
        if self.is_paused:
            self._paused_total += self._clock() - self._pause_started_at
            self._pause_started_at = None

    def toggle_pause(self) -> None:
        if self.is_paused:
            self.resume()
        else:
            self.pause()

    def elapsed_focus(self) -> float:
        """已专注秒数（不含暂停）。"""
        now = self._clock()
        paused = self._paused_total
        if self.is_paused:
            paused += now - self._pause_started_at
        return (now - self._start) - paused

    @property
    def phase(self) -> Phase:
        return Phase.FOCUS if self.elapsed_focus() < self._target else Phase.OVERTIME

    def remaining(self) -> float:
        """专注阶段剩余秒数；加时阶段为 0。"""
        return max(0.0, self._target - self.elapsed_focus())

    def overtime(self) -> float:
        """加时阶段已超出的秒数；专注阶段为 0。"""
        return max(0.0, self.elapsed_focus() - self._target)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_timer.py -v`
Expected: PASS — 6 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/timer.py tests/test_timer.py
git commit -m "feat: add FocusTimer state machine"
```

---

## Task 6: stats.py — 日期过滤与聚合

**Files:**
- Create: `pomo/stats.py`
- Test: `tests/test_stats.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_stats.py`:
```python
from datetime import date

from pomo.models import Session
from pomo.stats import (
    aggregate_by_category,
    longest_session,
    sessions_in_week,
    sessions_on_date,
    total_focus_seconds,
    week_bounds,
)


def _session(task: str, category: str, day: str, focus: int) -> Session:
    return Session(
        id="id-" + task,
        category=category,
        task=task,
        started_at=f"{day}T09:00:00",
        ended_at=f"{day}T09:30:00",
        focus_seconds=focus,
        target_seconds=1500,
        reached_overtime=focus >= 1500,
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_stats.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.stats'`

- [ ] **Step 3: 实现 `pomo/stats.py`**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_stats.py -v`
Expected: PASS — 7 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/stats.py tests/test_stats.py
git commit -m "feat: add stats aggregation module"
```

---

## Task 7: UI 基础 — 格式化与配色

**Files:**
- Create: `pomo/ui/format.py`
- Create: `pomo/ui/theme.py`
- Test: `tests/test_format.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_format.py`:
```python
from pomo.timer import Phase
from pomo.ui.format import format_clock, format_minutes, format_span, progress_bar
from pomo.ui.theme import FOCUS, OVERTIME, palette_for


def test_format_clock_pads_minutes_and_seconds():
    assert format_clock(0) == "00:00"
    assert format_clock(65) == "01:05"
    assert format_clock(1500) == "25:00"


def test_format_clock_allows_minutes_over_sixty():
    assert format_clock(3725) == "62:05"


def test_format_span_is_hours_colon_minutes():
    assert format_span(0) == "0:00"
    assert format_span(2100) == "0:35"
    assert format_span(9000) == "2:30"


def test_format_minutes_text():
    assert format_minutes(3120) == "52 分钟"


def test_progress_bar_fills_proportionally():
    assert progress_bar(0.0, width=10) == "░░░░░░░░░░"
    assert progress_bar(1.0, width=10) == "██████████"
    assert progress_bar(0.5, width=10) == "█████░░░░░"


def test_progress_bar_clamps_out_of_range():
    assert progress_bar(-1.0, width=4) == "░░░░"
    assert progress_bar(2.0, width=4) == "████"


def test_palette_for_phase():
    assert palette_for(Phase.FOCUS) is FOCUS
    assert palette_for(Phase.OVERTIME) is OVERTIME
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_format.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.ui.format'`

- [ ] **Step 3: 实现 `pomo/ui/format.py`**

```python
"""时长格式化与进度条字符串（纯函数）。"""


def format_clock(seconds: float) -> str:
    """秒数 -> 'MM:SS'，用于倒计时显示。分钟可超过 60。"""
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def format_span(seconds: float) -> str:
    """秒数 -> 'H:MM'，用于报表里的累计时长。"""
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    return f"{hours}:{rem // 60:02d}"


def format_minutes(seconds: float) -> str:
    """秒数 -> 'N 分钟'。"""
    return f"{int(seconds) // 60} 分钟"


def progress_bar(
    fraction: float,
    width: int = 22,
    fill: str = "█",
    empty: str = "░",
) -> str:
    """按比例生成进度条字符串。fraction 超出 [0, 1] 会被夹紧。"""
    fraction = max(0.0, min(1.0, fraction))
    filled = round(fraction * width)
    return fill * filled + empty * (width - filled)
```

- [ ] **Step 4: 实现 `pomo/ui/theme.py`**

```python
"""极简优雅配色：专注阶段冷色，加时阶段暖色。"""

from dataclasses import dataclass

from pomo.timer import Phase


@dataclass(frozen=True)
class Palette:
    """一套配色。值为 Rich 可识别的颜色字符串。"""

    accent: str  # 倒计时数字、进度条
    label: str  # 任务·分类标题
    dim: str  # 次要文字、边框


# Nord 风格：冷静的青蓝 / 温暖的琥珀。
FOCUS = Palette(accent="#88C0D0", label="#E5E9F0", dim="#4C566A")
OVERTIME = Palette(accent="#EBCB8B", label="#E5E9F0", dim="#4C566A")


def palette_for(phase: Phase) -> Palette:
    """根据计时阶段选择配色。"""
    return OVERTIME if phase is Phase.OVERTIME else FOCUS
```

- [ ] **Step 5: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_format.py -v`
Expected: PASS — 7 passed

- [ ] **Step 6: Commit**

```bash
git add pomo/ui/format.py pomo/ui/theme.py tests/test_format.py
git commit -m "feat: add UI formatting helpers and color palettes"
```

---

## Task 8: keyboard.py — 非阻塞按键

**Files:**
- Create: `pomo/keyboard.py`
- Test: `tests/test_keyboard.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_keyboard.py`:
```python
from pomo.keyboard import KEY_ENTER, KEY_ESC, KEY_SPACE, normalize_key


def test_normalize_space():
    assert normalize_key(" ") == KEY_SPACE


def test_normalize_enter_variants():
    assert normalize_key("\r") == KEY_ENTER
    assert normalize_key("\n") == KEY_ENTER


def test_normalize_escape():
    assert normalize_key("\x1b") == KEY_ESC


def test_normalize_letter_is_lowercased():
    assert normalize_key("S") == "s"
    assert normalize_key("q") == "q"


def test_normalize_non_printable_returns_none():
    assert normalize_key("\x00") is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_keyboard.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.keyboard'`

- [ ] **Step 3: 实现 `pomo/keyboard.py`**

```python
"""Windows 终端非阻塞按键读取。

非 Windows 平台需另行实现 read_key（例如基于 termios），
归一化逻辑 normalize_key 与平台无关。
"""

import msvcrt

KEY_SPACE = "space"
KEY_ENTER = "enter"
KEY_ESC = "esc"

# 方向键/功能键在 msvcrt 下以这两个字节作为前缀。
_PREFIX = ("\x00", "\xe0")


def normalize_key(ch: str) -> str | None:
    """把单个原始字符归一化为按键名；无法识别时返回 None。"""
    if ch == " ":
        return KEY_SPACE
    if ch in ("\r", "\n"):
        return KEY_ENTER
    if ch == "\x1b":
        return KEY_ESC
    if ch.isprintable():
        return ch.lower()
    return None


def read_key() -> str | None:
    """非阻塞读取一个按键。无按键时返回 None。"""
    if not msvcrt.kbhit():
        return None
    ch = msvcrt.getwch()
    if ch in _PREFIX:
        msvcrt.getwch()  # 消费功能键的第二个字节
        return None
    return normalize_key(ch)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_keyboard.py -v`
Expected: PASS — 5 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/keyboard.py tests/test_keyboard.py
git commit -m "feat: add non-blocking keyboard input"
```

---

## Task 9: ui/countdown.py — 专注画面与结束卡片

**Files:**
- Create: `pomo/ui/countdown.py`
- Test: `tests/test_countdown.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_countdown.py`:
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_countdown.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.ui.countdown'`

- [ ] **Step 3: 实现 `pomo/ui/countdown.py`**

```python
"""专注/加时实时画面与 session 结束卡片的渲染。"""

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pomo.models import Session
from pomo.timer import FocusTimer, Phase
from pomo.ui.format import format_clock, format_minutes, format_span, progress_bar
from pomo.ui.theme import FOCUS, palette_for

ENCOURAGEMENTS = [
    "保持专注，你做得很好",
    "一次只做一件事",
    "深呼吸，继续",
    "此刻就是最好的时机",
    "专注是一种温柔的力量",
]

_KEYS_HINT = "空格 暂停 / 继续      s 完成      Esc 放弃"


def _spaced(text: str) -> str:
    """'25:00' -> '2 5 : 0 0'，营造极简的大号数字感。"""
    return " ".join(text)


def render_focus(
    category: str,
    task: str,
    timer: FocusTimer,
    encouragement: str,
) -> RenderableType:
    """渲染一帧专注/加时画面。"""
    phase = timer.phase
    pal = palette_for(phase)

    if phase is Phase.FOCUS:
        clock_text = format_clock(timer.remaining())
        fraction = (
            timer.elapsed_focus() / timer.target_seconds
            if timer.target_seconds
            else 1.0
        )
    else:
        clock_text = "+" + format_clock(timer.overtime())
        fraction = 1.0

    label = Text(f"{task} · {category}", style=pal.label, justify="center")

    big = Text(_spaced(clock_text), style=f"bold {pal.accent}", justify="center")
    panel = Panel(big, border_style=pal.dim, padding=(1, 4), expand=False)

    pct = int(min(1.0, max(0.0, fraction)) * 100)
    bar = Text(
        f"{progress_bar(fraction)}  {pct}%",
        style=pal.accent,
        justify="center",
    )

    if timer.is_paused:
        status_text = "⏸  已暂停"
    elif phase is Phase.OVERTIME:
        status_text = "加时中 · 做完按 s 收尾"
    else:
        status_text = f"· {encouragement} ·"
    status = Text(status_text, style=pal.dim, justify="center")

    keys = Text(_KEYS_HINT, style=pal.dim, justify="center")

    group = Group(
        label,
        Text(""),
        Align.center(panel),
        Text(""),
        bar,
        Text(""),
        status,
        Text(""),
        keys,
    )
    return Align.center(group)


def render_summary(
    session: Session,
    today_total_seconds: int,
    today_category_rows: list[tuple[str, int, int]],
) -> RenderableType:
    """渲染 session 结束卡片。"""
    pal = FOCUS

    head = Text(justify="left")
    head.append("✓ 本次  ", style=f"bold {pal.accent}")
    head.append(f"{session.task} · {session.category}", style=pal.label)

    dur_text = f"  专注 {format_minutes(session.focus_seconds)}"
    if session.reached_overtime:
        dur_text += "（含加时）"
    dur = Text(dur_text, style=pal.label)

    total = Text(
        f"  今日累计  {format_span(today_total_seconds)}",
        style=f"bold {pal.accent}",
    )

    breakdown = Table.grid(padding=(0, 2))
    breakdown.add_column()
    breakdown.add_column()
    breakdown.add_column()
    for cat, secs, count in today_category_rows:
        breakdown.add_row(
            Text(f"  {cat}", style=pal.dim),
            Text(format_span(secs), style=pal.dim),
            Text(f"· {count} 个", style=pal.dim),
        )

    body = Group(
        head,
        dur,
        Text(""),
        total,
        Text(""),
        breakdown,
        Text(""),
        Text("  好好休息一下 ☕", style=pal.dim),
    )
    return Panel(
        body,
        title="session 完成",
        border_style=pal.dim,
        padding=(1, 3),
        expand=False,
    )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_countdown.py -v`
Expected: PASS — 4 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/ui/countdown.py tests/test_countdown.py
git commit -m "feat: add focus screen and summary card rendering"
```

---

## Task 10: ui/prompts.py — 分类/任务选择与仪式

**Files:**
- Create: `pomo/ui/prompts.py`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_prompts.py`:
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_prompts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.ui.prompts'`

- [ ] **Step 3: 实现 `pomo/ui/prompts.py`**

```python
"""会话开始前的交互：分类选择、任务输入、3·2·1 仪式。"""

import time

from rich.align import Align
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text

from pomo.models import Session


def known_categories(sessions: list[Session]) -> list[str]:
    """历史出现过的分类，最近使用的在前，去重。"""
    seen: list[str] = []
    for s in reversed(sessions):
        if s.category not in seen:
            seen.append(s.category)
    return seen


def recent_tasks(
    sessions: list[Session],
    category: str,
    limit: int = 5,
) -> list[str]:
    """指定分类下最近用过的任务名，最近的在前，去重，最多 limit 个。"""
    seen: list[str] = []
    for s in reversed(sessions):
        if s.category == category and s.task not in seen:
            seen.append(s.task)
            if len(seen) >= limit:
                break
    return seen


def _pick_from_list(console: Console, prompt: str, options: list[str]) -> str:
    """展示编号选项，让用户输入编号选择，或直接输入新值。空输入会重问。"""
    for i, opt in enumerate(options, 1):
        console.print(f"  [cyan]{i}[/cyan]  {opt}")
    if options:
        console.print("  [dim]或直接输入一个新的[/dim]")
    while True:
        raw = Prompt.ask(prompt).strip()
        if raw.isdigit() and options and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw:
            return raw


def pick_category(console: Console, sessions: list[Session]) -> str:
    """选择或输入一个分类。"""
    console.print("[dim]选择分类：[/dim]")
    return _pick_from_list(console, "分类", known_categories(sessions))


def pick_task(console: Console, sessions: list[Session], category: str) -> str:
    """选择或输入这次要做的任务。"""
    console.print(f"[dim]这次在「{category}」里做什么？[/dim]")
    return _pick_from_list(console, "任务", recent_tasks(sessions, category))


def ready_ritual(console: Console) -> None:
    """开始前约 3.5 秒的 3·2·1 仪式。"""
    console.print()
    for n in ("3", "2", "1"):
        console.print(Align.center(Text(n, style="bold cyan")))
        time.sleep(0.7)
    console.print(Align.center(Text("开始 ·", style="dim")))
    time.sleep(0.5)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_prompts.py -v`
Expected: PASS — 5 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/ui/prompts.py tests/test_prompts.py
git commit -m "feat: add category/task prompts and ready ritual"
```

---

## Task 11: ui/report.py — 复盘报表渲染

**Files:**
- Create: `pomo/ui/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_report.py`:
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.ui.report'`

- [ ] **Step 3: 实现 `pomo/ui/report.py`**

```python
"""复盘报表渲染。"""

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pomo.models import Session
from pomo.stats import aggregate_by_category, longest_session, total_focus_seconds
from pomo.ui.format import format_minutes, format_span, progress_bar
from pomo.ui.theme import FOCUS


def build_report(title: str, sessions: list[Session]) -> RenderableType:
    """根据一组 session 构建报表面板。"""
    pal = FOCUS

    if not sessions:
        empty = Text(
            "这段时间还没有记录。开一次 pomo 吧。",
            style=pal.dim,
            justify="center",
        )
        return Panel(
            empty,
            title=title,
            border_style=pal.dim,
            padding=(1, 3),
            expand=False,
        )

    total = total_focus_seconds(sessions)
    rows = aggregate_by_category(sessions)
    max_secs = max(secs for _, secs, _ in rows)
    longest = longest_session(sessions)

    header = Text()
    header.append(title, style=f"bold {pal.label}")
    header.append(f"        总计 {format_span(total)}", style=f"bold {pal.accent}")

    grid = Table.grid(padding=(0, 2))
    grid.add_column()  # 分类
    grid.add_column()  # 条形图
    grid.add_column()  # 时长 · session 数
    for cat, secs, count in rows:
        bar = progress_bar(secs / max_secs if max_secs else 0.0, width=22)
        grid.add_row(
            Text(cat, style=pal.label),
            Text(bar, style=pal.accent),
            Text(f"{format_span(secs)}  · {count} 个 session", style=pal.dim),
        )

    longest_line = Text(
        f"最长一段   {longest.task} · {longest.category} · "
        f"{format_minutes(longest.focus_seconds)}",
        style=pal.dim,
    )

    body = Group(header, Text(""), grid, Text(""), longest_line)
    return Panel(body, border_style=pal.dim, padding=(1, 2), expand=False)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_report.py -v`
Expected: PASS — 3 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/ui/report.py tests/test_report.py
git commit -m "feat: add report rendering"
```

---

## Task 12: cli.py — report 命令

**Files:**
- Create: `pomo/cli.py`
- Test: `tests/test_cli_report.py`

- [ ] **Step 1: 写失败的测试**

`tests/test_cli_report.py`:
```python
from datetime import datetime

from typer.testing import CliRunner

from pomo.cli import app
from pomo.models import Session
from pomo.storage import append_session


def test_report_empty_state(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["report"])
    assert result.exit_code == 0
    assert "还没有记录" in result.output


def test_report_shows_seeded_session(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    now = datetime.now()
    session = Session(
        id="x",
        category="工作",
        task="写文档",
        started_at=now.isoformat(timespec="seconds"),
        ended_at=now.isoformat(timespec="seconds"),
        focus_seconds=1500,
        target_seconds=1500,
        reached_overtime=False,
    )
    append_session(tmp_path / "sessions.json", session)
    result = CliRunner().invoke(app, ["report"])
    assert result.exit_code == 0
    assert "工作" in result.output


def test_report_rejects_bad_date(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["report", "--date", "not-a-date"])
    assert result.exit_code == 1
    assert "日期格式无效" in result.output
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv/Scripts/python -m pytest tests/test_cli_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pomo.cli'`

- [ ] **Step 3: 实现 `pomo/cli.py`**

> 本任务只实现 `report` 命令与共用的 Typer app。`start` 命令在 Task 13 追加。

```python
"""Typer CLI：start / report 命令。"""

from datetime import date as date_cls
from datetime import datetime

import typer
from rich.console import Console

from pomo.config import sessions_file
from pomo.stats import sessions_in_week, sessions_on_date
from pomo.storage import load_sessions
from pomo.ui.report import build_report

app = typer.Typer(add_completion=False, help="Fancy Pomodoro — 专注计时与时间记录。")


def show_report(target_day: date_cls, week: bool) -> None:
    """渲染并打印复盘报表。"""
    console = Console()
    sessions = load_sessions(sessions_file())
    if week:
        scope = sessions_in_week(sessions, target_day)
        title = f"{target_day.isoformat()} 所在周  本周复盘"
    else:
        scope = sessions_on_date(sessions, target_day)
        title = f"{target_day.isoformat()}  当日复盘"
    console.print()
    console.print(build_report(title, scope))
    console.print()


@app.command()
def report(
    week: bool = typer.Option(False, "--week", help="查看本周（周一至周日）。"),
    date: str = typer.Option(
        None, "--date", help="查看指定日，格式 YYYY-MM-DD。"
    ),
) -> None:
    """查看专注复盘报表（默认今天）。"""
    if date:
        try:
            target = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            typer.echo(f"日期格式无效：{date}（应为 YYYY-MM-DD）")
            raise typer.Exit(code=1)
    else:
        target = date_cls.today()
    show_report(target, week)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.venv/Scripts/python -m pytest tests/test_cli_report.py -v`
Expected: PASS — 3 passed

- [ ] **Step 5: Commit**

```bash
git add pomo/cli.py tests/test_cli_report.py
git commit -m "feat: add report CLI command"
```

---

## Task 13: cli.py — start 命令与会话主循环

**Files:**
- Modify: `pomo/cli.py`
- Create: `pomo/__main__.py`

- [ ] **Step 1: 在 `pomo/cli.py` 顶部补充 import**

把文件开头的 import 段替换为：

```python
"""Typer CLI：start / report 命令。"""

import random
import time
from datetime import date as date_cls
from datetime import datetime

import typer
from rich.console import Console
from rich.live import Live
from rich.prompt import Confirm

from pomo.config import DEFAULT_FOCUS_MINUTES, sessions_file
from pomo.keyboard import KEY_ENTER, KEY_ESC, KEY_SPACE, read_key
from pomo.models import Session
from pomo.stats import aggregate_by_category, sessions_in_week, sessions_on_date, total_focus_seconds
from pomo.storage import append_session, load_sessions
from pomo.timer import FocusTimer, Phase
from pomo.ui.countdown import ENCOURAGEMENTS, render_focus, render_summary
from pomo.ui.prompts import pick_category, pick_task, ready_ritual
from pomo.ui.report import build_report
```

- [ ] **Step 2: 在 `pomo/cli.py` 末尾追加会话主循环与 start 命令**

```python
def _countdown_loop(
    console: Console,
    category: str,
    task: str,
    timer: FocusTimer,
    encouragement: str,
) -> str:
    """运行实时倒计时画面。返回 'finished' 或 'abandoned'。"""
    belled = False
    with Live(
        render_focus(category, task, timer, encouragement),
        console=console,
        transient=True,
        refresh_per_second=8,
    ) as live:
        try:
            while True:
                key = read_key()
                if key == KEY_SPACE:
                    timer.toggle_pause()
                elif key in (KEY_ENTER, "s"):
                    return "finished"
                elif key == KEY_ESC:
                    live.stop()
                    timer.pause()
                    if Confirm.ask("确定放弃本次吗？将不会记录", default=False):
                        return "abandoned"
                    timer.resume()
                    live.start()
                if not belled and timer.phase is Phase.OVERTIME:
                    console.bell()
                    belled = True
                live.update(render_focus(category, task, timer, encouragement))
                time.sleep(0.2)
        except KeyboardInterrupt:
            return "finished"


def run_session(minutes: int) -> None:
    """完整跑一次专注 session：选任务 → 计时 → 记录 → 小结。"""
    console = Console()
    path = sessions_file()
    sessions = load_sessions(path)

    category = pick_category(console, sessions)
    task = pick_task(console, sessions, category)
    ready_ritual(console)

    started_at = datetime.now()
    timer = FocusTimer(target_seconds=minutes * 60)
    encouragement = random.choice(ENCOURAGEMENTS)

    outcome = _countdown_loop(console, category, task, timer, encouragement)
    ended_at = datetime.now()

    if outcome == "abandoned":
        console.print("[dim]已放弃本次，未记录。[/dim]")
        return

    session = Session.create(
        category=category,
        task=task,
        started_at=started_at,
        ended_at=ended_at,
        focus_seconds=timer.elapsed_focus(),
        target_seconds=minutes * 60,
    )
    append_session(path, session)

    today = sessions_on_date(load_sessions(path), started_at.date())
    console.print()
    console.print(
        render_summary(
            session,
            total_focus_seconds(today),
            aggregate_by_category(today),
        )
    )
    console.print()


@app.command()
def start(
    minutes: int = typer.Option(
        DEFAULT_FOCUS_MINUTES, "--minutes", "-m", help="本次专注目标时长（分钟）。"
    ),
) -> None:
    """开一次专注 session。"""
    run_session(minutes)


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    """不带子命令时直接开始一次默认时长的 session。"""
    if ctx.invoked_subcommand is None:
        run_session(DEFAULT_FOCUS_MINUTES)
```

- [ ] **Step 3: 创建 `pomo/__main__.py`**

```python
"""支持 `python -m pomo`。"""

from pomo.cli import app

if __name__ == "__main__":
    app()
```

- [ ] **Step 4: 跑完整测试套件确认无回归**

Run: `.venv/Scripts/python -m pytest -v`
Expected: PASS — 全部通过（约 44 项）。

- [ ] **Step 5: 手动冒烟测试 — 命令可用**

Run: `.venv/Scripts/pomo --help`
Expected: 显示 `start` 与 `report` 两个命令。

Run: `.venv/Scripts/python -m pomo --help`
Expected: 同上。

- [ ] **Step 6: 手动冒烟测试 — 完整跑一次 session**

Run: `.venv/Scripts/pomo start --minutes 1`

逐项确认：
- [ ] 提示选择分类，输入一个新分类（如「测试」）后回车。
- [ ] 提示输入任务名，输入（如「冒烟测试」）后回车。
- [ ] 出现 3 · 2 · 1 仪式。
- [ ] 进入倒计时画面：任务·分类标题、`0 1 : 0 0` 风格大号数字、进度条、鼓励语、底部按键提示。
- [ ] 按 `空格` 能暂停（显示「已暂停」）再按恢复。
- [ ] 等约 1 分钟到点：终端响一声，配色转暖，数字变为 `+0 0 : 0x` 加时正计时。
- [ ] 按 `s` 结束：出现结束卡片，含本次时长、今日累计、分类分布。

Run: `.venv/Scripts/pomo report`
Expected: 看到刚才那次 session 出现在「当日复盘」里。

- [ ] **Step 7: 手动冒烟测试 — 放弃流程**

Run: `.venv/Scripts/pomo start --minutes 1`，选完任务后在倒计时画面按 `Esc`。
Expected: 出现「确定放弃本次吗？」确认；输入 `n` 能恢复倒计时，输入 `y` 则提示「已放弃本次，未记录」且 `pomo report` 不增加记录。

- [ ] **Step 8: Commit**

```bash
git add pomo/cli.py pomo/__main__.py
git commit -m "feat: add start command with live countdown session"
```

---

## Task 14: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建 `README.md`**

```markdown
# Fancy Pomodoro

一个极简优雅的命令行番茄钟，辅助专注并自动记录时间花费。

## 安装

需要 Python 3.11+。

\`\`\`
python -m venv .venv
.venv/Scripts/python -m pip install -e .
\`\`\`

安装后 `pomo` 命令位于 `.venv/Scripts/`。把该目录加入 PATH，或用
`pipx install .` 全局安装，即可在任意目录直接敲 `pomo`。

## 使用

\`\`\`
pomo                     # 开一次 25 分钟专注 session
pomo start --minutes 50  # 自定义目标时长
pomo report              # 今日复盘
pomo report --week       # 本周复盘
pomo report --date 2026-05-20
\`\`\`

session 进行中：`空格` 暂停/继续，`s` 完成并记录，`Esc` 放弃。
25 分钟到点后无缝转入加时正计时，做完按 `s` 收尾。

## 数据

每次 session 记录到 `~/.fancy-pomodoro/sessions.json`（人类可读的 JSON）。
可用环境变量 `POMO_DATA_DIR` 改变存储目录。

## 开发

\`\`\`
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest
\`\`\`

设计与实现文档见 `docs/superpowers/`。
\`\`\`

> 注意：上面代码块里的 `\`\`\`` 是为了在本计划文档中转义；写入 README.md 时应是正常的三反引号代码围栏。

- [ ] **Step 2: 验证全套测试仍通过**

Run: `.venv/Scripts/python -m pytest`
Expected: PASS — 全部通过。

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## 自查结果

**Spec 覆盖：** 已逐节核对设计文档——CLI 命令（Task 12/13）、加时 session 生命周期与按键（Task 13）、`FocusTimer` 状态机（Task 5）、Session 数据模型与存储（Task 3/4）、`report` 报表（Task 11/12）、极简优雅界面与冷暖配色（Task 7/9）、错误处理（损坏文件 Task 4、放弃二次确认与 `Ctrl-C` Task 13、无记录空状态 Task 11）、测试策略（各 Task 的 TDD 步骤）。无遗漏。

**占位符扫描：** 无 TBD/TODO；每个步骤都含完整代码与确切命令。

**类型一致性：** `Session`、`FocusTimer`/`Phase`、`Palette`、各 `format_*`/`progress_bar`、`read_key`/`KEY_*`、`render_focus`/`render_summary`/`build_report`、`run_session`/`show_report` 的签名在定义与调用处一致。`pomo/cli.py` 跨 Task 12（report）与 Task 13（start）增量构建，Task 13 Step 1 明确给出最终 import 段以避免缺漏。
