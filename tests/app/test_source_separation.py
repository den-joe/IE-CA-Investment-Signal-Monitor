"""Real and illustrative data must never mix. These run against the actual
files on disk, not temp copies."""

import json

from app.core.repository import REAL_DATA_DIR, get_repository


def all_findings(repo):
    return [f for result in repo.load_all_findings().values() for f in result.items]


def all_raw(repo):
    return [e for d in repo.list_run_dates() for e in repo.load_raw(d).items]


def names_and_aliases(repo) -> set[str]:
    names: set[str] = set()
    for c in repo.load_companies().items:
        names.add(c.name.casefold())
        names.update(a.casefold() for a in c.aliases)
    return names


def test_illustrative_mode_returns_only_illustrative_rows():
    repo = get_repository(illustrative=True)
    rows = all_findings(repo) + all_raw(repo) + list(repo.load_companies().items)
    assert rows, "illustrative fixtures should not be empty"
    assert {r.origin for r in rows} == {"illustrative"}


def test_real_mode_returns_only_real_rows():
    repo = get_repository(illustrative=False)
    rows = all_findings(repo) + all_raw(repo) + list(repo.load_companies().items)
    assert {r.origin for r in rows} <= {"real"}


def test_illustrative_companies_never_share_a_name_or_alias_with_real_ones():
    assert names_and_aliases(get_repository(True)).isdisjoint(names_and_aliases(get_repository(False)))


def test_illustrative_findings_only_name_illustrative_companies():
    illustrative = get_repository(True)
    names = {c.name for c in illustrative.load_companies().items}
    assert {f.company for f in all_findings(illustrative)} <= names


def test_no_illustrative_url_appears_in_real_data_files():
    illustrative_urls = {
        u for u in (
            [f.source_url for f in all_findings(get_repository(True))]
            + [e.source_url for e in all_raw(get_repository(True))]
        ) if u
    }
    real_text = "".join(
        p.read_text(encoding="utf-8") for p in REAL_DATA_DIR.rglob("*.json")
    )
    assert not any(url in real_text for url in illustrative_urls)


def test_illustrative_fixtures_cover_all_tiers_gates_and_sectors():
    findings = all_findings(get_repository(True))
    assert {f.tier for f in findings} >= {0, 1, 2, 3, 4}
    assert {f.gate_passed for f in findings} == {True, False}
    assert {f.sector for f in findings} == {"ai_cloud", "life_sciences", "fintech"}


def test_every_illustrative_signal_text_is_marked():
    repo = get_repository(True)
    texts = [f.signal_text for f in all_findings(repo)] + [e.signal_text for e in all_raw(repo)]
    assert all(t.startswith("[Illustrative]") for t in texts)
