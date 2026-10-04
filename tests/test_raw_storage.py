import json

import pytest

from src.storage import load_raw_entries, write_raw_entries
from src.storage import raw


@pytest.fixture(autouse=True)
def raw_dir(tmp_path, monkeypatch):
    path = tmp_path / "raw"
    monkeypatch.setattr(raw, "RAW_DIR", path)
    return path


def make_entry(url: str) -> dict:
    return {"signal_text": "text", "date_mentioned": "2026-09-28", "source_url": url}


def test_write_raw_entries_creates_dated_file(raw_dir):
    write_raw_entries([make_entry("https://a")], run_date="2026-09-28")

    data = json.loads((raw_dir / "2026-09-28.json").read_text(encoding="utf-8"))
    assert data["date"] == "2026-09-28"
    assert data["entries"] == [make_entry("https://a")]


def test_round_trip_by_date():
    write_raw_entries([make_entry("https://a")], run_date="2026-09-27")
    write_raw_entries([make_entry("https://b")], run_date="2026-09-28")

    assert load_raw_entries("2026-09-27") == [make_entry("https://a")]


def test_load_without_date_returns_latest_file():
    write_raw_entries([make_entry("https://a")], run_date="2026-09-27")
    write_raw_entries([make_entry("https://b")], run_date="2026-09-28")

    assert load_raw_entries() == [make_entry("https://b")]


def test_load_when_nothing_saved_raises():
    with pytest.raises(FileNotFoundError):
        load_raw_entries()


def test_load_missing_date_raises():
    write_raw_entries([make_entry("https://a")], run_date="2026-09-27")

    with pytest.raises(FileNotFoundError):
        load_raw_entries("2026-01-01")


def test_same_day_write_overwrites_earlier_file():
    write_raw_entries([make_entry("https://a")], run_date="2026-09-28")
    write_raw_entries([make_entry("https://b")], run_date="2026-09-28")

    assert load_raw_entries("2026-09-28") == [make_entry("https://b")]
