"""The process-wide authenticated Specify client."""

import os
from functools import lru_cache

from specify_client import ApiSettings, SpecifyClient, get_session

from .config import Settings


def _credentials() -> tuple[str, str]:
    return os.environ["SPECIFY_USERNAME"], os.environ["SPECIFY_PASSWORD"]


@lru_cache(maxsize=1)
def get_specify_client(settings: Settings) -> SpecifyClient:
    policy = ApiSettings.from_yaml(settings.specify_settings_path)
    username, password = _credentials()
    session = get_session(
        policy.base_url,
        username=username,
        password=password,
        collection=settings.specify_collection_id,
        timeout=policy.timeout,
    )
    return SpecifyClient(policy, session, credential_provider=_credentials)
