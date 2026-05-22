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
