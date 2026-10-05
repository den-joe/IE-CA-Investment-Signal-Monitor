"""Rendering for the Findings page: every record the selected run saved, with
drill-down per record. Kept out of app/views/findings.py so tests can call
render_findings() with hand-made data without running the page script."""

from datetime import date

import streamlit as st

from app.core.models import Company, Finding, LoadResult, SourceType
from app.core.selectors import FindingFilter, count_by_tier, filter_findings, sort_findings
from app.core.tiers import SECTORS, sector_label, tier_info
from app.ui.components import (
    gate_badge,
    load_problem,
    md_escape,
    run_date_label,
    skipped_note,
    source_line,
    tier_badge,
    tier_label,
    truncate,
)

PAGE_SIZE = 50
GATE_OPTIONS = ["All", "Passed", "Not passed"]
GATE_VALUES = {"All": "all", "Passed": "passed", "Not passed": "failed"}

# Widget keys, so "Clear filters" can reset them.
K_SECTORS, K_TIERS, K_GATE, K_COMPANIES, K_SEARCH = "f_sectors", "f_tiers", "f_gate", "f_companies", "f_search"
K_NON_SIGNALS, K_SORT, K_PAGE = "f_non_signals", "f_sort", "f_page"


def _clear_filters() -> None:
    for key in (K_SECTORS, K_TIERS, K_COMPANIES):
        st.session_state[key] = []
    st.session_state[K_GATE] = "All"
    st.session_state[K_SEARCH] = ""
    st.session_state[K_NON_SIGNALS] = False
    st.session_state[K_PAGE] = 1


def pipeline_explainer() -> None:
    with st.expander("How this page relates to the pipeline"):
        st.markdown(
            "**Analogy.** The dossier after the last specialist has stamped every page: "
            "each page names a company, carries a tier label, and has been checked against the "
            "market-cap gate.\n\n"
            "**Plain English.** Each row is one record this run saved. It was matched to a "
            "tracked company, given a tier by the AI classifier, checked against earlier runs so "
            "only new records remain, and gate-checked on market cap.\n\n"
            "**Code.** `persist_run` in `src/graph.py` calls `write_run(state[\"records\"])`, "
            "which writes `data/runs/<date>.json`.\n\n"
            "**What happens to the state.** `records` is a list of `company, sector, signal_text, "
            "tier, date_mentioned, source_url, gate_passed, gate_reason`. The file does not store "
            "the source type, so this page recovers it by matching `source_url` against the same "
            "day's raw entries file."
        )


def _summary(result: LoadResult[Finding], shown: list[Finding], flt: FindingFilter, run_date: date | None) -> None:
    total = len(result.items)
    when = f" on {run_date_label(run_date)}" if run_date else ""

    if total == 0:
        st.markdown(
            f"This run saved no records{when}. The entries it collected are listed on Run overview."
        )
        return

    tiers = count_by_tier(result.items)
    non_signals = tiers.get(0, 0)

    if shown:
        st.markdown(f"Showing {len(shown)} of {total} records saved{when}.")
    elif non_signals == total and not flt.show_non_signals:
        st.markdown(
            f"This run saved {total} records{when}. All {total} are Tier 0 (not a signal), "
            "so none are shown. Turn on **Show non-signals** to see them."
        )
    else:
        message = "No records match these filters."
        if flt.sectors and not any(f.sector in flt.sectors for f in result.items):
            names = ", ".join(sector_label(s) for s in sorted(flt.sectors))
            message += f" This run has no records in {names}."
        st.markdown(message)

    if any(f.source is SourceType.NEWS for f in shown):
        st.caption(
            "Records from the News API are labelled corroboration. The methodology says news "
            "should not originate a finding; whether it may is an open decision."
        )
    if shown and all(f.source is SourceType.UNKNOWN for f in shown):
        st.caption(
            "The source type could not be recovered for these records: there is no raw entries "
            "file for this date, or their links are not in it."
        )


