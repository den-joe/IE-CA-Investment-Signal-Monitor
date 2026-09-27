import xml.etree.ElementTree as ET

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def parse_gac_entries(raw_content: str) -> list[dict]:
    root = ET.fromstring(raw_content)
    entries = []

    for entry in root.findall("atom:entry", ATOM_NS):
        title = entry.find("atom:title", ATOM_NS).text
        summary = entry.find("atom:summary", ATOM_NS).text
        updated = entry.find("atom:updated", ATOM_NS).text
        link = entry.find("atom:link", ATOM_NS).get("href")

        entries.append(
            {
                "signal_text": f"{title} {summary}",
                "date_mentioned": updated,
                "source_url": link,
            }
        )

    return entries
