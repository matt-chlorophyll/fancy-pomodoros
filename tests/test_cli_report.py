from datetime import datetime

from typer.testing import CliRunner

from pomo import cli
from pomo.cli import _countdown_loop, app
from pomo.models import Session
from pomo.ratings import load_ratings
from pomo.storage import append_session
from pomo.timer import FocusTimer


def test_report_empty_state(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["report"])
    assert result.exit_code == 0
    assert "还没有记录" in result.output


def test_report_shows_seeded_session(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    now = datetime.now()
    session = Session(
        id="x",
        category="工作",
        task="写文档",
        started_at=now.isoformat(timespec="seconds"),
        ended_at=now.isoformat(timespec="seconds"),
        focus_seconds=1500,
        target_seconds=1500,
        reached_overtime=False,
    )
    append_session(tmp_path / "sessions.json", session)
    result = CliRunner().invoke(app, ["report"])
    assert result.exit_code == 0
    assert "工作" in result.output


def test_report_rejects_bad_date(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["report", "--date", "not-a-date"])
    assert result.exit_code == 1
    assert "日期格式无效" in result.output


def test_report_week_flag_shows_session(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    now = datetime.now()
    session = Session(
        id="x",
        category="工作",
        task="写文档",
        started_at=now.isoformat(timespec="seconds"),
        ended_at=now.isoformat(timespec="seconds"),
        focus_seconds=1500,
        target_seconds=1500,
        reached_overtime=True,
    )
    append_session(tmp_path / "sessions.json", session)
    result = CliRunner().invoke(app, ["report", "--week"])
    assert result.exit_code == 0
    assert "工作" in result.output
    assert "本周复盘" in result.output


def test_start_rejects_non_positive_minutes(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["start", "--minutes", "0"])
    assert result.exit_code != 0


def test_rest_rejects_non_positive_minutes(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["rest", "--minutes", "0"])
    assert result.exit_code != 0


def test_rest_command_is_registered():
    # 不实际跑（避免开计时），只看 help 里有 rest 命令。
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "rest" in result.output


def test_superfocus_commands_are_registered():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "superfocus" in result.output
    assert "sf" in result.output


def test_superfocus_rejects_non_positive_minutes(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["superfocus", "--minutes", "0"])
    assert result.exit_code != 0


def test_sf_rejects_non_positive_minutes(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["sf", "--minutes", "0"])
    assert result.exit_code != 0


class _FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class _NullLive:
    """旁路 rich.Live —— 测试 _countdown_loop 时只关心按键和阈值。"""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def update(self, *args, **kwargs) -> None:
        pass


def _patch_read_key(monkeypatch, keys):
    queue = list(keys)

    def fake_read_key():
        return queue.pop(0) if queue else None

    monkeypatch.setattr(cli, "read_key", fake_read_key)


def _setup_loop_env(monkeypatch, keys):
    _patch_read_key(monkeypatch, keys)
    monkeypatch.setattr(cli, "Live", _NullLive)
    from rich.console import Console

    return Console(quiet=True)


def test_countdown_loop_below_threshold_returns_abandoned(monkeypatch):
    console = _setup_loop_env(monkeypatch, ["s"])
    clock = _FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(60)  # 才专注了 1 分钟

    outcome = _countdown_loop(
        console, "工作", "写文档", timer, "加油", min_focus_seconds=1500
    )
    assert outcome == "abandoned"


def test_countdown_loop_at_threshold_returns_finished(monkeypatch):
    console = _setup_loop_env(monkeypatch, ["s"])
    clock = _FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)
    clock.advance(1500)  # 刚好到 25 分钟

    outcome = _countdown_loop(
        console, "工作", "写文档", timer, "加油", min_focus_seconds=1500
    )
    assert outcome == "finished"


def test_countdown_loop_no_threshold_completes_immediately(monkeypatch):
    """min_focus_seconds=0（默认）时，按 s 立刻完成，保持原有行为。"""
    console = _setup_loop_env(monkeypatch, ["s"])
    clock = _FakeClock()
    timer = FocusTimer(target_seconds=1500, clock=clock)

    outcome = _countdown_loop(console, "工作", "写文档", timer, "加油")
    assert outcome == "finished"


def test_rate_records_score_and_comment(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(
        app, ["rate", "--score", "4", "--comment", "今天非常focus"]
    )
    assert result.exit_code == 0
    ratings = load_ratings(tmp_path / "ratings.json")
    assert len(ratings) == 1
    assert ratings[0].score == 4
    assert ratings[0].comment == "今天非常focus"


def test_rate_makes_comment_optional(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["rate", "--score", "3"])
    assert result.exit_code == 0
    ratings = load_ratings(tmp_path / "ratings.json")
    assert len(ratings) == 1
    assert ratings[0].comment == ""


def test_rate_requires_score(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["rate"])
    assert result.exit_code != 0


def test_rate_rejects_score_out_of_range(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    assert CliRunner().invoke(app, ["rate", "--score", "0"]).exit_code != 0
    assert CliRunner().invoke(app, ["rate", "--score", "6"]).exit_code != 0


def test_rate_overwrites_same_day(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["rate", "--score", "2", "--comment", "一开始"])
    result = runner.invoke(app, ["rate", "--score", "5", "--comment", "其实挺好"])
    assert result.exit_code == 0
    ratings = load_ratings(tmp_path / "ratings.json")
    assert len(ratings) == 1
    assert ratings[0].score == 5
    assert ratings[0].comment == "其实挺好"


def test_report_shows_today_rating(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    CliRunner().invoke(app, ["rate", "--score", "4", "--comment", "今天还不错"])
    result = CliRunner().invoke(app, ["report"])
    assert result.exit_code == 0
    assert "评分" in result.output
    assert "今天还不错" in result.output
