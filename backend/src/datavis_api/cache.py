"""Durable, atomic CSV cache for reviewed datasets."""

from __future__ import annotations

import fcntl
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, TextIO


@dataclass(frozen=True)
class CachedCsv:
    path: Path
    generated_at: datetime


def cache_path(state_dir: Path, slug: str) -> Path:
    return state_dir / "cache" / f"{slug}.csv"


def read_cached_csv(state_dir: Path, slug: str) -> CachedCsv | None:
    path = cache_path(state_dir, slug)
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return CachedCsv(
        path=path,
        generated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
    )


def is_fresh(cached: CachedCsv, ttl_seconds: int) -> bool:
    return time.time() - cached.generated_at.timestamp() <= ttl_seconds


@contextmanager
def dataset_lock(
    state_dir: Path, slug: str, timeout_seconds: float = 1
) -> Iterator[bool]:
    directory = cache_path(state_dir, slug).parent
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / f".{slug}.lock"
    with lock_path.open("a") as handle:
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    yield False
                    return
                time.sleep(0.05)
        try:
            yield True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def atomic_cache_writer(state_dir: Path, slug: str) -> Iterator[TextIO]:
    directory = cache_path(state_dir, slug).parent
    directory.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{slug}.", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            yield handle
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, cache_path(state_dir, slug))
        directory_descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
