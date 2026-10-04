import json
from datetime import date
from pathlib import Path

RUNS_DIR = Path(__file__).resolve().parents[2] / "data" / "runs"


def write_run(records: list[dict], run_date: str | None = None) -> None:
    """Persist one run to data/runs/<run_date>.json.

    Design choice: one run per day. A second run on the same date overwrites
    that day's file, so earlier records are lost from the seen-keys set.
    """
    run_date = run_date or date.today().isoformat()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{run_date}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"date": run_date, "records": records}, f, indent=2)


def load_seen_keys() -> set[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    if not RUNS_DIR.exists():
        return seen

    for path in RUNS_DIR.glob("*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for record in data.get("records", []):
                seen.add((record["company"], record["source_url"]))
        except (json.JSONDecodeError, KeyError, OSError):
            continue

    return seen
