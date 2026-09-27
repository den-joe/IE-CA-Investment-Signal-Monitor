from src.digest import generate_digest

print("--- empty case ---")
print(generate_digest([]))

print("--- synthetic tier-1 case ---")
synthetic_record = {
    "company": "Open Text Corp.",
    "sector": "ai_cloud",
    "signal_text": "We are evaluating a new Irish data centre as part of our European expansion plans.",
    "tier": 1,
    "date_mentioned": "2026-09-26T00:00:00Z",
    "source_url": "https://example.com/opentext-ireland",
    "gate_passed": True,
    "gate_reason": "Market cap meets threshold",
}
print(generate_digest([synthetic_record]))
