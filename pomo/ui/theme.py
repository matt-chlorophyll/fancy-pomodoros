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
