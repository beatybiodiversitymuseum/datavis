"""A deliberately simple, temperature-only marine suitability lesson."""

from pathlib import Path
import re

import pandas as pd


GRID_PATH = Path(__file__).resolve().parent / "data" / "bio_oracle_bc_surface_temperature.csv"
CELL_SIZE = 0.05
LAT_START = 48.025
LON_START = -139.975


def load_temperature_grid(path: Path = GRID_PATH) -> pd.DataFrame:
    grid = pd.read_csv(path)
    grid["lat_cell"] = ((grid["latitude"] - LAT_START) / CELL_SIZE).round().astype(int)
    grid["lon_cell"] = ((grid["longitude"] - LON_START) / CELL_SIZE).round().astype(int)
    return grid


def _field_tokens(column: str) -> list[str]:
    separated = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(column))
    return re.findall(r"[a-z]+", separated.casefold())


def _source_fields(
    columns: pd.Index, labels: dict[str, str] | None = None
) -> dict[str, str]:
    selected = {}
    for role in ("latitude", "longitude", "genus", "species", "state"):
        matches = []
        for column in columns:
            names = (str(column), (labels or {}).get(str(column), ""))
            for name in names:
                tokens = _field_tokens(name)
                if tokens[-1:] == [role] or tokens[-3:] == [role, "full", "name"]:
                    matches.append(str(column))
                    break
        if len(matches) == 1:
            selected[role] = matches[0]
        elif len(matches) > 1:
            raise ValueError(f"Occurrence dataset has ambiguous {role} fields")
    missing = [role for role in ("latitude", "longitude", "genus", "species", "state") if role not in selected]
    if missing:
        raise ValueError("Occurrence dataset is missing fields: " + ", ".join(missing))
    return selected


def matched_occurrences(
    source: pd.DataFrame, grid: pd.DataFrame, labels: dict[str, str] | None = None
) -> pd.DataFrame:
    fields = _source_fields(source.columns, labels)
    records = source.loc[
        source[fields["state"]].eq("British Columbia"), list(fields.values())
    ].rename(columns={column: role for role, column in fields.items()}).copy()
    records = records[["latitude", "longitude", "genus", "species"]]
    records["latitude"] = pd.to_numeric(records["latitude"], errors="coerce")
    records["longitude"] = pd.to_numeric(records["longitude"], errors="coerce")
    records = records.dropna(subset=["latitude", "longitude", "genus", "species"])
    records = records.loc[
        records["latitude"].between(-90, 90)
        & records["longitude"].between(-180, 180)
        & records["genus"].astype(str).str.strip().ne("")
        & records["species"].astype(str).str.strip().ne("")
    ].copy()
    records["species"] = (
        records["genus"].astype(str).str.strip()
        + " " + records["species"].astype(str).str.strip()
    )
    records["lat_cell"] = ((records["latitude"] - LAT_START) / CELL_SIZE).round().astype(int)
    records["lon_cell"] = ((records["longitude"] - LON_START) / CELL_SIZE).round().astype(int)
    records = records.drop_duplicates(["species", "lat_cell", "lon_cell"])
    return records.merge(
        grid[["lat_cell", "lon_cell", "baseline_c", "ssp245_2050_c"]],
        on=["lat_cell", "lon_cell"],
        how="left",
        validate="many_to_one",
    )


def temperature_envelope(
    records: pd.DataFrame, species: str, tail: float = 0.1
) -> tuple[float, float, int]:
    if not 0 < tail < 0.5:
        raise ValueError("temperature envelope tail must be between 0 and 0.5")
    temperatures = records.loc[records["species"].eq(species), "baseline_c"].dropna()
    if len(temperatures) < 50:
        raise ValueError("At least 50 distinct BC ocean grid cells are needed for this lesson.")
    return float(temperatures.quantile(tail)), float(temperatures.quantile(1 - tail)), len(temperatures)


def suitability(grid: pd.DataFrame, minimum: float, maximum: float, column: str) -> pd.DataFrame:
    result = grid[["latitude", "longitude", column]].copy()
    result["suitable"] = result[column].between(minimum, maximum)
    return result
