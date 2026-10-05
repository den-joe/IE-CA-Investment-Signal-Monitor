"""Cached reads. Each public function looks up the file's modification time
and passes it to a cached inner function, so editing a data file on disk
invalidates the cache without restarting the app."""

import os
from datetime import date
from pathlib import Path

import streamlit as st

from app.core.models import Company, Finding, LoadResult, RawEntry
from app.core.repository import ILLUSTRATIVE_DIR, REAL_COMPANIES_PATH, REAL_DATA_DIR, get_repository


def _data_dir(illustrative: bool) -> Path:
    return ILLUSTRATIVE_DIR if illustrative else REAL_DATA_DIR


def _mtime(*paths: Path) -> tuple[float, ...]:
    stamps = []
    for path in paths:
        try:
            stamps.append(os.stat(path).st_mtime)
        except OSError:
            stamps.append(0.0)
    return tuple(stamps)


def _folder_mtime(illustrative: bool) -> tuple[float, ...]:
    base = _data_dir(illustrative)
    return _mtime(base / "runs", base / "raw")


@st.cache_data(show_spinner=False)
def _run_dates(illustrative: bool, stamp: tuple[float, ...]) -> list[date]:
    return get_repository(illustrative).list_run_dates()


@st.cache_data(show_spinner=False)
def _findings(illustrative: bool, run_date: date, stamp: tuple[float, ...]) -> LoadResult[Finding]:
    return get_repository(illustrative).load_findings(run_date)


@st.cache_data(show_spinner=False)
def _raw(illustrative: bool, run_date: date, stamp: tuple[float, ...]) -> LoadResult[RawEntry]:
    return get_repository(illustrative).load_raw(run_date)


@st.cache_data(show_spinner=False)
def _all_findings(illustrative: bool, stamp: tuple[float, ...]) -> dict[date, LoadResult[Finding]]:
    return get_repository(illustrative).load_all_findings()


@st.cache_data(show_spinner=False)
def _companies(illustrative: bool, stamp: tuple[float, ...]) -> LoadResult[Company]:
    return get_repository(illustrative).load_companies()


def run_dates(illustrative: bool) -> list[date]:
    return _run_dates(illustrative, _folder_mtime(illustrative))


def findings(illustrative: bool, run_date: date) -> LoadResult[Finding]:
    base = _data_dir(illustrative)
    name = f"{run_date.isoformat()}.json"
    return _findings(illustrative, run_date, _mtime(base / "runs" / name, base / "raw" / name))


def raw_entries(illustrative: bool, run_date: date) -> LoadResult[RawEntry]:
    path = _data_dir(illustrative) / "raw" / f"{run_date.isoformat()}.json"
    return _raw(illustrative, run_date, _mtime(path))


def all_findings(illustrative: bool) -> dict[date, LoadResult[Finding]]:
    runs = sorted((_data_dir(illustrative) / "runs").glob("*.json"))
    return _all_findings(illustrative, _folder_mtime(illustrative) + _mtime(*runs))


def companies(illustrative: bool) -> LoadResult[Company]:
    path = ILLUSTRATIVE_DIR / "companies.yaml" if illustrative else REAL_COMPANIES_PATH
    return _companies(illustrative, _mtime(path))
