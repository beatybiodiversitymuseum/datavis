import streamlit as st

from datavis.ui import apply_branding, dataset_client


st.set_page_config(page_title="Beaty Data Visualizations", page_icon="📊", layout="wide")
apply_branding()
st.title("Beaty Data Visualizations")
st.subheader("From a reviewed Specify query to an interactive public view")

st.markdown(
    """
    **Specify decides what data is included.** A collection manager creates a
    saved query that selects the records and fields needed to answer a question.
    Those fields are reviewed before the query is published here.

    **Streamlit decides how people can explore it.** The reviewed query result
    becomes an interactive page with filters, summaries, charts, maps, tables,
    and downloads. Streamlit cannot request a different Specify query or expose
    collection credentials.
    """
)

st.markdown("#### 1. Define the dataset in Specify")
st.write(
    "A saved query controls which specimen records appear and which columns leave Specify."
)
st.markdown("#### 2. Review and publish the query")
st.write(
    "Museum staff review the displayed fields, then publish that query as a named dataset."
)
st.markdown("#### 3. Explore the result in Streamlit")
st.write(
    "A focused app can filter, summarize, chart, map, display, and download the reviewed rows."
)

st.divider()
st.header("Two ways to explore")
explorer_column, example_column = st.columns(2)
with explorer_column:
    st.subheader("🔎 Query Explorer")
    st.write(
        "See a reviewed saved query much as it leaves Specify: one row per result "
        "and one column per displayed query field. This is the best place to check "
        "what data is available before designing a visualization."
    )
    st.page_link("pages/01_Query_Explorer.py", label="Open Query Explorer", icon="🔎")
with example_column:
    st.subheader("🌿 Herbarium Explorer")
    st.write(
        "See what Streamlit can add to one saved query: linked filters, live counts, "
        "charts, a map, a searchable table, and a filtered CSV download."
    )
    st.page_link(
        "pages/02_Herbarium_Dashboard.py", label="Open the worked example", icon="🌿"
    )

st.subheader("🌊 Algae Climate Explorer")
st.write(
    "Try a classroom sea temperature envelope using reviewed algae occurrences "
    "and Bio-ORACLE present and future marine climate grids."
)
st.page_link(
    "pages/03_Algae_Climate_Explorer.py", label="Open the climate example", icon="🌊"
)

st.info(
    "Want to build another view? Start with the question you want to answer and a "
    "Specify saved query containing only the records and fields approved for public use."
)

st.divider()

try:
    datasets = dataset_client().list_datasets()
except Exception:
    st.error("The data service is temporarily unavailable.")
    st.stop()

if not datasets:
    st.info("The first reviewed visualization is being prepared.")
else:
    st.header("Published datasets")
    st.caption(
        "Each dataset below is backed by a fixed, reviewed Specify saved query."
    )
    for dataset in datasets:
        st.subheader(dataset["title"])
        st.write(
            dataset.get("description") or "A reviewed Specify saved-query dataset."
        )
