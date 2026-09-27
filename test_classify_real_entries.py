from src.collector import (
    fetch_gac_listings,
    fetch_negative_space_source,
    fetch_news_corroboration,
)
from src.extractor import (
    classify_tier,
    load_companies,
    match_company,
    parse_gac_entries,
    parse_negative_space_entries,
    parse_news_entries,
)

companies = load_companies()

sources = {
    "GAC": lambda: parse_gac_entries(fetch_gac_listings()["raw_content"]),
    "News (OpenText)": lambda: parse_news_entries(
        fetch_news_corroboration("OpenText")["raw_content"]
    ),
    "Negative-space": lambda: parse_negative_space_entries(
        fetch_negative_space_source()["raw_content"]
    ),
}

for source_name, get_entries in sources.items():
    entries = get_entries()
    matched = [(e, match_company(e["signal_text"], companies)) for e in entries]
    matched = [(e, c) for e, c in matched if c]

    print(f"=== {source_name}: {len(matched)} of {len(entries)} matched ===")
    print()

    for entry, company in matched:
        classification = classify_tier(entry["signal_text"])
        print(f"Company: {company}")
        print(f"Tier: {classification.tier}")
        print(f"Justification: {classification.justification}")
        print(f"Text: {entry['signal_text'][:120]}")
        print()
