"""Private backend client used only by the server-side Streamlit process."""

from io import BytesIO

import pandas as pd
import requests

from .config import Settings


class DatasetClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.backend_url
        self.session = requests.Session()
        self.session.headers["X-Service-Token"] = settings.backend_token

    def list_datasets(self) -> list[dict[str, str]]:
        response = self.session.get(f"{self.base_url}/v1/datasets", timeout=20)
        response.raise_for_status()
        return response.json()

    def dataframe(self, slug: str) -> pd.DataFrame:
        response = self.session.get(
            f"{self.base_url}/v1/datasets/{slug}.csv", timeout=190
        )
        response.raise_for_status()
        return pd.read_csv(BytesIO(response.content))
