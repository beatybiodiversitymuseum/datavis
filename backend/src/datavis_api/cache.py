"""Durable, atomic CSV cache for reviewed datasets."""

from __future__ import annotations

import os
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CachedCsv:
    content: bytes
    generated_at: datetime


def cache_path(state_dir: Path, slug: str) -> Path:
    return state_dir / "cache" / f"{slug}.csv"


def read_cached_csv(state_dir: Path, slug: str) -> CachedCsv | None:
    path = cache_path(state_dir, slug)
    try:
        stat = path.stat()
        content = path.read_bytes()
    except FileNotFoundError:
        return None
    return CachedCsv(
        content=content,
        generated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
    )


def is_fresh(cached: CachedCsv, ttl_seconds: int) -> bool:
    return time.time() - cached.generated_at.timestamp() <= ttl_seconds


def write_cached_csv(state_dir: Path, slug: str, content: bytes) -> CachedCsv:
    directory = cache_path(state_dir, slug).parent
    directory.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{slug}.", dir=directory)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, cache_path(state_dir, slug))
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    cached = read_cached_csv(state_dir, slug)
    assert cached is not None
    return cached
