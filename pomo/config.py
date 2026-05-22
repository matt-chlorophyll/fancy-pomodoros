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
