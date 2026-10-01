import streamlit as st

from datavis.ui import apply_branding, dataset_client


st.set_page_config(page_title="Beaty Data Visualizations", page_icon="📊", layout="wide")
apply_branding()
st.title("Beaty Data Visualizations")
st.caption("Curated views of reviewed public collection data")

try:
    datasets = dataset_client().list_datasets()
except Exception:
    st.error("The data service is temporarily unavailable.")
    st.stop()

if not datasets:
    st.info("No public visualization datasets have been configured yet.")
else:
    st.write("Choose an application from the sidebar. Available datasets:")
    for dataset in datasets:
        st.subheader(dataset["title"])
        st.write(dataset.get("description") or "A reviewed Specify saved-query dataset.")
