from pathlib import Path

import yaml

COMPANIES_PATH = Path(__file__).resolve().parents[2] / "config" / "companies.yaml"


def load_companies() -> list[dict]:
    with open(COMPANIES_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["companies"]


def match_company(text: str, companies: list[dict]) -> str | None:
    text_lower = text.lower()
    for company in companies:
        names_to_check = [company["name"], *company["aliases"]]
        for name in names_to_check:
            if name.lower() in text_lower:
                return company["name"]
    return None
