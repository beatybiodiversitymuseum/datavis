import streamlit as st

from datavis.ui import apply_branding, dataset_client


st.set_page_config(page_title="Beaty Data Visualizations", page_icon="📊", layout="wide")
apply_branding()
st.title("Beaty Data Visualizations")
st.write("Explore UBC Herbarium specimens, browse museum records, and compare ocean temperatures for an algae species.")

st.divider()
st.header("Explore")
explorer_column, herbarium_column, climate_column = st.columns(3)
with explorer_column:
    st.subheader("🔎 Browse records")
    st.write(
        "Choose a museum dataset to inspect its records, collection dates, and locations."
    )
    st.page_link("pages/01_Browse_Records.py", label="Browse records", icon="🔎")
with herbarium_column:
    st.subheader("🌿 Herbarium Explorer")
    st.write(
        "Filter algae specimens by collector, place, and year. Explore summaries, a map, and a table."
    )
    st.page_link(
        "pages/02_Herbarium_Dashboard.py", label="Explore specimens", icon="🌿"
    )
with climate_column:
    st.subheader("🌊 Algae and ocean temperature")
    st.write(
        "Compare present and future ocean temperatures with those observed near *Fucus gardneri* records."
    )
    st.page_link(
        "pages/03_Algae_Climate_Explorer.py", label="Compare temperatures", icon="🌊"
    )

st.divider()

try:
    datasets = dataset_client().list_datasets()
except Exception:
    st.error("The data service is temporarily unavailable.")
    st.stop()

if not datasets:
    st.info("No museum datasets are available right now.")
else:
    st.header("Available datasets")
    for dataset in datasets:
        st.subheader(dataset["title"])
        st.write(dataset.get("description") or "Museum records available to explore.")
