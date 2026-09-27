from src.collector import fetch_market_data
from src.extractor import load_companies

companies = load_companies()

for company in companies:
    print(f"--- {company['name']} ({company['ticker']}.{company['exchange']}) ---")
    try:
        result = fetch_market_data(company["ticker"], company["exchange"])
        print(result)
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
    print()
