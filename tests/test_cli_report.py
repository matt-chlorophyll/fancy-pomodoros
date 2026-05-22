from datetime import datetime

from typer.testing import CliRunner

from pomo.cli import app
from pomo.models import Session
from pomo.storage import append_session


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
