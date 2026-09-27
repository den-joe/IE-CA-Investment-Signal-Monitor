from src.collector import fetch_gac_listings
from src.extractor import load_companies, match_company, parse_gac_entries

fetch_result = fetch_gac_listings()
entries = parse_gac_entries(fetch_result["raw_content"])
companies = load_companies()

print(f"Parsed {len(entries)} entries")
print()

matches = 0
for entry in entries:
    company = match_company(entry["signal_text"], companies)
    if company:
        matches += 1
        print(f"MATCH: {company}")
        print(f"  Text: {entry['signal_text'][:100]}")
        print(f"  Date: {entry['date_mentioned']}")
        print(f"  URL: {entry['source_url']}")

print(f"\n{matches} of {len(entries)} entries matched a known company")
