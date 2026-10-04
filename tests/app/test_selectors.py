from datetime import date

from app.core.dates import parse_date
from app.core.models import Company, Finding, LoadResult, RawEntry, SourceType
from app.core.selectors import (
    FindingFilter,
    company_facts,
    digest_findings,
    filter_findings,
    funnel,
    in_run_flags,
    sort_findings,
    source_counts,
)


def make_finding(**overrides) -> Finding:
    fields = dict(
        company="Example Corp.",
        sector="ai_cloud",
        signal_text="text",
        tier=1,
        date_mentioned=parse_date("2026-10-01T00:00:00Z"),
        source_url="https://a",
        gate_passed=True,
        gate_reason="ok",
        source=SourceType.NEWS,
        origin="illustrative",
    )
    return Finding(**{**fields, **overrides})


def make_entry(**overrides) -> RawEntry:
    fields = dict(
        signal_text="text",
        date_mentioned=parse_date("2026-10-01T00:00:00Z"),
        source_url="https://a",
        source=SourceType.NEWS,
        source_label="News API (corroboration)",
        fetched_at=parse_date("2026-10-04T00:00:00"),
        query="Example Corp.",
        origin="illustrative",
    )
    return RawEntry(**{**fields, **overrides})


# --- digest rule ---------------------------------------------------------

def test_digest_excludes_tier_zero_and_failed_gate():
    findings = [
        make_finding(tier=0),
        make_finding(tier=2, gate_passed=False),
        make_finding(tier=3, source_url="https://keep"),
    ]
    assert [f.source_url for f in digest_findings(findings)] == ["https://keep"]


def test_digest_sorts_by_tier_and_keeps_ten():
    findings = [make_finding(tier=t, source_url=f"https://{i}") for i, t in enumerate([4, 1, 3, 2] * 4)]
    result = digest_findings(findings)
    assert len(result) == 10
    assert [f.tier for f in result] == [1, 1, 1, 1, 2, 2, 2, 2, 3, 3]


def test_digest_empty_when_all_tier_zero():
    assert digest_findings([make_finding(tier=0)] * 7) == []


# --- filters -------------------------------------------------------------

def test_tier_zero_hidden_by_default():
    findings = [make_finding(tier=0), make_finding(tier=1)]
    assert [f.tier for f in filter_findings(findings, FindingFilter())] == [1]
    assert len(filter_findings(findings, FindingFilter(show_non_signals=True))) == 2


def test_life_sciences_filter_with_no_matches_returns_empty_list():
    findings = [make_finding(sector="ai_cloud"), make_finding(sector="fintech")]
    assert filter_findings(findings, FindingFilter(sectors=frozenset({"life_sciences"}))) == []


def test_gate_filter():
    findings = [make_finding(gate_passed=True), make_finding(gate_passed=False)]
    assert [f.gate_passed for f in filter_findings(findings, FindingFilter(gate="failed"))] == [False]
    assert [f.gate_passed for f in filter_findings(findings, FindingFilter(gate="passed"))] == [True]
    assert len(filter_findings(findings, FindingFilter(gate="all"))) == 2


def test_text_search_is_case_insensitive_and_covers_company():
    findings = [make_finding(signal_text="Dublin hiring"), make_finding(company="Other", signal_text="x")]
    assert len(filter_findings(findings, FindingFilter(text="dublin"))) == 1
    assert len(filter_findings(findings, FindingFilter(text="other"))) == 1


# --- sorting -------------------------------------------------------------

def test_sort_by_date_puts_unparseable_last_and_mixes_timezones():
    findings = [
        make_finding(date_mentioned=parse_date("Autumn 2026"), source_url="free"),
        make_finding(date_mentioned=parse_date("24/09/2026"), source_url="ida"),
        make_finding(date_mentioned=parse_date("2026-10-02T17:26:00-04:00"), source_url="news"),
    ]
    assert [f.source_url for f in sort_findings(findings, "date")] == ["news", "ida", "free"]


def test_sort_by_tier_puts_non_signals_last():
    findings = [make_finding(tier=0), make_finding(tier=4), make_finding(tier=1)]
    assert [f.tier for f in sort_findings(findings, "tier")] == [1, 4, 0]


# --- run overview --------------------------------------------------------

def test_source_counts_split_news_by_query():
    raw = [
        make_entry(query="A"),
        make_entry(query="A"),
        make_entry(query="B"),
        make_entry(source=SourceType.GAC, source_label="Global Affairs Canada", query=None),
    ]
    assert source_counts(raw) == [
        ("Global Affairs Canada", "", 1),
        ("News API", "A", 2),
        ("News API", "B", 1),
    ]


def test_funnel_is_two_numbers():
    result = funnel([make_entry()] * 132, [make_finding()] * 7)
    assert (result.raw_collected, result.records_saved) == (132, 7)


def test_in_run_flags_match_on_url_and_ignore_empty_urls():
    raw = [make_entry(source_url="https://a"), make_entry(source_url="https://b"), make_entry(source_url=None)]
    findings = [make_finding(source_url="https://a"), make_finding(source_url=None)]
    assert in_run_flags(raw, findings) == [True, False, False]


# --- companies -----------------------------------------------------------

def test_company_facts_across_runs():
    company = Company("Example Corp.", (), "EXMP", "TSX", "ai_cloud", "2026-09-26", "illustrative")
    runs = {
        date(2026, 10, 1): LoadResult("ok", (make_finding(tier=3, gate_reason="old"),), ""),
        date(2026, 10, 4): LoadResult("ok", (make_finding(tier=0, gate_reason="new"),), ""),
    }
    facts = company_facts(company, runs)
    assert facts.record_count == 2
    assert facts.highest_tier == 3
    assert facts.latest_gate_reason == "new"
    assert facts.runs_considered == 2


def test_company_facts_with_no_records():
    company = Company("Nobody Inc.", (), "", "", "fintech", "", "illustrative")
    facts = company_facts(company, {date(2026, 10, 4): LoadResult("ok", (make_finding(),), "")})
    assert (facts.record_count, facts.highest_tier, facts.latest_gate_reason) == (0, None, None)
