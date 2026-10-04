import json
from datetime import date
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def write_raw_entries(entries: list[dict], run_date: str | None = None) -> None:
    """Persist collected entries to data/raw/<run_date>.json.

    Same design as write_run: one file per day, a second run on the same date
    overwrites that day's file.
    """
    run_date = run_date or date.today().isoformat()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{run_date}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"date": run_date, "entries": entries}, f, indent=2)


def load_raw_entries(run_date: str | None = None) -> list[dict]:
    """Load entries saved for run_date, or the most recent file if no date given."""
    if run_date:
        path = RAW_DIR / f"{run_date}.json"
    else:
        files = sorted(RAW_DIR.glob("*.json")) if RAW_DIR.exists() else []
        if not files:
            raise FileNotFoundError(f"No raw entries saved in {RAW_DIR}")
        path = files[-1]

    if not path.exists():
        raise FileNotFoundError(f"No raw entries file at {path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)["entries"]
