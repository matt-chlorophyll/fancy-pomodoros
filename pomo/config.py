"""数据目录解析与全局常量。"""

import os
from pathlib import Path

DEFAULT_FOCUS_MINUTES = 25
DEFAULT_REST_MINUTES = 5
SUPERFOCUS_MIN_MINUTES = 25
APP_DIR_NAME = ".fancy-pomodoro"
SESSIONS_FILENAME = "sessions.json"
RATINGS_FILENAME = "ratings.json"


def data_dir() -> Path:
    """返回数据目录。

    环境变量 POMO_DATA_DIR 指向非空路径时优先使用；未设置或为空字符串时，
    回退到 home 目录下的 .fancy-pomodoro。
    """
    override = os.environ.get("POMO_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / APP_DIR_NAME


def sessions_file() -> Path:
    """返回 sessions.json 的完整路径。"""
    return data_dir() / SESSIONS_FILENAME


def ratings_file() -> Path:
    """返回 ratings.json 的完整路径。"""
    return data_dir() / RATINGS_FILENAME
