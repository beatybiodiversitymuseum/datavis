from unittest.mock import patch

from datavis import cli


def configure(monkeypatch, tmp_path):
    monkeypatch.setenv("DATAVIS_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("DATAVIS_BACKEND_URL", "http://127.0.0.1:8025")
    monkeypatch.setenv("DATAVIS_BACKEND_TOKEN", "test-token")


def test_initialize_command_loads_settings_and_initializes(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)

    with patch.object(cli, "initialize") as initialize:
        with patch("sys.argv", ["datavis", "initialize"]):
            result = cli.main()

    assert result == 0
    initialize.assert_called_once()


def test_run_command_loads_settings_and_runs_service(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)

    with patch.object(cli, "run") as run:
        with patch("sys.argv", ["datavis", "run"]):
            result = cli.main()

    assert result == 0
    run.assert_called_once()


def test_service_errors_propagate(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)

    with patch.object(cli, "run", side_effect=RuntimeError("failed")):
        with patch("sys.argv", ["datavis", "run"]):
            try:
                cli.main()
            except RuntimeError as error:
                assert str(error) == "failed"
            else:
                raise AssertionError("runtime error did not propagate")
