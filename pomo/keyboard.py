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
