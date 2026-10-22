import streamlit as st

from datavis.explorer import date_counts, map_points
from datavis.ui import apply_branding, dataset_client


st.set_page_config(page_title="Browse Museum Records", page_icon="🔎", layout="wide")
apply_branding()
st.title("Browse Museum Records")
st.write(
    "Choose a dataset to see its records, collection dates, and mapped locations."
)
st.page_link(
    "pages/02_Herbarium_Dashboard.py",
    label="Explore Herbarium specimens",
    icon="🌿",
)
client = dataset_client()


@st.cache_data(ttl=86400, show_spinner=False)
def column_labels(slug: str) -> dict[str, str]:
    return dataset_client().column_labels(slug)

try:
    datasets = client.list_datasets()
except Exception:
    st.error("The data service is temporarily unavailable.")
    st.stop()

if not datasets:
    st.info("No museum datasets are available right now.")
    st.stop()

by_title = {item["title"]: item for item in datasets}
selected = by_title[st.selectbox("Dataset", list(by_title))]
st.caption(selected.get("description", ""))

try:
    frame = client.dataframe(selected["slug"])
except Exception:
    st.error("This dataset could not be loaded.")
    st.stop()

try:
    labels = column_labels(selected["slug"])
    frame = frame.rename(columns=labels)
except Exception:
    st.warning("Field names are temporarily unavailable.")

row_metric, field_metric = st.columns(2)
row_metric.metric("Records", f"{len(frame):,}")
field_metric.metric("Fields", f"{len(frame.columns):,}")
st.dataframe(frame, use_container_width=True, hide_index=True)

st.subheader("Records by collection date")
counts = date_counts(frame)
if counts is None:
    st.info("Collection dates are not available for this dataset.")
elif counts.empty:
    st.info("No collection dates are available to chart.")
else:
    st.caption("Each bar counts records collected on one date.")
    st.bar_chart(counts)

st.subheader("Map")
points = map_points(frame)
if points is None:
    st.info("Mapped locations are not available for this dataset.")
elif points.empty:
    st.info("No locations are available to map.")
else:
    st.caption(f"Showing {len(points):,} records with locations.")
    st.map(points, latitude="latitude", longitude="longitude")

numeric = frame.select_dtypes(include="number")
if not numeric.empty:
    st.subheader("Numeric values")
    column = st.selectbox("Field", list(numeric.columns))
    st.bar_chart(numeric[column].value_counts().sort_index())
