from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """Raised when required runtime configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    state_dir: Path
    log_level: str
    host: str
    port: int
    backend_url: str
    backend_token: str

    @classmethod
    def from_environment(cls) -> "Settings":
        state_dir = os.environ.get("DATAVIS_STATE_DIR")
        if not state_dir:
            raise ConfigurationError("DATAVIS_STATE_DIR is required")
        log_level = os.environ.get("DATAVIS_LOG_LEVEL", "INFO").upper()
        if log_level not in logging.getLevelNamesMapping():
            raise ConfigurationError(
                f"DATAVIS_LOG_LEVEL must be a standard logging level, got {log_level!r}"
            )
        try:
            port = int(os.environ.get("DATAVIS_PORT", "8501"))
        except ValueError as error:
            raise ConfigurationError("DATAVIS_PORT must be an integer") from error
        backend_url = os.environ.get("DATAVIS_BACKEND_URL", "").rstrip("/")
        backend_token = os.environ.get("DATAVIS_BACKEND_TOKEN", "")
        if not backend_url or not backend_token or not 1024 <= port <= 65535:
            raise ConfigurationError(
                "DATAVIS_BACKEND_URL, DATAVIS_BACKEND_TOKEN, and a valid port are required"
            )
        return cls(
            state_dir=Path(state_dir),
            log_level=log_level,
            host=os.environ.get("DATAVIS_HOST", "127.0.0.1"),
            port=port,
            backend_url=backend_url,
            backend_token=backend_token,
        )
