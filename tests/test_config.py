from pathlib import Path

from pomo import config


def test_data_dir_uses_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    assert config.data_dir() == tmp_path


def test_data_dir_defaults_to_home(monkeypatch, tmp_path):
    monkeypatch.delenv("POMO_DATA_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert config.data_dir() == tmp_path / ".fancy-pomodoro"


def test_sessions_file_lives_under_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("POMO_DATA_DIR", str(tmp_path))
    assert config.sessions_file() == tmp_path / "sessions.json"


def test_data_dir_ignores_empty_env_override(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("POMO_DATA_DIR", "")
    assert config.data_dir() == tmp_path / ".fancy-pomodoro"
