"""Find optional date and coordinate fields in a published query result."""

import pandas as pd


def _field(frame: pd.DataFrame, *names: str) -> str | None:
    columns = {str(column).casefold(): str(column) for column in frame.columns}
    for name in names:
        match = columns.get(name.casefold())
        if match is not None:
            return match
    return None


def date_counts(frame: pd.DataFrame) -> pd.Series | None:
    column = _field(
        frame,
        "1,10.collectingevent.endDate",
        "collection_date",
        "Date Collected",
    )
    if column is None:
        return None
    dates = pd.to_datetime(frame[column], errors="coerce").dt.date.dropna()
    return dates.value_counts().sort_index().rename("Items")


def map_points(frame: pd.DataFrame) -> pd.DataFrame | None:
    latitude = _field(frame, "1,10,2.locality.latitude1", "latitude", "Latitude")
    longitude = _field(frame, "1,10,2.locality.longitude1", "longitude", "Longitude")
    if latitude is None or longitude is None:
        return None
    points = pd.DataFrame({
        "latitude": pd.to_numeric(frame[latitude], errors="coerce"),
        "longitude": pd.to_numeric(frame[longitude], errors="coerce"),
    }).dropna()
    return points.loc[points.latitude.between(-90, 90) & points.longitude.between(-180, 180)]
