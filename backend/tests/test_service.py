import io
from pathlib import Path

import pytest

from datavis_api.config import ConfigurationError, load_datasets
from datavis_api.csv_export import write_query_csv


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
    output = io.StringIO(newline="")
    write_query_csv(Client(), 42, output)
    assert output.getvalue() == "1.name\r\nOak\r\n"


def test_writes_more_than_one_hundred_thousand_rows():
    class CountingOutput:
        def __init__(self):
            self.lines = 0

        def write(self, value):
            self.lines += value.count("\n")
            return len(value)

    class LargeClient(Client):
        def stored_query_rows(self, query_id):
            assert query_id == 42
            for record_id in range(100_001):
                yield [record_id, "Oak"]

    output = CountingOutput()
    write_query_csv(LargeClient(), 42, output)

    assert output.lines == 100_002


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
