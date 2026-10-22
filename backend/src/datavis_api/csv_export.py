"""Render one allowlisted Specify saved query as CSV."""

import csv
from dataclasses import dataclass
from typing import TextIO


class ExportError(RuntimeError):
    """Raised when Specify returns an unsafe or inconsistent query result."""


@dataclass(frozen=True)
class QueryColumn:
    header: str
    string_id: str


def query_columns(client, query_id: int) -> list[QueryColumn]:
    response = client.get(f"/api/specify/spquery/{query_id}/")
    response.raise_for_status()
    fields = sorted(
        (field for field in response.json()["fields"] if field.get("isdisplay")),
        key=lambda field: field["position"],
    )
    columns = [
        QueryColumn(
            header=str(
                field.get("columnalias") or field.get("title") or field["stringid"]
            ),
            string_id=str(field["stringid"]),
        )
        for field in fields
    ]
    headers = [column.header for column in columns]
    if not headers or len(headers) != len(set(headers)):
        raise ExportError("saved query must expose unique displayed columns")
    return columns


def write_query_csv(client, query_id: int, output: TextIO) -> None:
    headers = [column.header for column in query_columns(client, query_id)]
    sensitive_index = next(
        (index for index, header in enumerate(headers) if header.casefold() == "sensitive record"),
        None,
    )
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in client.stored_query_rows(query_id):
        if len(row) != len(headers) + 1:
            raise ExportError("saved query row does not match its displayed fields")
        sensitive_value = row[sensitive_index + 1] if sensitive_index is not None else None
        if sensitive_value not in (None, "None") and str(sensitive_value).strip():
            raise ExportError("saved query contains a sensitive record")
        writer.writerow("" if value is None or value == "None" else value for value in row[1:])
