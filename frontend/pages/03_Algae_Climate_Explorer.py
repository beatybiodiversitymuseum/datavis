import logging

import pydeck as pdk
import requests
import streamlit as st

from datavis.algae_sdm import (
    load_temperature_grid,
    matched_occurrences,
    suitability,
    temperature_envelope,
)
from datavis.ui import apply_branding, dataset_client


logger = logging.getLogger(__name__)
st.set_page_config(page_title="Algae Climate Explorer", page_icon="🌊", layout="wide")
apply_branding()
st.title("Algae Climate Explorer")
st.write(
    "Explore how a simple sea surface temperature envelope changes under a future "
    "climate scenario. This is a classroom model of climatic suitability, not a "
    "prediction of where algae will occur."
)


@st.cache_data(ttl=86400, show_spinner="Loading reviewed algae records…")
def load_occurrences():
    return dataset_client().dataframe("algae-sdm-occurrences")


@st.cache_data
def load_grid():
    return load_temperature_grid()


try:
    grid = load_grid()
except Exception:
    logger.exception("Marine temperature grid could not be loaded")
    st.error("The marine temperature grid is missing or unreadable in this deployment.")
    st.stop()

try:
    occurrences = load_occurrences()
except requests.HTTPError as error:
    logger.exception("Algae occurrence dataset request failed")
    status = error.response.status_code if error.response is not None else None
    if status == 404:
        st.error("The algae occurrence dataset is not published by the private data service yet. Deploy the updated backend first.")
    elif status == 502:
        st.error("The private data service could not refresh the algae occurrence dataset. Check the backend service logs.")
    else:
        st.error("The private data service rejected the algae occurrence dataset request. Check the backend service logs.")
    st.stop()
except Exception:
    logger.exception("Algae occurrence dataset could not be loaded")
    st.error("The algae occurrence dataset could not be loaded from the private data service.")
    st.stop()

try:
    records = matched_occurrences(occurrences, grid)
except ValueError as error:
    logger.warning("Checking collection field labels after a schema mismatch: %s", error)
    try:
        labels = dataset_client().column_labels("algae-sdm-occurrences")
        records = matched_occurrences(occurrences, grid, labels)
    except Exception:
        logger.exception("Algae occurrence dataset schema is incompatible; columns=%s", list(occurrences.columns))
        st.error("The algae occurrence dataset lacks the fields needed for this example. Check the frontend service logs.")
        st.stop()
except Exception:
    logger.exception("Algae occurrence dataset could not be matched to the marine grid")
    st.error("The algae occurrence dataset could not be matched to the marine grid. Check the frontend service logs.")
    st.stop()

species = "Fucus gardneri"
coverage = records.loc[records["species"].eq(species), "baseline_c"]
if coverage.count() < 50:
    st.warning("The example species does not currently have 50 matched BC ocean grid cells.")
    st.stop()

st.subheader("Example species: Fucus gardneri")
range_name = st.select_slider(
    "Temperatures included around the middle of the observed range",
    options=("50%", "80%", "90%"),
    value="80%",
)
tail = {"50%": 0.25, "80%": 0.1, "90%": 0.05}[range_name]
minimum, maximum, matched = temperature_envelope(records, species, tail)
total_cells = int(coverage.size)

one, two, three = st.columns(3)
one.metric("Distinct BC grid cells", f"{total_cells:,}")
two.metric("Matched ocean cells", f"{matched:,}")
three.metric("Training temperature range", f"{minimum:.1f}–{maximum:.1f} °C")
st.caption(
    f"{total_cells - matched:,} distinct record cells have no matching Bio-ORACLE ocean "
    "temperature value and are excluded from the model. Multiple specimens in one "
    "grid cell count once."
)


def show_map(column: str, title: str):
    mapped = suitability(grid, minimum, maximum, column)
    mapped["color"] = mapped["suitable"].map(
        {True: [22, 135, 119, 175], False: [175, 185, 192, 95]}
    )
    mapped["temperature"] = mapped[column].round(1)
    st.subheader(title)
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(latitude=53.5, longitude=-130.5, zoom=4.5),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=mapped,
                    get_position="[longitude, latitude]",
                    get_fill_color="color",
                    get_radius=2600,
                    pickable=True,
                )
            ],
            tooltip={"text": "Sea surface: {temperature} °C"},
        ),
        use_container_width=True,
    )
    st.caption(f"{mapped['suitable'].sum():,} of {len(mapped):,} ocean cells fall within the training range.")


left, right = st.columns(2)
with left:
    show_map("baseline_c", "Present baseline · 2010–2020")
with right:
    show_map("ssp245_2050_c", "SSP2-4.5 · 2050–2060")

st.info(
    f"Teaching method: the range spans the middle {range_name} of baseline sea "
    "surface temperature at matched BC occurrence cells. The same range is applied "
    "to both maps. Teal cells fall inside the range; grey cells fall outside it. "
    "The 0.05° grid is coarse for "
    "shoreline habitat; temperature alone omits other ecological factors."
)
st.caption(
    "Marine temperature: Bio-ORACLE v3 surface ocean temperature, baseline 2010–2020 "
    "and SSP2-4.5 2050–2060. Occurrences: reviewed Specify algae dataset. "
    "Maps show an ocean grid in a BC coastal study window, including adjacent waters."
)
