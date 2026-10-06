"""Private backend client used only by the server-side Streamlit process."""

import tempfile

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
        with self.session.get(
            f"{self.base_url}/v1/datasets/{slug}.csv", timeout=190, stream=True
        ) as response:
            response.raise_for_status()
            with tempfile.TemporaryFile(mode="w+b") as csv_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        csv_file.write(chunk)
                csv_file.seek(0)
                return pd.read_csv(csv_file)

    def column_labels(self, slug: str) -> dict[str, str]:
        response = self.session.get(
            f"{self.base_url}/v1/datasets/{slug}/columns", timeout=30
        )
        response.raise_for_status()
        return {item["source"]: item["label"] for item in response.json()}
