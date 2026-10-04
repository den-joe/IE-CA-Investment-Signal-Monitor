"""The dashboard's digest must select exactly what the pipeline's digest does.

Imports src.digest read-only; if someone changes the pipeline rule, this
fails instead of the two quietly drifting apart.
"""

from dataclasses import asdict

from app.core.dates import parse_date
from app.core.models import Finding, SourceType
from app.core.selectors import digest_findings
from src.digest import generate_digest


def make_finding(i: int, tier: int, gate_passed: bool) -> Finding:
    return Finding(
        company=f"Company {i}",
        sector="ai_cloud",
        signal_text=f"text {i}",
        tier=tier,
        date_mentioned=parse_date("2026-10-01T00:00:00Z"),
        source_url=f"https://example.com/{i}",
        gate_passed=gate_passed,
        gate_reason="",
        source=SourceType.NEWS,
        origin="illustrative",
    )


def as_pipeline_record(f: Finding) -> dict:
    record = asdict(f)
    record["date_mentioned"] = f.date_mentioned.raw
    return record


def urls_in_pipeline_digest(findings: list[Finding]) -> list[str]:
    markdown = generate_digest([as_pipeline_record(f) for f in findings])
    return [line.split("[[source]](")[1].split(")")[0] for line in markdown.splitlines() if "[[source]]" in line]


def test_same_selection_and_order_as_pipeline():
    tiers = [0, 4, 1, 3, 2, 1, 0, 4, 2, 3, 1, 2, 4, 3]
    findings = [make_finding(i, t, gate_passed=(i % 5 != 0)) for i, t in enumerate(tiers)]

    assert [f.source_url for f in digest_findings(findings)] == urls_in_pipeline_digest(findings)


def test_both_empty_when_all_tier_zero():
    findings = [make_finding(i, 0, True) for i in range(7)]
    assert digest_findings(findings) == []
    assert urls_in_pipeline_digest(findings) == []
