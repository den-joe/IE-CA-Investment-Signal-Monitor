from src.collector import fetch_gac_listings

result = fetch_gac_listings()
print(f"Source: {result['source']}")
print(f"URL: {result['url']}")
print(f"Timestamp: {result['timestamp']}")
print(f"Content length: {len(result['raw_content'])} bytes")
