from pomo.keyboard import KEY_ENTER, KEY_ESC, KEY_SPACE, normalize_key


def test_normalize_space():
    assert normalize_key(" ") == KEY_SPACE


def test_normalize_enter_variants():
    assert normalize_key("\r") == KEY_ENTER
    assert normalize_key("\n") == KEY_ENTER


def test_normalize_escape():
    assert normalize_key("\x1b") == KEY_ESC


def test_normalize_letter_is_lowercased():
    assert normalize_key("S") == "s"
    assert normalize_key("q") == "q"


def test_normalize_non_printable_returns_none():
    assert normalize_key("\x00") is None
