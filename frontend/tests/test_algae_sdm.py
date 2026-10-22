import pandas as pd
import pytest

from datavis.algae_sdm import matched_occurrences, suitability, temperature_envelope


def test_occurrences_match_ocean_cells_once_and_exclude_unmatched_records():
    grid = pd.DataFrame({
        "lat_cell": [0, 1], "lon_cell": [0, 0],
        "baseline_c": [10.0, 12.0], "ssp245_2050_c": [11.0, 13.0],
        "latitude": [48.025, 48.075], "longitude": [-139.975, -139.975],
    })
    source = pd.DataFrame({
        "Latitude": [48.025, 48.025, 48.075, 49.0, 48.025],
        "Longitude": [-139.975] * 5,
        "Genus - Full Name": ["Fucus"] * 5,
        "Species - Full Name": ["gardneri"] * 5,
        "State - Full Name": ["British Columbia"] * 4 + ["Alaska"],
    })

    matched = matched_occurrences(source, grid)

    assert len(matched) == 3
    assert matched["baseline_c"].count() == 2
    assert matched["baseline_c"].dropna().tolist() == [10.0, 12.0]


def test_temperature_envelope_requires_fifty_matched_cells():
    records = pd.DataFrame({"species": ["Fucus gardneri"] * 49, "baseline_c": range(49)})
    with pytest.raises(ValueError, match="50 distinct"):
        temperature_envelope(records, "Fucus gardneri")


def test_suitability_applies_same_bounds_to_current_and_future():
    grid = pd.DataFrame({
        "latitude": [50, 51], "longitude": [-130, -129],
        "baseline_c": [10, 12], "ssp245_2050_c": [12, 14],
    })
    assert suitability(grid, 10, 12, "baseline_c")["suitable"].tolist() == [True, True]
    assert suitability(grid, 10, 12, "ssp245_2050_c")["suitable"].tolist() == [True, False]
