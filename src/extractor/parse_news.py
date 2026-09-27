import json


def parse_news_entries(raw_content: str) -> list[dict]:
    data = json.loads(raw_content)
    entries = []

    for article in data["articles"]:
        title = article["title"] or ""
        description = article["description"] or ""

        entries.append(
            {
                "signal_text": f"{title} {description}".strip(),
                "date_mentioned": article["publishedAt"],
                "source_url": article["url"],
            }
        )

    return entries
