from pathlib import Path

import pytest

from datavis.config import ConfigurationError, Settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("DATAVIS_STATE_DIR", "/tmp/service-state")
    monkeypatch.setenv("DATAVIS_LOG_LEVEL", "debug")
    monkeypatch.setenv("DATAVIS_BACKEND_URL", "http://127.0.0.1:8025")
    monkeypatch.setenv("DATAVIS_BACKEND_TOKEN", "test-token")

    settings = Settings.from_environment()

    assert settings.state_dir == Path("/tmp/service-state")
    assert settings.log_level == "DEBUG"


def test_state_dir_is_required(monkeypatch):
    monkeypatch.delenv("DATAVIS_STATE_DIR", raising=False)

    with pytest.raises(ConfigurationError):
        Settings.from_environment()


def test_log_level_is_validated(monkeypatch):
    monkeypatch.setenv("DATAVIS_STATE_DIR", "/tmp/service-state")
    monkeypatch.setenv("DATAVIS_LOG_LEVEL", "verbose")
    monkeypatch.setenv("DATAVIS_BACKEND_URL", "http://127.0.0.1:8025")
    monkeypatch.setenv("DATAVIS_BACKEND_TOKEN", "test-token")

    with pytest.raises(ConfigurationError, match="standard logging level"):
        Settings.from_environment()
