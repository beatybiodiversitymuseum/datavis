from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import threading

from .config import Settings

logger = logging.getLogger(__name__)


def initialize(settings: Settings) -> None:
    """Idempotently prepare durable state required by this release."""
    settings.state_dir.mkdir(parents=True, exist_ok=True)
    # Add version-aware migrations or cache construction here when required.
    logger.info("service initialization completed")


def run(settings: Settings) -> None:
    """Execute one complete, safely repeatable unit of domain work."""
    settings.state_dir.mkdir(parents=True, exist_ok=True)
    logger.info("service run started")
    # Implement domain work here. Stage and validate output before activation.
    logger.info("service run completed")


def serve(settings: Settings) -> None:
    """Run Streamlit as the supervised public web process."""
    settings.state_dir.mkdir(parents=True, exist_ok=True)
    root = os.environ.get("DATAVIS_APP_ROOT", ".")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        f"{root}/Home.py",
        "--server.headless=true",
        f"--server.address={settings.host}",
        f"--server.port={settings.port}",
        "--server.baseUrlPath=datavis",
        "--browser.gatherUsageStats=false",
    ]
    raise SystemExit(subprocess.call(command))
