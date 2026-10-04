from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Generic, Literal, TypeVar

Origin = Literal["real", "illustrative"]
LoadStatus = Literal["ok", "missing", "empty", "malformed"]

T = TypeVar("T")


class SourceType(Enum):
    GAC = ("Global Affairs Canada", "trade announcements")
    IDA = ("IDA Ireland press", "negative-space check, not yet used by the pipeline")
    NEWS = ("News API", "corroboration")
    UNKNOWN = ("Source type not recorded", "no matching raw entry for this link")

    def __init__(self, label: str, role: str) -> None:
        self.label = label
        self.role = role


# The exact strings the collectors write into data/raw/*.json.
SOURCE_LABELS: dict[str, SourceType] = {
    "Global Affairs Canada": SourceType.GAC,
    "IE inward-investment agency": SourceType.IDA,
    "News API (corroboration)": SourceType.NEWS,
}


def source_type_for(label: str) -> SourceType:
    return SOURCE_LABELS.get(label, SourceType.UNKNOWN)


@dataclass(frozen=True)
class ParsedDate:
    raw: str
    value: datetime | None  # None means unparseable; show `raw` as-is

    def display(self) -> str:
        if self.value is None:
            return self.raw or "No date"
        return self.value.strftime("%d %b %Y")


@dataclass(frozen=True)
class Finding:
    company: str
    sector: str
    signal_text: str
    tier: int
    date_mentioned: ParsedDate
    source_url: str | None
    gate_passed: bool
    gate_reason: str
    source: SourceType
    origin: Origin


@dataclass(frozen=True)
class RawEntry:
    signal_text: str
    date_mentioned: ParsedDate
    source_url: str | None
    source: SourceType
    source_label: str
    fetched_at: ParsedDate
    query: str | None
    origin: Origin


@dataclass(frozen=True)
class Company:
    name: str
    aliases: tuple[str, ...]
    ticker: str
    exchange: str
    sector: str
    date_added: str
    origin: Origin


@dataclass(frozen=True)
class LoadResult(Generic[T]):
    status: LoadStatus
    items: tuple[T, ...]
    message: str
    skipped_rows: int = 0

    @property
    def ok(self) -> bool:
        return self.status == "ok"
