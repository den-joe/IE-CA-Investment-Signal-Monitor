from src.extractor import classify_tier

samples = {
    "tier 1 (expected)": "We are evaluating a European manufacturing site as part of our international expansion strategy.",
    "tier 2 (expected)": "The company has registered a new subsidiary entity in the European Union to support local operations.",
    "tier 3 (expected)": "The company posted a new job listing for a VP of European Operations based in Dublin.",
    "tier 4 (expected)": "The company cited the EU-Canada Strategic Partnership as a strategic tailwind in its latest filing.",
    "tier 0 (expected)": "The company posted record quarterly profits driven by strong core product sales.",
}

for label, text in samples.items():
    result = classify_tier(text)
    print(f"{label}: got tier {result.tier}")
    print(f"  Text: {text}")
    print(f"  Justification: {result.justification}")
    print()
