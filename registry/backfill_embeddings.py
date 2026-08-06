from registry.registry import list_tools
from registry.vector_store import upsert_tool_embedding

def backfill():
    tools = list_tools()
    for t in tools:
        upsert_tool_embedding(t["name"], t["description"])
        print(f"Embedded: {t['name']}")
    print(f"\nBackfilled {len(tools)} tool embeddings.")

if __name__ == "__main__":
    backfill()