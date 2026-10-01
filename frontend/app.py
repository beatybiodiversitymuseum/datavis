import streamlit as st

from datavis.ui import apply_branding, dataset_client


st.set_page_config(page_title="Beaty Data Visualizations", page_icon="📊", layout="wide")
apply_branding()
st.title("Beaty Data Visualizations")
st.caption("Curated views of reviewed public collection data")

st.markdown(
    """
    Each visualization starts with a saved Specify query whose fields have been
    reviewed for public use. The service runs that query, turns the result into
    a consistently structured CSV, and gives the Streamlit application only the
    columns it needs for charts, maps, filters, and tables.

    This shared pattern keeps each visualization focused on interpretation and
    presentation while making its source dataset clear and repeatable.
    """
)

flow_query, flow_csv, flow_app = st.columns(3)
flow_query.subheader("1. Reviewed query")
flow_query.write("A numbered Specify query defines the records and fields intended for the visualization.")
flow_csv.subheader("2. Structured CSV")
flow_csv.write("The query result is checked against the app's expected columns and delivered as CSV.")
flow_app.subheader("3. Streamlit app")
flow_app.write("A focused app turns that dataset into useful interactive views.")

st.info(
    "Have collection data you would like to explore visually? Contact Paul Bucci "
    "with the question you want to answer and the Specify data involved."
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
    st.write("Choose an application from the sidebar. Available datasets:")
    for dataset in datasets:
        st.subheader(dataset["title"])
        st.write(dataset.get("description") or "A reviewed Specify saved-query dataset.")
