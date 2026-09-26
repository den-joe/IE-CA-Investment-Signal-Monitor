from datetime import datetime
from pathlib import Path

from .gac import FetchResult

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def fetch_negative_space_source() -> FetchResult:
    """Reads the most recently saved manual HTML snapshot from data/.

    The originating site blocks plain HTTP fetches (bot-detection
    challenge), so snapshots are saved by hand from a real browser
    session and dropped in data/ as YYYY-MM-DD.html.
    """
    snapshots = sorted(DATA_DIR.glob("????-??-??.html"))
    if not snapshots:
        raise FileNotFoundError(f"No manual snapshot found in {DATA_DIR}")

    latest = snapshots[-1]

    return FetchResult(
        source="IE inward-investment agency",
        url=str(latest),
        timestamp=datetime.utcnow().isoformat(),
        raw_content=latest.read_text(encoding="utf-8"),
    )