def _record_row(f: Finding, position: int, total: int) -> None:
    with st.container(border=True):
        st.markdown(f"{tier_badge(f.tier)} {gate_badge(f.gate_passed)}")
        st.markdown(f"**{md_escape(f.company)}**  \n{md_escape(truncate(f.signal_text))}")
        st.caption(
            f"{sector_label(f.sector)}, mentioned {md_escape(f.date_mentioned.display())}, "
            f"via {f.source.label} ({f.source.role})"
        )
        with st.expander("Details"):
            info = tier_info(f.tier)
            st.markdown(f"**{tier_label(f.tier)}**  \n{md_escape(info.definition)}")
            st.markdown("**Full text**")
            st.markdown(md_escape(f.signal_text))
            st.markdown(f"**Source**  \n{source_line(f.source_url, f.source, f.date_mentioned)}")
            if f.date_mentioned.value is None and f.date_mentioned.raw:
                st.caption("The date could not be parsed; shown as the source wrote it.")
            gate_word = "passed" if f.gate_passed else "not passed"
            st.markdown(f"**Market-cap gate: {gate_word}**  \n{md_escape(f.gate_reason)}")
            st.caption(f"Record {position} of {total} in this run's file.")


def render_findings(
    result: LoadResult[Finding],
    companies: LoadResult[Company],
    run_date: date | None = None,
) -> None:
    if not result.ok:
        load_problem(result, "records")
        return
    skipped_note(result)

    # Defaults via session state, not default=, because "Clear filters" also
    # writes these keys and Streamlit warns when both are used.
    st.session_state.setdefault(K_GATE, "All")
    st.session_state.setdefault(K_SORT, "Tier")

    filter_area = st.container()
    options_area = st.container()

    # Drawn first in code (the tier list depends on it), shown second on the page.
    with options_area:
        left, middle, right = st.columns([2, 2, 1])
        show_non_signals = left.toggle("Show non-signals (Tier 0)", key=K_NON_SIGNALS)
        sort_choice = middle.segmented_control("Sort by", ["Tier", "Date"], key=K_SORT)
        right.button("Clear filters", on_click=_clear_filters)

    tier_options = [1, 2, 3, 4] + ([0] if show_non_signals else [])
    if K_TIERS in st.session_state:
        st.session_state[K_TIERS] = [t for t in st.session_state[K_TIERS] if t in tier_options]

    company_names = sorted({c.name for c in companies.items} | {f.company for f in result.items})

    with filter_area:
        # Gate gets the widest column: its three-option control clips below ~260px.
        c1, c2, c3, c4, c5 = st.columns([2, 2, 3, 2, 2])
        sectors = c1.multiselect("Sector", list(SECTORS), format_func=sector_label, key=K_SECTORS, placeholder="All")
        tiers = c2.multiselect("Tier", tier_options, format_func=tier_label, key=K_TIERS, placeholder="All")
        gate_choice = c3.segmented_control("Gate", GATE_OPTIONS, key=K_GATE)
        chosen = c4.multiselect("Company", company_names, key=K_COMPANIES, placeholder="All")
        search = c5.text_input("Search text", key=K_SEARCH, placeholder="Any word")

    flt = FindingFilter(
        sectors=frozenset(sectors),
        tiers=frozenset(tiers),
        gate=GATE_VALUES.get(gate_choice or "All", "all"),  # type: ignore[arg-type]
        companies=frozenset(chosen),
        text=search,
        show_non_signals=show_non_signals,
    )
    shown = sort_findings(filter_findings(result.items, flt), "date" if sort_choice == "Date" else "tier")

    _summary(result, shown, flt, run_date)

    pages = max(1, -(-len(shown) // PAGE_SIZE))
    page = 1
    if pages > 1:
        page = int(st.number_input(f"Page (of {pages})", 1, pages, 1, key=K_PAGE))
    positions = {id(f): i + 1 for i, f in enumerate(result.items)}
    for f in shown[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]:
        _record_row(f, positions[id(f)], len(result.items))
