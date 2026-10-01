from pathlib import Path

import pytest

from datavis_api.config import ConfigurationError, load_datasets
from datavis_api.csv_export import ExportError, render_query_csv


class Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"fields": [{"isdisplay": True, "position": 0, "stringid": "1.name"}]}


class Client:
    def get(self, path):
        assert path == "/api/specify/spquery/42/"
        return Response()

    def stored_query_rows(self, query_id):
        assert query_id == 42
        yield [101, "Oak"]


def test_renders_query_without_internal_record_id():
    assert render_query_csv(Client(), 42, 10) == b"1.name\r\nOak\r\n"


def test_enforces_row_limit():
    with pytest.raises(ExportError, match="row limit"):
        render_query_csv(Client(), 42, 0)


def test_enforces_reviewed_column_contract():
    with pytest.raises(ExportError, match="reviewed dataset contract"):
        render_query_csv(Client(), 42, 10, ("wrong.source",), ("catalogNumber",))


def test_maps_reviewed_source_columns_to_public_csv_names():
    assert render_query_csv(
        Client(), 42, 10, ("1.name",), ("scientificName",)
    ) == b"scientificName\r\nOak\r\n"


def test_dataset_registry_is_explicit_allowlist(tmp_path: Path):
    registry = tmp_path / "datasets.yaml"
    registry.write_text("datasets:\n  plants:\n    title: Plants\n    query_id: 42\n")
    assert load_datasets(registry)["plants"].query_id == 42


def test_rejects_invalid_query_id(tmp_path: Path):
    registry = tmp_path / "datasets.yaml"
    registry.write_text("datasets:\n  plants:\n    title: Plants\n    query_id: 0\n")
    with pytest.raises(ConfigurationError):
        load_datasets(registry)


def test_disabled_dataset_does_not_require_query_id(tmp_path: Path):
    registry = tmp_path / "datasets.yaml"
    registry.write_text(
        "datasets:\n  plants:\n    enabled: false\n    title: Plants\n    query_id: null\n"
    )
    assert load_datasets(registry) == {}
