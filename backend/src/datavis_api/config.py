from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigurationError(ValueError):
    """Raised when required runtime configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    state_dir: Path
    cache_ttl_seconds: int
    log_level: str
    datasets_path: Path
    specify_settings_path: Path
    specify_collection_id: int

    @classmethod
    def from_environment(cls) -> "Settings":
        state_dir = os.environ.get("DATAVIS_API_STATE_DIR")
        if not state_dir:
            raise ConfigurationError("DATAVIS_API_STATE_DIR is required")
        log_level = os.environ.get("DATAVIS_API_LOG_LEVEL", "INFO").upper()
        if log_level not in logging.getLevelNamesMapping():
            raise ConfigurationError(
                f"DATAVIS_API_LOG_LEVEL must be a standard logging level, got {log_level!r}"
            )
        datasets_path = Path(os.environ.get("DATAVIS_DATASETS_PATH", "config/datasets.yaml"))
        specify_settings_path = Path(
            os.environ.get("SPECIFY_SETTINGS_PATH", "config/specify.yaml")
        )
        try:
            collection_id = int(os.environ["SPECIFY_COLLECTION_ID"])
            cache_ttl_seconds = int(
                os.environ.get("DATAVIS_CACHE_TTL_SECONDS", "86400")
            )
        except (KeyError, ValueError) as error:
            raise ConfigurationError(
                "collection ID and cache TTL must be integers"
            ) from error
        if collection_id < 1 or cache_ttl_seconds < 1:
            raise ConfigurationError(
                "collection ID and cache TTL must be positive"
            )
        return cls(
            state_dir=Path(state_dir),
            cache_ttl_seconds=cache_ttl_seconds,
            log_level=log_level,
            datasets_path=datasets_path,
            specify_settings_path=specify_settings_path,
            specify_collection_id=collection_id,
        )


@dataclass(frozen=True)
class Dataset:
    slug: str
    title: str
    description: str
    query_id: int


def load_datasets(path: Path) -> dict[str, Dataset]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as error:
        raise ConfigurationError(f"could not read dataset registry {path}: {error}") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("datasets", {}), dict):
        raise ConfigurationError("dataset registry must contain a datasets mapping")
    datasets: dict[str, Dataset] = {}
    for slug, item in payload.get("datasets", {}).items():
        if not isinstance(slug, str) or not slug.replace("-", "").isalnum():
            raise ConfigurationError(f"invalid dataset slug: {slug!r}")
        if not isinstance(item, dict):
            raise ConfigurationError(f"dataset {slug!r} must be a mapping")
        if item.get("enabled") is False:
            continue
        try:
            query_id = int(item["query_id"])
            title = str(item["title"]).strip()
        except (KeyError, TypeError, ValueError) as error:
            raise ConfigurationError(f"dataset {slug!r} requires title and query_id") from error
        if query_id < 1 or not title:
            raise ConfigurationError(f"dataset {slug!r} has invalid title or query_id")
        datasets[slug] = Dataset(
            slug=slug,
            title=title,
            description=str(item.get("description", "")).strip(),
            query_id=query_id,
        )
    return datasets
