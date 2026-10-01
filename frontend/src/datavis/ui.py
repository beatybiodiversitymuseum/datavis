import os
from functools import lru_cache

import streamlit as st

from .config import Settings
from .connections import DatasetClient


def apply_branding() -> None:
    st.markdown(
        """<style>
        :root { --beaty-red: #ed1c24; }
        html, body, [class*="css"] { font-family: Whitney, "Helvetica Neue", Helvetica, Arial, sans-serif; hyphens: none; }
        h1, h2, h3 { font-family: Optima, "Helvetica Neue", Helvetica, Arial, sans-serif; }
        a, [data-testid="stMetricValue"] { color: var(--beaty-red); }
        </style>""",
        unsafe_allow_html=True,
    )


@st.cache_resource
def dataset_client() -> DatasetClient:
    return DatasetClient(Settings.from_environment())
