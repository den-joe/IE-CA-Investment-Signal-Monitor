import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

from .gac import FetchResult

load_dotenv()


def fetch_news_corroboration(query: str) -> FetchResult:
    """Corroboration-only search. Never treat a hit here as an originating
    signal — it exists to support/undercut a finding already made from a
    primary source, per CLAUDE.md's source-list rules.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise RuntimeError("NEWS_API_KEY not set in .env")

    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "sortBy": "publishedAt", "language": "en"}
    headers = {"X-Api-Key": api_key}

    response = httpx.get(url, params=params, headers=headers)
    response.raise_for_status()

    return FetchResult(
        source="News API (corroboration)",
        url=f"{url}?q={query}",
        timestamp=datetime.utcnow().isoformat(),
        raw_content=response.text,
    )
