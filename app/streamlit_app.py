"""Entry point for the analyst dashboard.

Run from the repo root:
    .venv\\Scripts\\python -m streamlit run app/streamlit_app.py

This script owns the sidebar (data-source switch and run date) and the
illustrative-data banner, then hands over to whichever page is selected.
"""

import streamlit as st

from app.ui import cache
from app.ui.components import illustrative_banner, run_date_label
from app.ui.state import ILLUSTRATIVE_KEY, RUN_DATE_KEY

st.set_page_config(page_title="Signal Scanner", page_icon=":material/travel_explore:", layout="wide")

pages = [
    st.Page("views/findings.py", title="Findings", icon=":material/fact_check:", default=True),
    st.Page("views/digest.py", title="Digest", icon=":material/summarize:"),
    st.Page("views/run_overview.py", title="Run overview", icon=":material/filter_alt:"),
    st.Page("views/companies.py", title="Companies", icon=":material/domain:"),
    st.Page("views/pipeline.py", title="Pipeline", icon=":material/account_tree:"),
    st.Page("views/methodology.py", title="Methodology & limits", icon=":material/rule:"),
]
page = st.navigation(pages)

with st.sidebar:
    st.markdown("**Canada–Ireland Signal Scanner**")
    illustrative = st.toggle(
        "Show illustrative sample data",
        key=ILLUSTRATIVE_KEY,
        help="Swaps the whole data source for fictional sample files in "
        "fixtures/illustrative. Real and sample records are never shown together.",
    )
    if illustrative:
        illustrative_banner()

    dates = cache.run_dates(illustrative)
    if dates:
        st.selectbox(
            "Run date",
            options=dates,
            format_func=run_date_label,
            key=RUN_DATE_KEY,
            help="One run per day. A second run on the same day replaces that day's files.",
        )
    else:
        st.session_state.pop(RUN_DATE_KEY, None)
        st.caption("No run files found.")

if illustrative:
    illustrative_banner()

page.run()
