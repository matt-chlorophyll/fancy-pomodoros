"""极简优雅配色：

focus 专注时冷色，加时变绿（专注得更久是好事）；
rest 休息时暖色，加时变红（休息超时该回来工作了）。
"""

from dataclasses import dataclass

from pomo.models import KIND_FOCUS, KIND_REST
from pomo.timer import Phase


@dataclass(frozen=True)
class Palette:
    """一套配色。值为 Rich 可识别的颜色字符串。"""

    accent: str  # 倒计时数字、进度条
    label: str  # 任务·分类标题
    dim: str  # 次要文字、边框


# Nord 风格调色板。
FOCUS = Palette(accent="#88C0D0", label="#E5E9F0", dim="#4C566A")
FOCUS_OVERTIME = Palette(accent="#A3BE8C", label="#E5E9F0", dim="#4C566A")
REST = Palette(accent="#EBCB8B", label="#E5E9F0", dim="#4C566A")
REST_OVERTIME = Palette(accent="#BF616A", label="#E5E9F0", dim="#4C566A")

# 向后兼容：旧名字 OVERTIME 指向 focus 加时配色。
OVERTIME = FOCUS_OVERTIME


def palette_for(phase: Phase, kind: str = KIND_FOCUS) -> Palette:
    """根据计时阶段与 session 类型选择配色。"""
    if kind == KIND_REST:
        return REST_OVERTIME if phase is Phase.OVERTIME else REST
    return FOCUS_OVERTIME if phase is Phase.OVERTIME else FOCUS
