
from pathlib import Path
from time import perf_counter

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data" / "chroma_db"

COLLECTION_NAME = "mini_rag"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_retriever():
    """Load the existing vector database and embedding model."""
    client = chromadb.PersistentClient(path=str(DB_DIR))

    collection = client.get_collection(COLLECTION_NAME)

    model = SentenceTransformer(MODEL_NAME)

    return collection, model


def search(query: str, top_k: int = 3) -> dict:
    """Retrieve relevant chunks and measure search latency."""
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    collection, model = load_retriever()

    # Time query embedding separately.
    start = perf_counter()
    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()
    embedding_ms = (perf_counter() - start) * 1000

    # Time vector retrieval separately.
    start = perf_counter()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    retrieval_ms = (perf_counter() - start) * 1000

    matches = []

    for i, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        matches.append(
            {
                "rank": i + 1,
                "source": metadata["source"],
                "chunk_index": metadata["chunk_index"],
                "text": document,
                "distance": round(distance, 4),
            }
        )

    return {
        "query": query,
        "document_count": collection.count(),
        "embedding_ms": round(embedding_ms, 2),
        "retrieval_ms": round(retrieval_ms, 2),
        "total_ms": round(embedding_ms + retrieval_ms, 2),
        "results": matches,
    }


if __name__ == "__main__":
    question = input("Ask a question: ")

    try:
        response = search(question)

        print(f"\nDocuments/chunks indexed: {response['document_count']}")
        print(f"Query embedding: {response['embedding_ms']} ms")
        print(f"Vector retrieval: {response['retrieval_ms']} ms")
        print(f"Measured total: {response['total_ms']} ms")

        for result in response["results"]:
            print(f"\n--- Result {result['rank']} ---")
            print(f"Source: {result['source']}")
            print(f"Distance: {result['distance']}")
            print(result["text"])

    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}")
    except Exception as exc:
        print(f"Retrieval failed: {exc}")
        raise
