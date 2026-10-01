import streamlit as st

from datavis.ui import apply_branding, dataset_client


st.set_page_config(page_title="Query Explorer", page_icon="🔎", layout="wide")
apply_branding()
st.title("Query Explorer")
client = dataset_client()

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

st.metric("Rows", f"{len(frame):,}")
st.dataframe(frame, use_container_width=True, hide_index=True)
numeric = frame.select_dtypes(include="number")
if not numeric.empty:
    column = st.selectbox("Numeric field", list(numeric.columns))
    st.bar_chart(numeric[column].value_counts().sort_index())
