from src.graph import graph

result = graph.invoke({})
print(f"raw_entries count: {len(result['raw_entries'])}")
print(f"records count: {len(result['records'])}")
print()
print(result["digest"])
