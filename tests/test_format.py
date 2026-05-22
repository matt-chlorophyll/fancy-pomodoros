from pomo.timer import Phase
from pomo.ui.format import format_clock, format_minutes, format_span, progress_bar
from pomo.ui.theme import FOCUS, OVERTIME, palette_for


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
