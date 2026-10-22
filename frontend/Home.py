import streamlit as st

from datavis.ui import apply_branding


st.set_page_config(page_title="Beaty Data Visualizations", page_icon="📊", layout="wide")
apply_branding()
st.title("Beaty Data Visualizations")
st.write(
    "This site turns reviewed museum records into focused visualizations. "
    "Each visualization starts with a saved Specify query and a decision about "
    "which fields can be shown publicly."
)

st.header("How a visualization is set up")

st.subheader("1. Prepare and review the records")
st.write(
    "Create a saved query in Specify with the records and fields the visualization "
    "needs. Review its displayed fields and representative results for public "
    "release, including sensitive locations and other restricted information."
)

st.subheader("2. Publish the reviewed dataset")
st.write(
    "Add the reviewed query to the dataset allowlist. The private data service "
    "runs that fixed query and supplies its CSV to the visualization. Visitors "
    "cannot choose a different query or access Specify credentials."
)

st.subheader("3. Build the visualization")
st.write(
    "Add a page that requests the published dataset and uses its actual fields "
    "for tables, filters, charts, or maps. Check that the page still gives a "
    "clear error if required fields are missing."
)

st.subheader("4. Check and release it")
st.write(
    "Test the page against the API's CSV columns and display labels, run the "
    "repository checks, then release the private data service and public site "
    "through the deployment process. Review any later changes to the saved "
    "query before they appear publicly."
)
