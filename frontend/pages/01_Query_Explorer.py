import streamlit as st

from datavis.explorer import date_counts, map_points
from datavis.ui import apply_branding, dataset_client


st.set_page_config(page_title="Query Explorer", page_icon="🔎", layout="wide")
apply_branding()
st.title("Query Explorer")
st.write(
    "Inspect the rows and displayed fields produced by a reviewed Specify saved query. "
    "This page stays close to the query result; the worked example shows how Streamlit "
    "can turn the same kind of result into a purpose-built dashboard."
)
st.page_link(
    "pages/02_Herbarium_Dashboard.py",
    label="See the Herbarium worked example",
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
    st.info("No reviewed datasets are currently published.")
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
    st.warning("Field labels are temporarily unavailable; showing saved-query names.")

row_metric, field_metric = st.columns(2)
row_metric.metric("Query rows", f"{len(frame):,}")
field_metric.metric("Displayed fields", f"{len(frame.columns):,}")
st.caption(
    "Rows come from the saved query. Column names use Specify's collection-specific "
    "labels when they are available."
)
st.dataframe(frame, use_container_width=True, hide_index=True)

st.subheader("Items by collection date")
counts = date_counts(frame)
if counts is None:
    st.info("This query does not include a collection date field.")
elif counts.empty:
    st.info("No valid collection dates are available for this query.")
else:
    st.caption("Each bar counts query rows for one collection date.")
    st.bar_chart(counts)

st.subheader("Map")
points = map_points(frame)
if points is None:
    st.info("This query does not include latitude and longitude fields.")
elif points.empty:
    st.info("No valid coordinates are available for this query.")
else:
    st.caption(f"Showing {len(points):,} query rows with valid coordinates.")
    st.map(points, latitude="latitude", longitude="longitude")

numeric = frame.select_dtypes(include="number")
if not numeric.empty:
    st.subheader("Quick numeric summary")
    st.caption(
        "Choose any numeric query field to see how often each value occurs—one example "
        "of a visualization Streamlit can create without changing the Specify query."
    )
    column = st.selectbox("Numeric query field", list(numeric.columns))
    st.bar_chart(numeric[column].value_counts().sort_index())
