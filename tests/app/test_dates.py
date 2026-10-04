from datetime import timedelta

import pytest

from app.core.dates import parse_date


def test_iso_with_z():
    parsed = parse_date("2026-09-22T06:45:17Z")
    assert parsed.value is not None
    assert parsed.value.utcoffset() == timedelta(0)
    assert parsed.display() == "22 Sep 2026"


def test_iso_with_offset():
    parsed = parse_date("2026-10-02T17:26:00-04:00")
    assert parsed.value is not None
    assert parsed.value.utcoffset() == timedelta(hours=-4)


def test_iso_without_timezone():
    assert parse_date("2026-10-04T16:52:47.987227").value is not None


def test_ida_day_first_format():
    parsed = parse_date("24/09/2026")
    assert parsed.value is not None
    assert (parsed.value.day, parsed.value.month) == (24, 9)


@pytest.mark.parametrize("raw", ["Autumn 2026", "13/13/2026", "yesterday"])
def test_unparseable_text_keeps_raw_string(raw):
    parsed = parse_date(raw)
    assert parsed.value is None
    assert parsed.display() == raw


@pytest.mark.parametrize("raw", ["", None, "   "])
def test_empty_or_missing_date(raw):
    parsed = parse_date(raw)
    assert parsed.value is None
    assert parsed.display() == "No date"
