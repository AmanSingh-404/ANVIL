import chromadb
from sentence_transformers import SentenceTransformer

_model = None
_client = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path="registry/chroma_store")
        _collection = _client.get_or_create_collection(name="tools")
    return _collection


def embed_text(text: str) -> list:
    model = _get_model()
    return model.encode(text).tolist()


def upsert_tool_embedding(tool_name: str, description: str):
    """
    Adds or updates a tool's embedding in the vector store,
    keyed by tool name so re-forging the same tool overwrites cleanly.
    """
    collection = _get_collection()
    embedding = embed_text(description)
    collection.upsert(
        ids=[tool_name],
        embeddings=[embedding],
        documents=[description],
    )


def query_relevant_tools(task_description: str, top_k: int = 5) -> list:
    """
    Returns the names of the top_k most semantically relevant tools
    for a given task description.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return []

    query_embedding = embed_text(task_description)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )
    return results["ids"][0] if results["ids"] else []