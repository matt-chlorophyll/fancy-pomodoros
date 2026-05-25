"""每日整体满意度评分的模型与读写。

每条 Rating 是 (日期, 1-5 分, 可选 comment, 记录时刻)。
当天重复评分会覆盖前一次。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date as date_cls
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1


@dataclass
class Rating:
    """对某一天的整体满意度评分。"""

    date: str  # YYYY-MM-DD
    score: int  # 1-5
    comment: str
    recorded_at: str  # ISO8601 本地时间

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> "Rating":
        return cls(
            date=str(raw["date"]),
            score=int(raw["score"]),
            comment=str(raw.get("comment", "")),
            recorded_at=str(raw["recorded_at"]),
        )

    @classmethod
    def create(
        cls, *, day: date_cls, score: int, comment: str, now: datetime
    ) -> "Rating":
        return cls(
            date=day.isoformat(),
            score=int(score),
            comment=comment,
            recorded_at=now.isoformat(timespec="seconds"),
        )


def _is_corrupt(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return False
    except (json.JSONDecodeError, ValueError, OSError):
        return True


def load_ratings(path: Path) -> list[Rating]:
    """读取所有 rating。文件不存在或损坏时返回空列表。"""
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [Rating.from_dict(item) for item in raw.get("ratings", [])]
    except (json.JSONDecodeError, ValueError, KeyError, TypeError, OSError, AttributeError):
        return []


def save_ratings(path: Path, ratings: list[Rating]) -> None:
    """原子写入全部 rating。若已存在的文件损坏，先备份为 .bak。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and _is_corrupt(path):
        path.replace(path.with_name(path.name + ".bak"))
    payload = {
        "version": SCHEMA_VERSION,
        "ratings": [r.to_dict() for r in ratings],
    }
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def upsert_rating(path: Path, rating: Rating) -> None:
    """写入一条 rating，同一天已有记录则覆盖。"""
    existing = [r for r in load_ratings(path) if r.date != rating.date]
    existing.append(rating)
    save_ratings(path, existing)


def rating_for_date(ratings: list[Rating], day: date_cls) -> Rating | None:
    """返回指定日期的 rating，没有则 None。"""
    target = day.isoformat()
    for r in ratings:
        if r.date == target:
            return r
    return None


def ratings_in_range(
    ratings: list[Rating], start: date_cls, end: date_cls
) -> list[Rating]:
    """返回 [start, end] 区间内的 rating，按日期升序。"""
    s, e = start.isoformat(), end.isoformat()
    inside = [r for r in ratings if s <= r.date <= e]
    return sorted(inside, key=lambda r: r.date)
