import pandas as pd
import pytest

from datavis.herbarium import (
    FIELD_CANDIDATES,
    HerbariumSchemaError,
    prepare_herbarium_data,
)


def query_frame():
    return pd.DataFrame(
        {
            "1.collectionobject.catalogNumber": ["A1"],
            "1,10.collectingevent.endDate": ["1995-06-02"],
            "1,10,2.locality.localityName": ["English Bay"],
            "1,10,2.locality.latitude1": ["49.28"],
            "1,10,2.locality.longitude1": ["-123.14"],
            "1,10,2,3.geography.Country": ["Canada"],
            "1,10,2,3.geography.State": ["British Columbia"],
            "1,10,30-collectors,5.agent.firstName": ["Ada"],
            "1,10,30-collectors,5.agent.middleInitial": ["L"],
            "1,10,30-collectors,5.agent.lastName": ["Smith"],
        }
    )


def test_prepares_live_query_columns_for_dashboard():
    frame = prepare_herbarium_data(query_frame())

    assert frame.loc[0, "full_name"] == "Ada L Smith"
    assert frame.loc[0, "year"] == 1995
    assert frame.loc[0, "latitude"] == 49.28
    assert frame.loc[0, "province"] == "British Columbia"


def test_accepts_saved_query_aliases():
    source = query_frame().rename(
        columns={candidates[0]: target for target, candidates in FIELD_CANDIDATES.items()}
    )

    assert prepare_herbarium_data(source).loc[0, "catalognumber"] == "A1"


def test_reports_missing_saved_query_fields():
    with pytest.raises(HerbariumSchemaError, match="longitude"):
        prepare_herbarium_data(
            query_frame().drop(columns=["1,10,2.locality.longitude1"])
        )
