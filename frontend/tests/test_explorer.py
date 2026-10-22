import pandas as pd

from datavis.explorer import date_counts, map_points


def test_charts_accept_specify_fields_and_ignore_invalid_values():
    frame = pd.DataFrame({
        "1,10.collectingevent.endDate": ["2020-01-02", "2020-01-02", "bad"],
        "1,10,2.locality.latitude1": [49.2, "91", 48.5],
        "1,10,2.locality.longitude1": [-123.1, -123, "bad"],
    })

    assert date_counts(frame).to_dict() == {pd.Timestamp("2020-01-02").date(): 2}
    assert map_points(frame).to_dict("records") == [
        {"latitude": 49.2, "longitude": -123.1}
    ]


def test_charts_accept_display_labels_and_missing_fields():
    frame = pd.DataFrame({
        "Date Collected": ["2021-03-04"],
        "Latitude": [50],
        "Longitude": [-120],
    })

    assert date_counts(frame).sum() == 1
    assert len(map_points(frame)) == 1
    assert date_counts(pd.DataFrame()) is None
    assert map_points(pd.DataFrame()) is None
