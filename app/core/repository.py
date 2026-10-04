"""Read-only access to the files the pipeline writes.

Views depend only on the SignalRepository protocol. FileRepository reads the
JSON/YAML files on disk; an API-backed class could replace it later without
touching any view.
"""

import json
import re
from datetime import date
from pathlib import Path
from typing import Callable, Protocol, TypeVar

import yaml

from app.core.dates import parse_date
from app.core.models import (
    Company,
    Finding,
    LoadResult,
    Origin,
    RawEntry,
    SourceType,
    source_type_for,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_DATA_DIR = REPO_ROOT / "data"
REAL_COMPANIES_PATH = REPO_ROOT / "config" / "companies.yaml"
ILLUSTRATIVE_DIR = REPO_ROOT / "fixtures" / "illustrative"

_DATE_FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")

T = TypeVar("T")


class SignalRepository(Protocol):
    origin: Origin

    def list_run_dates(self) -> list[date]: ...
    def load_findings(self, run_date: date) -> LoadResult[Finding]: ...
    def load_raw(self, run_date: date) -> LoadResult[RawEntry]: ...
    def load_all_findings(self) -> dict[date, LoadResult[Finding]]: ...
    def load_companies(self) -> LoadResult[Company]: ...


def _read_json_list(path: Path, key: str) -> tuple[LoadResult[dict], list[dict]]:
    """Read {"<key>": [...]} from path. Returns a status result plus the rows."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return LoadResult("missing", (), f"{_rel(path)} does not exist."), []
    except OSError as e:
        return LoadResult("malformed", (), f"{_rel(path)} could not be read: {e}"), []

    if not text.strip():
        return LoadResult("empty", (), f"{_rel(path)} is empty."), []

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return LoadResult("malformed", (), f"{_rel(path)} is not valid JSON ({e.msg}, line {e.lineno})."), []

    rows = data.get(key) if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return LoadResult("malformed", (), f'{_rel(path)} has no "{key}" list.'), []

    return LoadResult("ok", (), ""), rows


def _convert_rows(rows: list[dict], convert: Callable[[dict], T]) -> tuple[tuple[T, ...], int]:
    """Convert each row, skipping (and counting) rows that are missing fields."""
    items: list[T] = []
    skipped = 0
    for row in rows:
        try:
            items.append(convert(row))
        except (KeyError, TypeError, ValueError):
            skipped += 1
    return tuple(items), skipped


def _url_or_none(value: object) -> str | None:
    text = "" if value is None else str(value).strip()
    return text or None


def _rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


class FileRepository:
    def __init__(self, data_dir: Path, companies_path: Path, origin: Origin) -> None:
        self.data_dir = data_dir
        self.companies_path = companies_path
        self.origin: Origin = origin

    def _runs_path(self, run_date: date) -> Path:
        return self.data_dir / "runs" / f"{run_date.isoformat()}.json"

    def _raw_path(self, run_date: date) -> Path:
        return self.data_dir / "raw" / f"{run_date.isoformat()}.json"

    def list_run_dates(self) -> list[date]:
        """Dates with a run file or a raw file, newest first."""
        dates: set[date] = set()
        for folder in (self.data_dir / "runs", self.data_dir / "raw"):
            try:
                names = [p.name for p in folder.iterdir()]
            except OSError:
                continue
            for name in names:
                match = _DATE_FILENAME.match(name)
                if not match:
                    continue
                try:
                    dates.add(date.fromisoformat(match.group(1)))
                except ValueError:
                    continue
        return sorted(dates, reverse=True)

    def load_raw(self, run_date: date) -> LoadResult[RawEntry]:
        status, rows = _read_json_list(self._raw_path(run_date), "entries")
        if not status.ok:
            return status  # type: ignore[return-value]

        def convert(row: dict) -> RawEntry:
            label = str(row["source"])
            query = row.get("query")
            return RawEntry(
                signal_text=str(row["signal_text"]),
                date_mentioned=parse_date(row.get("date_mentioned")),
                source_url=_url_or_none(row.get("source_url")),
                source=source_type_for(label),
                source_label=label,
                fetched_at=parse_date(row.get("fetched_at")),
                query=str(query) if query else None,
                origin=self.origin,
            )

        items, skipped = _convert_rows(rows, convert)
        return LoadResult("ok", items, "", skipped)

    def load_findings(self, run_date: date) -> LoadResult[Finding]:
        status, rows = _read_json_list(self._runs_path(run_date), "records")
        if not status.ok:
            return status  # type: ignore[return-value]

        # Run records don't store their source, so recover it from the same
        # day's raw file by URL. No raw file, or no match: UNKNOWN.
        raw = self.load_raw(run_date)
        source_by_url = {e.source_url: e.source for e in raw.items if e.source_url}

        def convert(row: dict) -> Finding:
            tier = row["tier"]
            if isinstance(tier, bool) or not isinstance(tier, int):
                raise ValueError(f"tier is not an integer: {tier!r}")
            url = _url_or_none(row.get("source_url"))
            gate_passed = row.get("gate_passed")
            return Finding(
                company=str(row["company"]),
                sector=str(row.get("sector", "")),
                signal_text=str(row["signal_text"]),
                tier=tier,
                date_mentioned=parse_date(row.get("date_mentioned")),
                source_url=url,
                # Fail closed, like the pipeline's gate: no result means not passed.
                gate_passed=gate_passed is True,
                gate_reason=str(row.get("gate_reason") or "Gate result not recorded"),
                source=source_by_url.get(url, SourceType.UNKNOWN) if url else SourceType.UNKNOWN,
                origin=self.origin,
            )

        items, skipped = _convert_rows(rows, convert)
        return LoadResult("ok", items, "", skipped)

    def load_all_findings(self) -> dict[date, LoadResult[Finding]]:
        return {
            d: self.load_findings(d)
            for d in self.list_run_dates()
            if self._runs_path(d).exists()
        }

    def load_companies(self) -> LoadResult[Company]:
        path = self.companies_path
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return LoadResult("missing", (), f"{_rel(path)} does not exist.")
        except OSError as e:
            return LoadResult("malformed", (), f"{_rel(path)} could not be read: {e}")

        if not text.strip():
            return LoadResult("empty", (), f"{_rel(path)} is empty.")

        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            return LoadResult("malformed", (), f"{_rel(path)} is not valid YAML: {e}")

        rows = data.get("companies") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            return LoadResult("malformed", (), f'{_rel(path)} has no "companies" list.')

        def convert(row: dict) -> Company:
            return Company(
                name=str(row["name"]),
                aliases=tuple(str(a) for a in row.get("aliases") or ()),
                ticker=str(row.get("ticker", "")),
                exchange=str(row.get("exchange", "")),
                sector=str(row.get("sector", "")),
                date_added=str(row.get("date_added", "")),
                origin=self.origin,
            )

        items, skipped = _convert_rows(rows, convert)
        return LoadResult("ok", items, "", skipped)


def get_repository(illustrative: bool) -> SignalRepository:
    """The data-source switch. One or the other, never a mix."""
    if illustrative:
        return FileRepository(ILLUSTRATIVE_DIR, ILLUSTRATIVE_DIR / "companies.yaml", "illustrative")
    return FileRepository(REAL_DATA_DIR, REAL_COMPANIES_PATH, "real")
