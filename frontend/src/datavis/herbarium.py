"""Prepare query 685's live saved-query schema for the Herbarium dashboard."""

from __future__ import annotations

import pandas as pd


class HerbariumSchemaError(ValueError):
    """Raised when the saved query no longer supplies a dashboard field."""


FIELD_CANDIDATES = {
    "catalognumber": ("1.collectionobject.catalogNumber", "catalognumber"),
    "collection_date": ("1,10.collectingevent.endDate", "collection_date"),
    "localityname": ("1,10,2.locality.localityName", "localityname"),
    "latitude": ("1,10,2.locality.latitude1", "latitude"),
    "longitude": ("1,10,2.locality.longitude1", "longitude"),
    "country": ("1,10,2,3.geography.Country", "country"),
    "province": ("1,10,2,3.geography.State", "province"),
    "firstname": ("1,10,30-collectors,5.agent.firstName", "firstname"),
    "middleinitial": (
        "1,10,30-collectors,5.agent.middleInitial",
        "middleinitial",
    ),
    "lastname": ("1,10,30-collectors,5.agent.lastName", "lastname"),
}


def _source_column(columns: pd.Index, candidates: tuple[str, ...]) -> str | None:
    by_casefold = {str(column).casefold(): str(column) for column in columns}
    for candidate in candidates:
        if candidate.casefold() in by_casefold:
            return by_casefold[candidate.casefold()]
    return None


def prepare_herbarium_data(source: pd.DataFrame) -> pd.DataFrame:
    """Map the saved query's displayed fields into dashboard-friendly names."""
    rename = {}
    missing = []
    for target, candidates in FIELD_CANDIDATES.items():
        column = _source_column(source.columns, candidates)
        if column is None:
            missing.append(target)
        else:
            rename[column] = target
    if missing:
        raise HerbariumSchemaError(
            "saved query 685 is missing dashboard fields: " + ", ".join(missing)
        )

    frame = source.rename(columns=rename).copy()
    parsed_dates = pd.to_datetime(frame["collection_date"], errors="coerce")
    frame["collection_date"] = parsed_dates.dt.date
    frame["year"] = parsed_dates.dt.year
    frame["decade"] = (frame["year"] // 10) * 10
    for column in ("latitude", "longitude"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column, fallback in (
        ("localityname", "Unknown Locality"),
        ("country", "Unknown"),
        ("province", "Unknown"),
    ):
        frame[column] = frame[column].fillna(fallback).replace("", fallback)

    name_parts = frame[["firstname", "middleinitial", "lastname"]].fillna("")
    frame["full_name"] = name_parts.apply(
        lambda row: " ".join(part.strip() for part in row if part.strip()), axis=1
    ).replace("", "Unknown Collector")
    frame["lastname"] = frame["lastname"].fillna("")
    return frame
