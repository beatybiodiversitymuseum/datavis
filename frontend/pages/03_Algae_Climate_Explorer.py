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
st.title("Where does the ocean match this alga's observed temperatures?")
st.write(
    "Museum records show where this species was collected. We look up the sea "
    "surface temperature at those locations, then color ocean cells whose "
    "temperature falls in the same range. Compare today's map with a future "
    "climate scenario."
)


@st.cache_data(ttl=86400, show_spinner="Loading algae records…")
def load_occurrences():
    return dataset_client().dataframe("algae-sdm-occurrences")


@st.cache_data(ttl=86400, show_spinner=False)
def load_field_labels():
    return dataset_client().column_labels("algae-sdm-occurrences")


@st.cache_data
def load_grid():
    return load_temperature_grid()


try:
    grid = load_grid()
except Exception:
    logger.exception("Marine temperature grid could not be loaded")
    st.error("Ocean temperature data is temporarily unavailable.")
    st.stop()

try:
    occurrences = load_occurrences()
except requests.HTTPError as error:
    logger.exception("Algae occurrence dataset request failed")
    status = error.response.status_code if error.response is not None else None
    if status == 404:
        st.error("Algae records are not available right now.")
    elif status == 502:
        st.error("Algae records are temporarily unavailable. Please try again later.")
    else:
        st.error("Algae records could not be loaded right now.")
    st.stop()
except Exception:
    logger.exception("Algae occurrence dataset could not be loaded")
    st.error("Algae records could not be loaded right now.")
    st.stop()

try:
    labels = load_field_labels()
except Exception:
    logger.exception("Collection field labels could not be loaded")
    st.error("Algae records could not be displayed right now.")
    st.stop()

try:
    records = matched_occurrences(occurrences, grid, labels)
except ValueError:
    logger.exception(
        "Algae occurrence schema is incompatible; columns=%s labels=%s",
        list(occurrences.columns), labels,
    )
    st.error("Algae records could not be displayed right now.")
    st.stop()
except Exception:
    logger.exception("Algae occurrence dataset could not be matched to the marine grid")
    st.error("Algae records could not be compared with ocean temperatures right now.")
    st.stop()

species = "Fucus gardneri"
coverage = records.loc[records["species"].eq(species), "baseline_c"]
if coverage.count() < 50:
    st.warning("There are too few *Fucus gardneri* locations with ocean temperature data for this comparison.")
    st.stop()

st.subheader("Fucus gardneri")
range_name = st.select_slider(
    "How much of the observed temperature range should count as a match?",
    options=("50%", "80%", "90%"),
    value="80%",
    help="The middle 80% omits the warmest 10% and coolest 10% of temperatures at the matched museum locations.",
)
tail = {"50%": 0.25, "80%": 0.1, "90%": 0.05}[range_name]
minimum, maximum, matched = temperature_envelope(records, species, tail)
total_cells = int(coverage.size)
training_locations = records.loc[
    records["species"].eq(species) & records["baseline_c"].notna(),
    ["latitude", "longitude", "baseline_c"],
].copy()
training_locations["temperature"] = training_locations["baseline_c"].round(1)
training_locations["kind"] = "Museum record location"

st.write(
    f"**Step 1 · Learn from museum records.** {matched:,} distinct BC ocean cells "
    f"with *Fucus gardneri* records have a matching temperature value. The middle "
    f"{range_name} of those temperatures is **{minimum:.1f}–{maximum:.1f} °C**."
)
st.caption(f"{total_cells - matched:,} additional record cells have no ocean temperature value and are left out. Multiple specimens in one cell count once.")

current = suitability(grid, minimum, maximum, "baseline_c")
future = suitability(grid, minimum, maximum, "ssp245_2050_c")
st.write(
    "**Step 2 · Compare the ocean.** Teal cells fall in that same temperature "
    "range. Grey cells do not. White outlined circles on the present-day map "
    "show the museum record locations used above."
)
st.markdown(
    '<span style="color:#168777">●</span> Temperature matches &nbsp;&nbsp; '
    '<span style="color:#aeb9c0">●</span> Temperature outside range &nbsp;&nbsp; '
    '<span style="color:#303838">◉</span> Museum record location (present map)',
    unsafe_allow_html=True,
)


def show_map(mapped, column: str, title: str, show_records: bool = False):
    mapped = mapped.copy()
    mapped["color"] = mapped["suitable"].map(
        {True: [22, 135, 119, 175], False: [175, 185, 192, 95]}
    )
    mapped["temperature"] = mapped[column].round(1)
    mapped["kind"] = "Ocean grid cell"
    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=mapped,
            get_position="[longitude, latitude]",
            get_fill_color="color",
            get_radius=2600,
            pickable=True,
        )
    ]
    if show_records:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=training_locations,
                get_position="[longitude, latitude]",
                get_fill_color=[255, 255, 255, 230],
                get_line_color=[40, 48, 48, 230],
                get_radius=4400,
                line_width_min_pixels=2,
                stroked=True,
                pickable=True,
            )
        )
    st.subheader(title)
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(latitude=53.5, longitude=-130.5, zoom=4.5),
            layers=layers,
            tooltip={"text": "{kind}\nSea surface: {temperature} °C"},
        ),
        use_container_width=True,
    )
    st.caption(f"{mapped['suitable'].sum():,} of {len(mapped):,} mapped ocean cells match the temperature range.")


left, right = st.columns(2)
with left:
    show_map(current, "baseline_c", "Present ocean · 2010–2020", show_records=True)
with right:
    show_map(future, "ssp245_2050_c", "Future ocean · 2050–2060 (SSP2-4.5)")

st.warning(
    "These maps show a temperature match, not where the species will live. "
    "They include offshore and adjacent waters; they do not account for "
    "shoreline habitat, salinity, light, dispersal, or sampling bias."
)
with st.expander("Data and method"):
    st.write(
        "Each map marker represents a 0.05° Bio-ORACLE ocean grid cell in a "
        "rectangular study area around BC. We take the middle portion selected "
        "above from present-day sea surface temperatures at matched museum "
        "locations, then apply that fixed range to both maps."
    )
    st.caption(
        "Marine temperature: Bio-ORACLE v3 surface ocean temperature, baseline "
        "2010–2020 and SSP2-4.5 2050–2060. Algae locations: UBC Herbarium specimen records."
    )
