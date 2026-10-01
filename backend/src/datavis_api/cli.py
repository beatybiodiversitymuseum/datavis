"""Command-line entry point."""

import argparse
import os
import uvicorn

from .config import ConfigurationError, Settings
from .logging_config import configure_logging
from .service import initialize, refresh_all_datasets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("initialize", "refresh-cache", "serve"))
    args = parser.parse_args()
    if args.command in ("initialize", "refresh-cache"):
        try:
            settings = Settings.from_environment()
        except ConfigurationError as error:
            parser.error(str(error))
        configure_logging(settings.log_level)
        if args.command == "initialize":
            initialize(settings)
        else:
            refresh_all_datasets(settings)
    else:
        host = os.environ.get("DATAVIS_API_HOST", "127.0.0.1")
        port = int(os.environ.get("DATAVIS_API_PORT", "8025"))
        uvicorn.run("datavis_api.service:app", host=host, port=port, workers=1)
    return 0
