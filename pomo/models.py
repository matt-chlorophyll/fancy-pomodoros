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
