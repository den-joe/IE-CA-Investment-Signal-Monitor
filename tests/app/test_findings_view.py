"""Findings page, run through the real entry script with AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.ui.components import md_escape, truncate

ENTRY = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")


def details_count(at: AppTest) -> int:
    return sum(1 for e in at.expander if e.label == "Details")


def page_text(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown) + "\n".join(c.value for c in at.caption)


def illustrative_app() -> AppTest:
    at = AppTest.from_file(ENTRY, default_timeout=15).run()
    at.toggle(key="illustrative").set_value(True).run()
    return at


# --- helpers -------------------------------------------------------------

def test_md_escape_stops_dollar_signs_rendering_as_maths():
    assert md_escape("$100-million deal") == "\\$100-million deal"
    assert md_escape("a_b *c* [d]") == "a\\_b \\*c\\* \\[d\\]"


def test_truncate():
    assert truncate("short") == "short"
    long = "word " * 100
    out = truncate(long, 40)
    assert len(out) <= 40 and out.endswith("…")


# --- illustrative data ---------------------------------------------------

def test_illustrative_defaults_hide_tier_zero():
    at = illustrative_app()
    assert not at.exception
    assert details_count(at) == 6
    text = page_text(at)
    assert "inference" in text and "context only" in text
    assert "Showing 6 of 8 records" in text


def test_show_non_signals_reveals_all_rows():
    at = illustrative_app()
    at.toggle(key="f_non_signals").set_value(True).run()
    assert not at.exception
    assert details_count(at) == 8


def test_sector_and_gate_filters():
    at = illustrative_app()
    at.multiselect(key="f_sectors").set_value(["life_sciences"]).run()
    assert details_count(at) == 2
    at.multiselect(key="f_sectors").set_value([]).run()
    at.segmented_control(key="f_gate").set_value("Not passed").run()
    assert details_count(at) == 2
    assert not at.exception


def test_search_with_no_matches_explains_itself():
    at = illustrative_app()
    at.text_input(key="f_search").set_value("zzz-no-such-text").run()
    assert details_count(at) == 0
    assert "No records match these filters." in page_text(at)


def test_replacement_character_record_renders():
    at = illustrative_app()
    at.toggle(key="f_non_signals").set_value(True).run()
    assert not at.exception
    assert "�" in page_text(at)


def test_clear_filters_resets_everything():
    at = illustrative_app()
    at.multiselect(key="f_sectors").set_value(["fintech"]).run()
    at.button[0].click().run()
    assert details_count(at) == 6
    assert not at.exception


# --- real data -----------------------------------------------------------

def test_real_mode_runs_and_explains_tier_zero():
    at = AppTest.from_file(ENTRY, default_timeout=15).run()
    assert not at.exception
    text = page_text(at)
    # Real data changes daily; only check the page explains what it shows.
    assert "records" in text or "No run files" in text


# --- file problems -------------------------------------------------------

def test_malformed_file_shows_warning_and_no_rows():
    def script():
        from app.core.models import LoadResult
        from app.ui.findings_panel import render_findings

        render_findings(LoadResult("malformed", (), "data/runs/x.json is not valid JSON."), LoadResult("ok", (), ""))

    at = AppTest.from_function(script, default_timeout=15).run()
    assert not at.exception
    assert len(at.warning) == 1 and "not valid JSON" in at.warning[0].value
    assert details_count(at) == 0


def test_missing_file_shows_info_and_no_rows():
    def script():
        from app.core.models import LoadResult
        from app.ui.findings_panel import render_findings

        render_findings(LoadResult("missing", (), "data/runs/x.json does not exist."), LoadResult("ok", (), ""))

    at = AppTest.from_function(script, default_timeout=15).run()
    assert not at.exception
    assert len(at.info) == 1 and "does not exist" in at.info[0].value
    assert details_count(at) == 0
