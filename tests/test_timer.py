from pomo.timer import FocusTimer, Phase


class FakeClock:
    """可手动推进的假时钟，用于测试计时逻辑。"""

    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def test_new_timer_starts_in_focus_phase():
    timer = FocusTimer(target_seconds=1500, clock=FakeClock())
    assert timer.phase is Phase.FOCUS
    assert timer.remaining() == 1500
    assert timer.overtime() == 0


def test_elapsed_focus_tracks_clock():
    clock = FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(60)
    assert timer.elapsed_focus() == 60
    assert timer.remaining() == 1440


def test_crossing_target_switches_to_overtime():
    clock = FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(1501)
    assert timer.phase is Phase.OVERTIME
    assert timer.remaining() == 0
    assert timer.overtime() == 1


def test_pause_freezes_elapsed_time():
    clock = FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(100)
    timer.pause()
    assert timer.is_paused is True
    clock.advance(300)  # 暂停期间不应计入
    assert timer.elapsed_focus() == 100


def test_resume_continues_counting_without_paused_gap():
    clock = FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(100)
    timer.pause()
    clock.advance(300)
    timer.resume()
    assert timer.is_paused is False
    clock.advance(50)
    assert timer.elapsed_focus() == 150


def test_toggle_pause_flips_state():
    timer = FocusTimer(target_seconds=1500, clock=FakeClock())
    timer.toggle_pause()
    assert timer.is_paused is True
    timer.toggle_pause()
    assert timer.is_paused is False
