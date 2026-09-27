from src.graph import graph

result = graph.invoke({})
print(f"raw_entries count: {len(result['raw_entries'])}")
print(f"first entry: {result['raw_entries'][0]}")
