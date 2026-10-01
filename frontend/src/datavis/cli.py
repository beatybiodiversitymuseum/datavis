from __future__ import annotations

import argparse

from .config import ConfigurationError, Settings
from .logging_config import configure_logging
from .service import initialize, run, serve


def main() -> int:
    parser = argparse.ArgumentParser(description="Public multipage Streamlit host for curated Specify visualizations")
    parser.add_argument("command", choices=("initialize", "run", "serve"))
    args = parser.parse_args()

    try:
        settings = Settings.from_environment()
    except ConfigurationError as error:
        parser.error(str(error))

    configure_logging(settings.log_level)
    if args.command == "initialize":
        initialize(settings)
    elif args.command == "run":
        run(settings)
    else:
        serve(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
