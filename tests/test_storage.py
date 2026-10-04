import json

import pytest

from src.storage import load_seen_keys, write_run
from src.storage import runs


@pytest.fixture(autouse=True)
def runs_dir(tmp_path, monkeypatch):
    path = tmp_path / "runs"
    monkeypatch.setattr(runs, "RUNS_DIR", path)
    return path


def make_record(company: str, url: str) -> dict:
    return {"company": company, "source_url": url, "tier": 1}


def test_write_run_creates_dated_file(runs_dir):
    write_run([make_record("Open Text Corp.", "https://a")], run_date="2026-09-28")

    data = json.loads((runs_dir / "2026-09-28.json").read_text(encoding="utf-8"))
    assert data["date"] == "2026-09-28"
    assert data["records"] == [make_record("Open Text Corp.", "https://a")]


def test_write_run_with_no_records_still_writes_a_file(runs_dir):
    write_run([], run_date="2026-09-28")

    assert (runs_dir / "2026-09-28.json").exists()


def test_write_run_same_day_overwrites_earlier_run(runs_dir):
    # Documented limitation: one run per day.
    write_run([make_record("Open Text Corp.", "https://a")], run_date="2026-09-28")
    write_run([make_record("BlackBerry Ltd.", "https://b")], run_date="2026-09-28")

    assert load_seen_keys() == {("BlackBerry Ltd.", "https://b")}


def test_load_seen_keys_when_no_runs_exist():
    assert load_seen_keys() == set()


def test_load_seen_keys_round_trip_across_runs():
    write_run([make_record("Open Text Corp.", "https://a")], run_date="2026-09-27")
    write_run([make_record("BlackBerry Ltd.", "https://b")], run_date="2026-09-28")

    assert load_seen_keys() == {
        ("Open Text Corp.", "https://a"),
        ("BlackBerry Ltd.", "https://b"),
    }


def test_load_seen_keys_skips_corrupt_files(runs_dir):
    write_run([make_record("Open Text Corp.", "https://a")], run_date="2026-09-27")
    (runs_dir / "2026-09-28.json").write_text("{not json", encoding="utf-8")

    assert load_seen_keys() == {("Open Text Corp.", "https://a")}
