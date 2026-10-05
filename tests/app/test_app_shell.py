"""Runs the real entry script headlessly with Streamlit's AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.ui.components import ILLUSTRATIVE_BANNER

ENTRY = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")


def banners(at: AppTest) -> list[str]:
    return [w.value for w in at.warning if w.value == ILLUSTRATIVE_BANNER]


def test_real_mode_runs_without_banner():
    at = AppTest.from_file(ENTRY, default_timeout=10).run()
    assert not at.exception
    assert at.toggle(key="illustrative").value is False
    assert banners(at) == []


def test_illustrative_mode_shows_banner_in_sidebar_and_main():
    at = AppTest.from_file(ENTRY, default_timeout=10).run()
    at.toggle(key="illustrative").set_value(True).run()
    assert not at.exception
    assert len(banners(at)) == 2
    assert len(at.sidebar.warning) == 1


def test_run_date_defaults_to_latest():
    at = AppTest.from_file(ENTRY, default_timeout=10).run()
    select = at.selectbox(key="run_date")
    assert select.index == 0  # dates are listed newest first
