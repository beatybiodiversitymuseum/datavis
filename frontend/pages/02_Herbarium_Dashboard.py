import pandas as pd
import streamlit as st

from datavis.herbarium import HerbariumSchemaError, prepare_herbarium_data
from datavis.ui import apply_branding, dataset_client


st.set_page_config(page_title="UBC Herbarium Explorer", page_icon="🌿", layout="wide")
apply_branding()
st.markdown(
    """<style>
    .main { background-color: #f8f6f1; }
    .block-container { padding-top: 2rem; }
    [data-testid="metric-container"] {
        background: white; border: 1px solid #e0ddd5; border-radius: 8px;
        padding: 1rem 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    [data-testid="stSidebar"] { background-color: #1f2e1f; }
    [data-testid="stSidebar"] * { color: #d4e8d4; }
    .data-note {
        background: #fdf8ee; border-left: 3px solid #c8a951;
        padding: .7rem 1rem; border-radius: 0 6px 6px 0;
    }
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=86400, show_spinner="Loading collection data…")
def load_data() -> pd.DataFrame:
    return prepare_herbarium_data(dataset_client().dataframe("herbarium-algae"))


try:
    df = load_data()
except HerbariumSchemaError as error:
    st.error(f"The saved query does not currently match this dashboard: {error}")
    st.stop()
except Exception:
    st.error("The Herbarium dataset could not be loaded.")
    st.stop()

if df.empty:
    st.info("The Herbarium query returned no specimens.")
    st.stop()

st.sidebar.title("🌿 Herbarium Explorer")
st.sidebar.markdown("### Filters")

collectors = sorted(df["full_name"].dropna().unique())
countries = sorted(value for value in df["country"].unique() if value != "Unknown")
selected_collectors = st.sidebar.multiselect("Collectors", collectors)
selected_countries = st.sidebar.multiselect("Countries", countries)

if selected_countries:
    province_source = df[df["country"].isin(selected_countries)]
else:
    province_source = df
provinces = sorted(
    value for value in province_source["province"].unique() if value != "Unknown"
)
selected_provinces = st.sidebar.multiselect("Provinces / states", provinces)

years = df["year"].dropna()
year_range = None
if not years.empty:
    year_min, year_max = int(years.min()), int(years.max())
    year_range = st.sidebar.slider(
        "Collection year", year_min, year_max, (year_min, year_max)
    )

filtered = df.copy()
if selected_collectors:
    filtered = filtered[filtered["full_name"].isin(selected_collectors)]
if selected_countries:
    filtered = filtered[filtered["country"].isin(selected_countries)]
if selected_provinces:
    filtered = filtered[filtered["province"].isin(selected_provinces)]
if year_range:
    filtered = filtered[
        filtered["year"].isna()
        | filtered["year"].between(year_range[0], year_range[1])
    ]

with_date = int(filtered["collection_date"].notna().sum())
with_coords = int(filtered[["latitude", "longitude"]].notna().all(axis=1).sum())
st.sidebar.caption(f"{len(filtered):,} specimens match the filters")
st.sidebar.caption(f"📅 {with_date:,} have collection dates")
st.sidebar.caption(f"📍 {with_coords:,} have coordinates")

st.title("UBC Herbarium Explorer")
st.info("This dashboard currently represents the algae portion of the UBC Herbarium collection.")

total_collection = 102_862
st.markdown(
    f"""<div style="background:#1f2e1f;border-radius:10px;padding:1.2rem 2rem;
    margin-bottom:1.2rem;color:#d4e8d4">
    <span style="font-size:2.6rem;font-weight:600">{total_collection:,}</span><br>
    Total physical specimens in the collection · {len(df):,} algae query rows
    </div>""",
    unsafe_allow_html=True,
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Filtered Specimens", f"{len(filtered):,}")
metric_2.metric("Collectors", f"{filtered['full_name'].nunique():,}")
metric_3.metric("With Dates", f"{with_date:,}")
metric_4.metric("Georeferenced", f"{with_coords:,}")

if filtered.empty:
    st.warning("No specimens match the current filters.")
    st.stop()

st.markdown("---")
st.subheader("Specimens per Collector")
collector_counts = filtered["full_name"].value_counts()
if len(collector_counts) <= 5:
    top_collectors = len(collector_counts)
else:
    top_collectors = st.slider(
        "Collectors to display",
        min_value=5,
        max_value=min(100, len(collector_counts)),
        value=min(30, len(collector_counts)),
    )
st.bar_chart(collector_counts.head(top_collectors), horizontal=True)

st.markdown("---")
st.subheader("Collection Activity")
dated = filtered.dropna(subset=["year"]).copy()
if dated.empty:
    st.info("No dated specimens match the current filters.")
else:
    dated["year"] = dated["year"].astype(int)
    activity = dated.groupby("year").size().rename("Specimens")
    st.bar_chart(activity)

st.markdown("---")
st.subheader("Collector Timeline")
if dated.empty:
    st.info("No collector timeline is available for the current filters.")
else:
    timeline = (
        dated.groupby("full_name")
        .agg(
            first_collection=("year", "min"),
            last_collection=("year", "max"),
            specimens=("catalognumber", "count"),
        )
        .reset_index()
        .sort_values(["specimens", "full_name"], ascending=[False, True])
    )
    timeline["active_span"] = timeline["last_collection"] - timeline["first_collection"]
    st.dataframe(
        timeline.head(100),
        use_container_width=True,
        hide_index=True,
        column_config={
            "full_name": "Collector",
            "first_collection": "First Collection",
            "last_collection": "Last Collection",
            "specimens": "Specimens",
            "active_span": "Active Span (years)",
        },
    )

st.markdown("---")
st.subheader("Geographic Distribution")
map_data = filtered.dropna(subset=["latitude", "longitude"])[
    ["latitude", "longitude"]
]
if map_data.empty:
    st.info("No georeferenced specimens match the current filters.")
else:
    if len(map_data) > 5_000:
        st.markdown(
            '<div class="data-note">Displaying a stable sample of 5,000 points for map performance.</div>',
            unsafe_allow_html=True,
        )
        map_data = map_data.sample(5_000, random_state=42)
    st.map(map_data, latitude="latitude", longitude="longitude")

st.markdown("---")
title_column, download_column = st.columns([6, 1])
title_column.subheader("Specimen Records")
records = filtered[
    [
        "catalognumber",
        "full_name",
        "collection_date",
        "country",
        "province",
        "localityname",
        "latitude",
        "longitude",
    ]
].rename(
    columns={
        "catalognumber": "Catalog #",
        "full_name": "Collector",
        "collection_date": "Date",
        "country": "Country",
        "province": "Province/State",
        "localityname": "Locality",
        "latitude": "Lat",
        "longitude": "Lon",
    }
)
download_column.download_button(
    "⬇ CSV",
    records.to_csv(index=False),
    "herbarium_specimens.csv",
    "text/csv",
    use_container_width=True,
)
st.dataframe(records.head(5_000), use_container_width=True, hide_index=True)
if len(records) > 5_000:
    st.caption(f"Showing 5,000 of {len(records):,} matching rows; the download contains all rows.")
