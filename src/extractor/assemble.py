from .company_matcher import match_company
from .tier_classifier import classify_tier


def assemble_record(entry: dict, companies: list[dict]) -> dict | None:
    company_name = match_company(entry["signal_text"], companies)
    if company_name is None:
        return None

    company = next(c for c in companies if c["name"] == company_name)
    classification = classify_tier(entry["signal_text"])

    return {
        "company": company_name,
        "sector": company["sector"],
        "signal_text": entry["signal_text"],
        "tier": classification.tier,
        "date_mentioned": entry["date_mentioned"],
        "source_url": entry["source_url"],
    }
