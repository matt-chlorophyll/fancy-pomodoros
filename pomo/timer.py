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
