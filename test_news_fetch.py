from src.collector import fetch_news_corroboration

result = fetch_news_corroboration("OpenText Ireland")
print(f"Source: {result['source']}")
print(f"URL: {result['url']}")
print(f"Timestamp: {result['timestamp']}")
print(f"Content length: {len(result['raw_content'])} bytes")
