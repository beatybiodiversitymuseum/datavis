"""A deliberately simple, temperature-only marine suitability lesson."""

from pathlib import Path

import pandas as pd


GRID_PATH = Path(__file__).resolve().parents[2] / "data" / "bio_oracle_bc_surface_temperature.csv"
CELL_SIZE = 0.05
LAT_START = 48.025
LON_START = -139.975


def load_temperature_grid(path: Path = GRID_PATH) -> pd.DataFrame:
    grid = pd.read_csv(path)
    grid["lat_cell"] = ((grid["latitude"] - LAT_START) / CELL_SIZE).round().astype(int)
    grid["lon_cell"] = ((grid["longitude"] - LON_START) / CELL_SIZE).round().astype(int)
    return grid


def matched_occurrences(source: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    required = (
        "Latitude", "Longitude", "Genus - Full Name", "Species - Full Name",
        "State - Full Name",
    )
    missing = [column for column in required if column not in source]
    if missing:
        raise ValueError("query 707 is missing displayed fields: " + ", ".join(missing))

    records = source.loc[source["State - Full Name"].eq("British Columbia"), list(required)].copy()
    records["Latitude"] = pd.to_numeric(records["Latitude"], errors="coerce")
    records["Longitude"] = pd.to_numeric(records["Longitude"], errors="coerce")
    records = records.dropna(subset=["Latitude", "Longitude", "Genus - Full Name", "Species - Full Name"])
    records = records.loc[
        records["Latitude"].between(-90, 90)
        & records["Longitude"].between(-180, 180)
        & records["Genus - Full Name"].astype(str).str.strip().ne("")
        & records["Species - Full Name"].astype(str).str.strip().ne("")
    ].copy()
    records["species"] = (
        records["Genus - Full Name"].astype(str).str.strip()
        + " " + records["Species - Full Name"].astype(str).str.strip()
    )
    records["lat_cell"] = ((records["Latitude"] - LAT_START) / CELL_SIZE).round().astype(int)
    records["lon_cell"] = ((records["Longitude"] - LON_START) / CELL_SIZE).round().astype(int)
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
