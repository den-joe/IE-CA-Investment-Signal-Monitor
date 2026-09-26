from src.collector import fetch_negative_space_source

result = fetch_negative_space_source()
print(f"Source: {result['source']}")
print(f"URL: {result['url']}")
print(f"Timestamp: {result['timestamp']}")
print(f"Content length: {len(result['raw_content'])} bytes")
