from src.graph import tag_entries

FETCH = {
    "source": "Global Affairs Canada",
    "url": "https://example.com/feed",
    "timestamp": "2026-10-04T17:08:00",
    "raw_content": "ignored",
}


def make_entry(url: str) -> dict:
    return {"signal_text": "text", "date_mentioned": "2026-09-28", "source_url": url}


def test_tag_entries_adds_source_and_fetched_at():
    tagged = tag_entries([make_entry("https://a")], FETCH)

    assert tagged == [
        {
            **make_entry("https://a"),
            "source": "Global Affairs Canada",
            "fetched_at": "2026-10-04T17:08:00",
        }
    ]


def test_tag_entries_adds_query_only_when_given():
    assert "query" not in tag_entries([make_entry("https://a")], FETCH)[0]
    assert tag_entries([make_entry("https://a")], FETCH, query="OpenText")[0]["query"] == "OpenText"


def test_tag_entries_does_not_mutate_input():
    entry = make_entry("https://a")
    tag_entries([entry], FETCH)

    assert entry == make_entry("https://a")
