from pathlib import Path

import pytest

from datavis_api.config import ConfigurationError, Settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("DATAVIS_API_STATE_DIR", "/tmp/service-state")
    monkeypatch.setenv("DATAVIS_API_LOG_LEVEL", "debug")
    monkeypatch.setenv("SPECIFY_COLLECTION_ID", "1")
    monkeypatch.setenv("SPECIFY_METADATA_URL", "http://metadata")

    settings = Settings.from_environment()

    assert settings.state_dir == Path("/tmp/service-state")
    assert settings.log_level == "DEBUG"
    assert settings.cache_ttl_seconds == 86400
    assert settings.metadata_url == "http://metadata"


def test_state_dir_is_required(monkeypatch):
    monkeypatch.delenv("DATAVIS_API_STATE_DIR", raising=False)

    with pytest.raises(ConfigurationError):
        Settings.from_environment()


def test_log_level_is_validated(monkeypatch):
    monkeypatch.setenv("DATAVIS_API_STATE_DIR", "/tmp/service-state")
    monkeypatch.setenv("DATAVIS_API_LOG_LEVEL", "verbose")
    monkeypatch.setenv("SPECIFY_COLLECTION_ID", "1")
    monkeypatch.setenv("SPECIFY_METADATA_URL", "http://metadata")

    with pytest.raises(ConfigurationError, match="standard logging level"):
        Settings.from_environment()
