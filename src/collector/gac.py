import httpx
from datetime import datetime
from typing import TypedDict


class FetchResult(TypedDict):
    source: str
    url: str
    timestamp: str
    raw_content: str


def fetch_gac_listings() -> FetchResult:
    url = (
        "https://api.io.canada.ca/io-server/gc/news/en/v2"
        "?dept=departmentofforeignaffairstradeanddevelopment"
        "&sort=publishedDate&orderBy=desc&publishedDate%3E=2021-07-23"
        "&pick=50&format=atom&atomtitle=Global%20Affairs%20Canada"
    )

    response = httpx.get(url)
    response.raise_for_status()

    return FetchResult(
        source="Global Affairs Canada",
        url=url,
        timestamp=datetime.utcnow().isoformat(),
        raw_content=response.text,
    )
