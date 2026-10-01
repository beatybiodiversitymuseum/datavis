"""Render one allowlisted Specify saved query as CSV."""

import csv
import io


class ExportError(RuntimeError):
    """Raised when Specify returns an unsafe or inconsistent query result."""


def render_query_csv(
    client, query_id: int, max_rows: int, required_columns: tuple[str, ...] = ()
) -> bytes:
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
    if required_columns and tuple(headers) != required_columns:
        raise ExportError(
            "saved query columns do not match the reviewed dataset contract"
        )

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headers)
    for row_number, row in enumerate(client.stored_query_rows(query_id), start=1):
        if row_number > max_rows:
            raise ExportError(f"saved query exceeds the configured {max_rows} row limit")
        if len(row) != len(headers) + 1:
            raise ExportError("saved query row does not match its displayed fields")
        writer.writerow("" if value is None or value == "None" else value for value in row[1:])
    return output.getvalue().encode("utf-8")
