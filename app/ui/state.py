"""The two sidebar choices every page depends on, read from session state.

The widgets themselves live in app/streamlit_app.py; pages only read.
"""

from datetime import date

import streamlit as st

ILLUSTRATIVE_KEY = "illustrative"
RUN_DATE_KEY = "run_date"


def is_illustrative() -> bool:
    return bool(st.session_state.get(ILLUSTRATIVE_KEY, False))


def selected_run_date() -> date | None:
    value = st.session_state.get(RUN_DATE_KEY)
    return value if isinstance(value, date) else None
