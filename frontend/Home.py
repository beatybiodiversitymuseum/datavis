import streamlit as st

from datavis.ui import apply_branding


st.set_page_config(page_title="Beaty Data Visualizations", page_icon="📊", layout="wide")
apply_branding()
st.title("Beaty Data Visualizations")
st.write("Explore UBC Herbarium specimens and compare ocean temperatures for an algae species.")

st.divider()
st.header("Explore")
herbarium_column, climate_column = st.columns(2)
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
        "See where *Fucus gardneri* specimens were collected in BC, then compare "
        "present and projected surface seawater temperatures around those locations."
    )
    st.page_link(
        "pages/03_Algae_Climate_Explorer.py", label="Compare temperatures", icon="🌊"
    )
