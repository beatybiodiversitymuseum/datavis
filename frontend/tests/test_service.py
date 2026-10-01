from datavis.config import Settings
from datavis.service import initialize, run


def settings(state_dir):
    return Settings(
        state_dir=state_dir,
        log_level="INFO",
        host="127.0.0.1",
        port=8501,
        backend_url="http://127.0.0.1:8025",
        backend_token="test-token",
    )


def test_initialize_creates_state_directory(tmp_path):
    state_dir = tmp_path / "state"

    initialize(settings(state_dir))

    assert state_dir.is_dir()


def test_run_creates_state_directory(tmp_path):
    state_dir = tmp_path / "state"

    run(settings(state_dir))

    assert state_dir.is_dir()
