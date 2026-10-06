import os
import time
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

import pytest

from datavis_api.cache import (
    atomic_cache_writer,
    cache_path,
    dataset_lock,
    is_fresh,
    read_cached_csv,
)
from datavis_api.config import Dataset
from datavis_api import service


def settings(tmp_path: Path, ttl: int = 86400):
    return SimpleNamespace(
        state_dir=tmp_path,
        cache_ttl_seconds=ttl,
    )


def dataset():
    return Dataset("plants", "Plants", "", 42)


def write_cached_csv(state_dir: Path, slug: str, content: bytes):
    with atomic_cache_writer(state_dir, slug) as output:
        output.write(content.decode("utf-8"))
    cached = read_cached_csv(state_dir, slug)
    assert cached is not None
    return cached


def test_atomic_cache_round_trip(tmp_path):
    written = write_cached_csv(tmp_path, "plants", b"name\r\nOak\r\n")

    assert written.path.read_bytes() == b"name\r\nOak\r\n"
    assert read_cached_csv(tmp_path, "plants") == written
    assert is_fresh(written, 86400)
    assert not [
        path
        for path in (tmp_path / "cache").glob(".plants.*")
        if path.name != ".plants.lock"
    ]


def test_dataset_cache_refreshes_once_then_hits(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(service, "get_specify_client", lambda settings: object())
    monkeypatch.setattr(
        service,
        "write_query_csv",
        lambda *args: calls.append(args) or args[-1].write("name\r\nOak\r\n"),
    )

    first, first_status = service.cached_dataset_csv(settings(tmp_path), dataset())
    second, second_status = service.cached_dataset_csv(settings(tmp_path), dataset())

    assert first.path.read_bytes() == second.path.read_bytes()
    assert (first_status, second_status) == ("MISS", "HIT")
    assert len(calls) == 1


def test_refresh_failure_serves_last_csv_as_stale(monkeypatch, tmp_path):
    write_cached_csv(tmp_path, "plants", b"name\r\nOld oak\r\n")
    old = time.time() - 90000
    os.utime(cache_path(tmp_path, "plants"), (old, old))
    monkeypatch.setattr(service, "get_specify_client", lambda settings: object())
    monkeypatch.setattr(
        service,
        "write_query_csv",
        lambda *args: (_ for _ in ()).throw(RuntimeError("Specify unavailable")),
    )

    cached, status = service.cached_dataset_csv(settings(tmp_path), dataset())

    assert cached.path.read_bytes() == b"name\r\nOld oak\r\n"
    assert status == "STALE"


def test_scheduled_refresh_reports_failure(monkeypatch, tmp_path):
    write_cached_csv(tmp_path, "plants", b"name\r\nOld oak\r\n")
    monkeypatch.setattr(service, "get_specify_client", lambda settings: object())
    monkeypatch.setattr(
        service,
        "write_query_csv",
        lambda *args: (_ for _ in ()).throw(RuntimeError("Specify unavailable")),
    )

    with pytest.raises(RuntimeError, match="Specify unavailable"):
        service.cached_dataset_csv(
            settings(tmp_path), dataset(), force=True, allow_stale=False
        )


def test_interrupted_write_preserves_previous_cache(tmp_path):
    write_cached_csv(tmp_path, "plants", b"name\r\nOld oak\r\n")

    with pytest.raises(RuntimeError, match="interrupted"):
        with atomic_cache_writer(tmp_path, "plants") as output:
            output.write("name\r\nNew oak\r\n")
            raise RuntimeError("interrupted")

    assert cache_path(tmp_path, "plants").read_bytes() == b"name\r\nOld oak\r\n"


def test_dataset_lock_excludes_a_second_file_descriptor(tmp_path):
    with ExitStack() as stack:
        first = stack.enter_context(dataset_lock(tmp_path, "plants"))
        second = stack.enter_context(
            dataset_lock(tmp_path, "plants", timeout_seconds=0)
        )

        assert first is True
        assert second is False
