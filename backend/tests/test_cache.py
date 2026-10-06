import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from datavis_api.cache import cache_path, is_fresh, read_cached_csv, write_cached_csv
from datavis_api.config import Dataset
from datavis_api import service


def settings(tmp_path: Path, ttl: int = 86400):
    return SimpleNamespace(
        state_dir=tmp_path,
        cache_ttl_seconds=ttl,
        max_csv_rows=100,
    )


def dataset():
    return Dataset("plants", "Plants", "", 42)


def test_atomic_cache_round_trip(tmp_path):
    written = write_cached_csv(tmp_path, "plants", b"name\r\nOak\r\n")

    assert written.content == b"name\r\nOak\r\n"
    assert read_cached_csv(tmp_path, "plants") == written
    assert is_fresh(written, 86400)
    assert not list((tmp_path / "cache").glob(".plants.*"))


def test_dataset_cache_refreshes_once_then_hits(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(service, "get_specify_client", lambda settings: object())
    monkeypatch.setattr(
        service,
        "render_query_csv",
        lambda *args: calls.append(args) or b"name\r\nOak\r\n",
    )

    first, first_status = service.cached_dataset_csv(settings(tmp_path), dataset())
    second, second_status = service.cached_dataset_csv(settings(tmp_path), dataset())

    assert first.content == second.content
    assert (first_status, second_status) == ("MISS", "HIT")
    assert len(calls) == 1


def test_refresh_failure_serves_last_csv_as_stale(monkeypatch, tmp_path):
    write_cached_csv(tmp_path, "plants", b"name\r\nOld oak\r\n")
    old = time.time() - 90000
    os.utime(cache_path(tmp_path, "plants"), (old, old))
    monkeypatch.setattr(service, "get_specify_client", lambda settings: object())
    monkeypatch.setattr(
        service,
        "render_query_csv",
        lambda *args: (_ for _ in ()).throw(RuntimeError("Specify unavailable")),
    )

    cached, status = service.cached_dataset_csv(settings(tmp_path), dataset())

    assert cached.content == b"name\r\nOld oak\r\n"
    assert status == "STALE"


def test_scheduled_refresh_reports_failure(monkeypatch, tmp_path):
    write_cached_csv(tmp_path, "plants", b"name\r\nOld oak\r\n")
    monkeypatch.setattr(service, "get_specify_client", lambda settings: object())
    monkeypatch.setattr(
        service,
        "render_query_csv",
        lambda *args: (_ for _ in ()).throw(RuntimeError("Specify unavailable")),
    )

    with pytest.raises(RuntimeError, match="Specify unavailable"):
        service.cached_dataset_csv(
            settings(tmp_path), dataset(), force=True, allow_stale=False
        )
