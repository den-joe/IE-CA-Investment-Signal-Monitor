from typing import TypedDict

from langgraph.graph import END, StateGraph

from src.collector import fetch_gac_listings
from src.extractor import parse_gac_entries


class GraphState(TypedDict):
    raw_entries: list[dict]


def collect_gac(state: GraphState) -> dict:
    fetch_result = fetch_gac_listings()
    entries = parse_gac_entries(fetch_result["raw_content"])
    return {"raw_entries": entries}


builder = StateGraph(GraphState)
builder.add_node("collect_gac", collect_gac)
builder.set_entry_point("collect_gac")
builder.add_edge("collect_gac", END)

graph = builder.compile()
