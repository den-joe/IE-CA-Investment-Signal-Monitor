import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from src.collector import (
    fetch_gac_listings,
    fetch_market_data,
    fetch_negative_space_source,
    fetch_news_corroboration,
)
from src.extractor import (
    assemble_record,
    load_companies,
    parse_gac_entries,
    parse_negative_space_entries,
    parse_news_entries,
)
from src.digest import generate_digest
from src.scorer import check_market_cap_gate


class GraphState(TypedDict):
    raw_entries: Annotated[list[dict], operator.add]
    records: list[dict]
    digest: str


def collect_gac(state: GraphState) -> dict:
    fetch_result = fetch_gac_listings()
    entries = parse_gac_entries(fetch_result["raw_content"])
    return {"raw_entries": entries}


def collect_negative_space(state: GraphState) -> dict:
    fetch_result = fetch_negative_space_source()
    entries = parse_negative_space_entries(fetch_result["raw_content"])
    return {"raw_entries": entries}


def collect_news(state: GraphState) -> dict:
    companies = load_companies()
    all_entries = []
    for company in companies:
        fetch_result = fetch_news_corroboration(company["name"])
        all_entries.extend(parse_news_entries(fetch_result["raw_content"]))
    return {"raw_entries": all_entries}


def check_for_new_signals(state: GraphState) -> dict:
    return {}


def route_after_collection(state: GraphState) -> str:
    return "continue" if state["raw_entries"] else "skip"


def extract_signals(state: GraphState) -> dict:
    companies = load_companies()
    records = [assemble_record(e, companies) for e in state["raw_entries"]]
    records = [r for r in records if r is not None]
    return {"records": records}


def score_gate(state: GraphState) -> dict:
    companies = load_companies()
    companies_by_name = {c["name"]: c for c in companies}

    gate_cache: dict[str, dict] = {}
    for company_name in {r["company"] for r in state["records"]}:
        company = companies_by_name[company_name]
        market_data = fetch_market_data(company["ticker"], company["exchange"])
        gate_cache[company_name] = check_market_cap_gate(market_data)

    updated_records = [
        {
            **record,
            "gate_passed": gate_cache[record["company"]]["passed"],
            "gate_reason": gate_cache[record["company"]]["reason"],
        }
        for record in state["records"]
    ]

    return {"records": updated_records}


def generate_digest_node(state: GraphState) -> dict:
    return {"digest": generate_digest(state.get("records", []))}


builder = StateGraph(GraphState)
builder.add_node("collect_gac", collect_gac)
builder.add_node("collect_negative_space", collect_negative_space)
builder.add_node("collect_news", collect_news)
builder.add_node("check_for_new_signals", check_for_new_signals)
builder.add_node("extract_signals", extract_signals)
builder.add_node("score_gate", score_gate)
builder.add_node("generate_digest_node", generate_digest_node)

builder.add_edge(START, "collect_gac")
builder.add_edge(START, "collect_negative_space")
builder.add_edge(START, "collect_news")

builder.add_edge("collect_gac", "check_for_new_signals")
builder.add_edge("collect_negative_space", "check_for_new_signals")
builder.add_edge("collect_news", "check_for_new_signals")

builder.add_conditional_edges(
    "check_for_new_signals",
    route_after_collection,
    {"continue": "extract_signals", "skip": "generate_digest_node"},
)

builder.add_edge("extract_signals", "score_gate")
builder.add_edge("score_gate", "generate_digest_node")
builder.add_edge("generate_digest_node", END)

graph = builder.compile()
