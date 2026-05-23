from pomo.models import KIND_FOCUS, KIND_REST
from pomo.timer import Phase
from pomo.ui.format import format_clock, format_minutes, format_span, progress_bar
from pomo.ui.theme import (
    FOCUS,
    FOCUS_OVERTIME,
    OVERTIME,
    REST,
    REST_OVERTIME,
    palette_for,
)


def test_format_clock_pads_minutes_and_seconds():
    assert format_clock(0) == "00:00"
    assert format_clock(65) == "01:05"
    assert format_clock(1500) == "25:00"


def test_format_clock_allows_minutes_over_sixty():
    assert format_clock(3725) == "62:05"


def test_format_span_is_hours_colon_minutes():
    assert format_span(0) == "0:00"
    assert format_span(2100) == "0:35"
    assert format_span(9000) == "2:30"


def test_format_minutes_text():
    assert format_minutes(3120) == "52 分钟"


def test_progress_bar_fills_proportionally():
    assert progress_bar(0.0, width=10) == "░░░░░░░░░░"
    assert progress_bar(1.0, width=10) == "██████████"
    assert progress_bar(0.5, width=10) == "█████░░░░░"


def test_progress_bar_clamps_out_of_range():
    assert progress_bar(-1.0, width=4) == "░░░░"
    assert progress_bar(2.0, width=4) == "████"


def test_palette_for_phase():
    assert palette_for(Phase.FOCUS) is FOCUS
    assert palette_for(Phase.OVERTIME) is OVERTIME


def test_palette_for_focus_overtime_is_green_not_amber():
    # focus 加时表示更长的专注（好事），所以是绿色而非琥珀。
    assert palette_for(Phase.OVERTIME, KIND_FOCUS) is FOCUS_OVERTIME
    assert FOCUS_OVERTIME.accent.lower() == "#a3be8c"


def test_palette_for_rest_kind():
    assert palette_for(Phase.FOCUS, KIND_REST) is REST
    assert palette_for(Phase.OVERTIME, KIND_REST) is REST_OVERTIME
    # 休息超时是不好的，所以是红色。
    assert REST_OVERTIME.accent.lower() == "#bf616a"
