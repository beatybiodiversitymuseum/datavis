"""Render one allowlisted Specify saved query as CSV."""

import csv
from typing import TextIO


class ExportError(RuntimeError):
    """Raised when Specify returns an unsafe or inconsistent query result."""


def write_query_csv(client, query_id: int, output: TextIO) -> None:
    response = client.get(f"/api/specify/spquery/{query_id}/")
    response.raise_for_status()
    fields = sorted(
        (field for field in response.json()["fields"] if field.get("isdisplay")),
        key=lambda field: field["position"],
    )
    headers = [
        str(field.get("columnalias") or field.get("title") or field["stringid"])
        for field in fields
    ]
    if not headers or len(headers) != len(set(headers)):
        raise ExportError("saved query must expose unique displayed columns")
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in client.stored_query_rows(query_id):
        if len(row) != len(headers) + 1:
            raise ExportError("saved query row does not match its displayed fields")
        writer.writerow("" if value is None or value == "None" else value for value in row[1:])
