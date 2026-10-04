"""Pure functions over loaded models. No file access, no streamlit."""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

from app.core.models import Company, Finding, LoadResult, RawEntry, SourceType

GateFilter = Literal["all", "passed", "failed"]
SortKey = Literal["tier", "date"]

DIGEST_LIMIT = 10


def digest_findings(findings: tuple[Finding, ...] | list[Finding]) -> list[Finding]:
    """Mirror of src/digest/format.py: tier > 0 and gate passed, tier
    ascending (stable), at most 10."""
    selected = [f for f in findings if f.tier > 0 and f.gate_passed]
    selected.sort(key=lambda f: f.tier)
    return selected[:DIGEST_LIMIT]


@dataclass(frozen=True)
class FindingFilter:
    sectors: frozenset[str] = field(default_factory=frozenset)  # empty = all
    tiers: frozenset[int] = field(default_factory=frozenset)  # empty = all
    gate: GateFilter = "all"
    companies: frozenset[str] = field(default_factory=frozenset)  # empty = all
    text: str = ""
    show_non_signals: bool = False


def filter_findings(findings: tuple[Finding, ...] | list[Finding], flt: FindingFilter) -> list[Finding]:
    needle = flt.text.strip().casefold()
    result = []
    for f in findings:
        if f.tier == 0 and not flt.show_non_signals:
            continue
        if flt.sectors and f.sector not in flt.sectors:
            continue
        if flt.tiers and f.tier not in flt.tiers:
            continue
        if flt.gate == "passed" and not f.gate_passed:
            continue
        if flt.gate == "failed" and f.gate_passed:
            continue
        if flt.companies and f.company not in flt.companies:
            continue
        if needle and needle not in f"{f.company} {f.signal_text}".casefold():
            continue
        result.append(f)
    return result


def _sortable_date(f: Finding) -> datetime:
    """Unparseable dates sort last. The timezone is dropped so that naive IDA
    dates and offset-aware news dates can be compared at all."""
    value = f.date_mentioned.value
    if value is None:
        return datetime.min
    return value.replace(tzinfo=None)


def sort_findings(findings: list[Finding], key: SortKey) -> list[Finding]:
    if key == "tier":
        # Tier 1 first; Tier 0 (not a signal) after the real tiers.
        return sorted(findings, key=lambda f: (f.tier == 0, f.tier, -_sortable_date(f).toordinal()))
    return sorted(findings, key=_sortable_date, reverse=True)


def source_counts(raw: tuple[RawEntry, ...] | list[RawEntry]) -> list[tuple[str, str, int]]:
    """(source label, query or "", count), news split by query company."""
    counts: Counter[tuple[str, str]] = Counter(
        (e.source.label, e.query or "") for e in raw
    )
    order = {s.label: i for i, s in enumerate(SourceType)}
    return sorted(
        ((src, query, n) for (src, query), n in counts.items()),
        key=lambda row: (order.get(row[0], 99), -row[2], row[1]),
    )


@dataclass(frozen=True)
class Funnel:
    raw_collected: int
    records_saved: int


def funnel(raw: tuple[RawEntry, ...] | list[RawEntry], findings: tuple[Finding, ...] | list[Finding]) -> Funnel:
    """Two stages only. Matched-before-dedupe and dropped-by-dedupe counts are
    not persisted by the pipeline, so they are not reconstructed here."""
    return Funnel(raw_collected=len(raw), records_saved=len(findings))


def in_run_flags(raw: tuple[RawEntry, ...] | list[RawEntry], findings: tuple[Finding, ...] | list[Finding]) -> list[bool]:
    """For each raw entry, whether its URL appears in this run's records."""
    run_urls = {f.source_url for f in findings if f.source_url}
    return [e.source_url is not None and e.source_url in run_urls for e in raw]


@dataclass(frozen=True)
class CompanyFacts:
    record_count: int
    highest_tier: int | None  # strongest = lowest non-zero; 0 if only non-signals
    latest_gate_reason: str | None
    latest_gate_date: date | None
    runs_considered: int


def company_facts(company: Company, all_findings: dict[date, LoadResult[Finding]]) -> CompanyFacts:
    records: list[tuple[date, Finding]] = [
        (d, f)
        for d, result in all_findings.items()
        for f in result.items
        if f.company == company.name
    ]
    tiers = {f.tier for _, f in records}
    signal_tiers = sorted(t for t in tiers if t > 0)
    if signal_tiers:
        highest: int | None = signal_tiers[0]
    elif tiers:
        highest = 0
    else:
        highest = None

    latest_reason = latest_date = None
    if records:
        latest_date, latest = max(records, key=lambda pair: pair[0])
        latest_reason = latest.gate_reason

    return CompanyFacts(
        record_count=len(records),
        highest_tier=highest,
        latest_gate_reason=latest_reason,
        latest_gate_date=latest_date,
        runs_considered=len(all_findings),
    )
