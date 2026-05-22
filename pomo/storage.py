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
