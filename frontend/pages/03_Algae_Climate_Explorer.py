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
st.set_page_config(page_title="Algae and Ocean Temperature", page_icon="🌊", layout="wide")
apply_branding()
st.title("Fucus gardneri and ocean temperature")
st.write(
    "*Fucus gardneri* is a seaweed represented in the UBC Herbarium's specimen "
    "collection. The collection data records where specimens were found along "
    "the British Columbia coast. This page compares ocean temperatures at "
    "those places with temperatures across the surrounding ocean."
)
locations_column, temperature_column = st.columns(2)
with locations_column:
    st.subheader("Where the seaweed locations come from")
    st.write(
        "A herbarium specimen is a preserved organism kept for study. Its "
        "collection entry gives the species name and the place where it was "
        "found. We use the coordinates of BC specimens identified as "
        "*Fucus gardneri*. White rings on the first map mark the collection "
        "areas used in this comparison."
    )
with temperature_column:
    st.subheader("Where the temperatures come from")
    st.write(
        "Bio-ORACLE estimates average sea surface temperature across ocean "
        "areas around BC. We use its 2010–2020 values at collection areas to "
        "set a temperature range, then apply that range across the mapped "
        "ocean in both 2010–2020 and 2050–2060. These are seawater estimates, "
        "not measurements made when specimens were collected."
    )
st.info(
    "The colors on the maps describe seawater temperature. They do not show "
    "where this seaweed lives or where it will spread."
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

st.header("Temperatures near collected specimens")
st.write(
    "Collection areas do not all have the same seawater temperature. Choose "
    "how much of their temperature variation to include in the comparison. "
    "A narrow range produces fewer matches; a wider range produces more."
)
range_choice = st.radio(
    "Temperature range",
    options=("Narrow (middle 50%)", "Medium (middle 80%)", "Wide (middle 90%)"),
    index=1,
    horizontal=True,
)
tail, range_name = {
    "Narrow (middle 50%)": (0.25, "50%"),
    "Medium (middle 80%)": (0.1, "80%"),
    "Wide (middle 90%)": (0.05, "90%"),
}[range_choice]
minimum, maximum, matched = temperature_envelope(records, species, tail)
total_cells = int(coverage.size)
training_locations = records.loc[
    records["species"].eq(species) & records["baseline_c"].notna(),
    ["latitude", "longitude", "baseline_c"],
].copy()
training_locations["temperature"] = training_locations["baseline_c"].round(1)
training_locations["kind"] = "Area with a Fucus gardneri collection"

st.write(
    f"Of {total_cells:,} small map areas with BC *Fucus gardneri* collections, "
    f"{matched:,} have an ocean temperature estimate. For those areas, the "
    f"middle {range_name} of 2010–2020 temperatures is "
    f"**{minimum:.1f} to {maximum:.1f} °C**. That is the temperature range "
    "used to color both maps below."
)
st.caption(
    f"The other {total_cells - matched:,} collection areas could not be paired "
    "with an ocean temperature and are left out. When several specimens fall "
    "in one small map area, that area counts once. Changing the control above "
    "changes the temperature range; it does not change the specimen locations "
    "or the climate data."
)

current = suitability(grid, minimum, maximum, "baseline_c")
future = suitability(grid, minimum, maximum, "ssp245_2050_c")
st.header("Compare ocean temperatures")
st.write(
    "Each colored dot represents a small area of ocean around BC. Both maps "
    "use the same temperature range shown above. The left map uses average "
    "surface seawater temperature for 2010–2020. The right map uses projected "
    "temperature for 2050–2060 under one possible future emissions scenario."
)
st.markdown(
    '<span style="color:#168777">●</span> Water temperature falls inside the chosen range &nbsp;&nbsp; '
    '<span style="color:#aeb9c0">●</span> Water is colder or warmer &nbsp;&nbsp; '
    '<span style="color:#303838">◉</span> Collection area used to set the range (left map)',
    unsafe_allow_html=True,
)


def show_map(mapped, column: str, title: str, show_records: bool = False):
    mapped = mapped.copy()
    mapped["color"] = mapped["suitable"].map(
        {True: [22, 135, 119, 175], False: [175, 185, 192, 95]}
    )
    mapped["temperature"] = mapped[column].round(1)
    mapped["kind"] = "Area of ocean"
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
    st.caption(
        f"{mapped['suitable'].sum():,} of {len(mapped):,} ocean areas shown "
        "have surface temperatures in the chosen range. This counts ocean "
        "areas, not seaweed locations."
    )


left, right = st.columns(2)
with left:
    show_map(current, "baseline_c", "Average surface seawater · 2010–2020", show_records=True)
with right:
    show_map(future, "ssp245_2050_c", "Projected surface seawater · 2050–2060")

st.warning(
    "A temperature match is only one condition for this seaweed. The maps "
    "include offshore and nearby waters, even where this coastal species "
    "cannot live. They do not account for shoreline habitat, salinity, light, "
    "or how the seaweed spreads."
)
with st.expander("Data and method"):
    st.write(
        "The map covers a rectangle around BC, including offshore and nearby "
        "waters. Bio-ORACLE divides it into 0.05° ocean cells, each several "
        "kilometres across. We use one 2010–2020 surface temperature per cell "
        "containing a collection location. The selected middle portion of "
        "those values sets a fixed temperature range for both maps."
    )
    st.caption(
        "Marine temperature: Bio-ORACLE v3 surface ocean temperature, baseline "
        "2010–2020 and SSP2-4.5 2050–2060. SSP2-4.5 is a future emissions "
        "scenario. Algae locations: UBC Herbarium specimen collection data."
    )
