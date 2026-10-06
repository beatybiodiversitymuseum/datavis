from unittest.mock import patch

from datavis_api import cli


def configure(monkeypatch, tmp_path):
    monkeypatch.setenv("DATAVIS_API_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("SPECIFY_COLLECTION_ID", "1")
    monkeypatch.setenv("SPECIFY_METADATA_URL", "http://metadata")


def test_initialize_command_loads_settings_and_initializes(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)

    with patch.object(cli, "initialize") as initialize:
        with patch("sys.argv", ["datavis-api", "initialize"]):
            result = cli.main()

    assert result == 0
    initialize.assert_called_once()


def test_refresh_cache_command_loads_settings(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)

    with patch.object(cli, "refresh_all_datasets") as refresh:
        with patch("sys.argv", ["datavis-api", "refresh-cache"]):
            result = cli.main()

    assert result == 0
    refresh.assert_called_once()
