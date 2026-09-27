from src.collector import fetch_negative_space_source
from src.extractor import load_companies, match_company, parse_negative_space_entries

fetch_result = fetch_negative_space_source()
entries = parse_negative_space_entries(fetch_result["raw_content"])
companies = load_companies()

print(f"Parsed {len(entries)} entries")
print()

for entry in entries:
    print(f"Date: {entry['date_mentioned']}")
    print(f"Text: {entry['signal_text'][:100]}")
    print(f"URL: {entry['source_url']}")
    print()

matches = 0
for entry in entries:
    company = match_company(entry["signal_text"], companies)
    if company:
        matches += 1
        print(f"MATCH: {company} -> {entry['signal_text'][:80]}")

print(f"\n{matches} of {len(entries)} entries matched a known company")
