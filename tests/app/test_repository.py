import json
from datetime import date

import pytest

from app.core.models import SourceType
from app.core.repository import FileRepository

RUN_DATE = date(2026, 10, 4)


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "runs").mkdir()
    (tmp_path / "raw").mkdir()
    return FileRepository(tmp_path, tmp_path / "companies.yaml", "real")


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def make_record(**overrides):
    record = {
        "company": "Open Text Corp.",
        "sector": "ai_cloud",
        "signal_text": "Some text",
        "tier": 0,
        "date_mentioned": "2026-09-22T06:45:17Z",
        "source_url": "https://a",
        "gate_passed": True,
        "gate_reason": "Market cap CAD 1 meets the threshold",
    }
    return {**record, **overrides}


def make_entry(**overrides):
    entry = {
        "signal_text": "Some text",
        "date_mentioned": "2026-10-02T17:26:00-04:00",
        "source_url": "https://a",
        "source": "News API (corroboration)",
        "fetched_at": "2026-10-04T16:52:47.987227",
        "query": "Open Text Corp.",
    }
    return {**entry, **overrides}


# --- file-level failures -------------------------------------------------

def test_missing_run_file(repo):
    result = repo.load_findings(RUN_DATE)
    assert result.status == "missing"
    assert result.items == ()
    assert "does not exist" in result.message


def test_empty_run_file(repo, tmp_path):
    (tmp_path / "runs" / "2026-10-04.json").write_text("", encoding="utf-8")
    assert repo.load_findings(RUN_DATE).status == "empty"


def test_malformed_json(repo, tmp_path):
    (tmp_path / "runs" / "2026-10-04.json").write_text("{not json", encoding="utf-8")
    result = repo.load_findings(RUN_DATE)
    assert result.status == "malformed"
    assert "not valid JSON" in result.message


def test_wrong_top_level_shape(repo, tmp_path):
    write_json(tmp_path / "runs" / "2026-10-04.json", ["a", "list"])
    assert repo.load_findings(RUN_DATE).status == "malformed"


def test_run_with_zero_records_is_ok_not_an_error(repo, tmp_path):
    write_json(tmp_path / "runs" / "2026-10-04.json", {"date": "2026-10-04", "records": []})
    result = repo.load_findings(RUN_DATE)
    assert result.status == "ok"
    assert result.items == ()


def test_rows_missing_required_keys_are_skipped_and_counted(repo, tmp_path):
    bad = make_record()
    del bad["company"]
    write_json(
        tmp_path / "runs" / "2026-10-04.json",
        {"records": [make_record(), bad, make_record(tier="1")]},
    )
    result = repo.load_findings(RUN_DATE)
    assert len(result.items) == 1
    assert result.skipped_rows == 2


def test_missing_raw_file(repo):
    assert repo.load_raw(RUN_DATE).status == "missing"


def test_malformed_companies_yaml(repo, tmp_path):
    (tmp_path / "companies.yaml").write_text("companies: [unclosed", encoding="utf-8")
    assert repo.load_companies().status == "malformed"


def test_missing_companies_yaml(repo):
    assert repo.load_companies().status == "missing"


# --- row-level quirks ----------------------------------------------------

def test_empty_source_url_becomes_none(repo, tmp_path):
    write_json(
        tmp_path / "raw" / "2026-10-04.json",
        {"entries": [make_entry(source_url="", source="IE inward-investment agency")]},
    )
    entry = repo.load_raw(RUN_DATE).items[0]
    assert entry.source_url is None
    assert entry.source is SourceType.IDA


def test_replacement_character_survives_unchanged(repo, tmp_path):
    text = "Revenue up � guidance raised"
    write_json(tmp_path / "runs" / "2026-10-04.json", {"records": [make_record(signal_text=text)]})
    assert repo.load_findings(RUN_DATE).items[0].signal_text == text


def test_free_text_date_falls_back_to_raw(repo, tmp_path):
    write_json(
        tmp_path / "runs" / "2026-10-04.json",
        {"records": [make_record(date_mentioned="Autumn 2026")]},
    )
    finding = repo.load_findings(RUN_DATE).items[0]
    assert finding.date_mentioned.value is None
    assert finding.date_mentioned.display() == "Autumn 2026"


def test_missing_gate_result_fails_closed(repo, tmp_path):
    record = make_record()
    del record["gate_passed"], record["gate_reason"]
    write_json(tmp_path / "runs" / "2026-10-04.json", {"records": [record]})
    finding = repo.load_findings(RUN_DATE).items[0]
    assert finding.gate_passed is False
    assert finding.gate_reason == "Gate result not recorded"


def test_unknown_source_label_is_unknown(repo, tmp_path):
    write_json(tmp_path / "raw" / "2026-10-04.json", {"entries": [make_entry(source="Something new")]})
    entry = repo.load_raw(RUN_DATE).items[0]
    assert entry.source is SourceType.UNKNOWN
    assert entry.source_label == "Something new"


# --- source join ---------------------------------------------------------

def test_finding_gets_source_from_same_day_raw_file(repo, tmp_path):
    write_json(tmp_path / "runs" / "2026-10-04.json", {"records": [make_record(source_url="https://a")]})
    write_json(tmp_path / "raw" / "2026-10-04.json", {"entries": [make_entry(source_url="https://a")]})
    assert repo.load_findings(RUN_DATE).items[0].source is SourceType.NEWS


def test_finding_url_not_in_raw_is_unknown(repo, tmp_path):
    write_json(tmp_path / "runs" / "2026-10-04.json", {"records": [make_record(source_url="https://zzz")]})
    write_json(tmp_path / "raw" / "2026-10-04.json", {"entries": [make_entry(source_url="https://a")]})
    assert repo.load_findings(RUN_DATE).items[0].source is SourceType.UNKNOWN


def test_finding_without_raw_file_is_unknown(repo, tmp_path):
    write_json(tmp_path / "runs" / "2026-10-04.json", {"records": [make_record()]})
    result = repo.load_findings(RUN_DATE)
    assert result.status == "ok"
    assert result.items[0].source is SourceType.UNKNOWN


# --- run-date discovery --------------------------------------------------

def test_run_dates_union_of_runs_and_raw_newest_first(repo, tmp_path):
    write_json(tmp_path / "runs" / "2026-10-01.json", {"records": []})
    write_json(tmp_path / "raw" / "2026-10-04.json", {"entries": []})
    (tmp_path / "runs" / "notes.json").write_text("{}", encoding="utf-8")
    (tmp_path / "runs" / "2026-13-45.json").write_text("{}", encoding="utf-8")
    assert repo.list_run_dates() == [date(2026, 10, 4), date(2026, 10, 1)]


def test_run_dates_when_folders_missing(tmp_path):
    repo = FileRepository(tmp_path / "nowhere", tmp_path / "c.yaml", "real")
    assert repo.list_run_dates() == []


def test_load_all_findings_only_includes_dates_with_run_files(repo, tmp_path):
    write_json(tmp_path / "runs" / "2026-10-01.json", {"records": [make_record()]})
    write_json(tmp_path / "raw" / "2026-10-04.json", {"entries": []})
    assert list(repo.load_all_findings()) == [date(2026, 10, 1)]
