"""Small display pieces shared by every page.

Colour is never the only carrier of meaning: every badge spells out its
label, and tier markers ("inference", "context only") are written in words.
"""

from datetime import date

import streamlit as st

from app.core.models import LoadResult, ParsedDate, SourceType
from app.core.tiers import sector_label, tier_info

ILLUSTRATIVE_BANNER = "ILLUSTRATIVE DATA, not real findings."

# Streamlit badge colours adapt to light and dark themes on their own.
_TIER_COLOURS: dict[int, str] = {1: "blue", 2: "violet", 3: "orange", 4: "gray", 0: "gray"}


def _escape(text: str) -> str:
    """Stop square brackets and colons in data from being read as badge or
    colour syntax inside Streamlit markdown."""
    return text.replace("[", "\\[").replace("]", "\\]")


_MD_SPECIAL = "\\`*_[]~$#<>|"


def md_escape(text: str) -> str:
    """Escape source text before rendering it as markdown. Without this,
    '$100-million ... $163M' in a headline renders as LaTeX maths."""
    return "".join(f"\\{ch}" if ch in _MD_SPECIAL else ch for ch in text)


def truncate(text: str, limit: int = 160) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1].rstrip() + "…"


def tier_label(tier: int) -> str:
    """Plain-text label, for places badges can't go (markdown export, tables)."""
    info = tier_info(tier)
    label = f"Tier {tier} · {info.name}" if tier > 0 else info.name
    return f"{label} · {info.marker}" if info.marker else label


def tier_badge(tier: int) -> str:
    colour = _TIER_COLOURS.get(tier, "gray")
    return f":{colour}-badge[{_escape(tier_label(tier))}]"


def sector_chip(sector: str) -> str:
    """Deliberately quieter than a tier badge: plain gray text, no fill."""
    return f":gray[{_escape(sector_label(sector))}]"


def gate_badge(passed: bool) -> str:
    # A failed gate is information, not an error, so it is gray rather than red.
    return ":green-badge[Gate passed]" if passed else ":gray-badge[Gate not passed]"


def source_line(url: str | None, source: SourceType, when: ParsedDate) -> str:
    """'News API (corroboration) · 22 Sep 2026 · [Open source](url)'.
    No URL means no link at all, never a broken one."""
    parts = [f"{source.label} ({source.role})", md_escape(when.display())]
    if url:
        # Angle brackets keep URLs containing ")" or spaces from breaking the link.
        parts.append(f"[Open source](<{url}>)")
    else:
        parts.append(":gray[No link recorded]")
    return " · ".join(parts)


def load_problem(result: LoadResult, what: str) -> None:
    """Explain a file that couldn't be used, and what that means for this page."""
    if result.status in ("missing", "empty"):
        st.info(f"{result.message} There are no {what} to show for this date.")
    else:
        st.warning(f"{result.message} The {what} for this date can't be shown until the file is fixed.")


def skipped_note(result: LoadResult) -> None:
    if result.skipped_rows:
        st.caption(
            f"{result.skipped_rows} row(s) in this file were skipped because "
            "required fields were missing or malformed."
        )


def illustrative_banner() -> None:
    st.warning(ILLUSTRATIVE_BANNER, icon=":material/science:")


def dossier_caption(text: str) -> None:
    """One line per page: what the dossier looks like at this stage."""
    st.caption(text)


def no_run_selected() -> None:
    st.info("No run files found in data/runs or data/raw. Run the pipeline to create one.")


def run_date_label(d: date) -> str:
    return d.strftime("%d %b %Y")
