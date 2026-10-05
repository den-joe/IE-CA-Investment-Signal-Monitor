import streamlit as st

from app.ui import cache
from app.ui.components import dossier_caption, no_run_selected
from app.ui.findings_panel import pipeline_explainer, render_findings
from app.ui.state import is_illustrative, selected_run_date

st.title("Findings")
dossier_caption("The dossier after scoring: every new record this run saved, each with its tier label and gate result.")
pipeline_explainer()

run_date = selected_run_date()
if run_date is None:
    no_run_selected()
else:
    illustrative = is_illustrative()
    render_findings(cache.findings(illustrative, run_date), cache.companies(illustrative), run_date)
