from bs4 import BeautifulSoup

BASE_URL = "https://www.idaireland.com"


def parse_negative_space_entries(raw_content: str) -> list[dict]:
    soup = BeautifulSoup(raw_content, "html.parser")
    entries = []

    for card in soup.select(".latest-news-grid__card-item"):
        title_tag = card.select_one("h3 a")
        description_tag = card.select_one("p")
        date_tag = card.select_one("li.date")

        title = title_tag.get_text(strip=True) if title_tag else ""
        description = description_tag.get_text(strip=True) if description_tag else ""
        date = date_tag.get_text(strip=True) if date_tag else ""
        href = title_tag["href"] if title_tag and title_tag.has_attr("href") else ""

        entries.append(
            {
                "signal_text": f"{title} {description}".strip(),
                "date_mentioned": date,
                "source_url": f"{BASE_URL}{href}" if href else "",
            }
        )

    return entries
