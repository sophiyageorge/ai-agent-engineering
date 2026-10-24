
from pathlib import Path
from time import perf_counter

import chromadb
from sentence_transformers import SentenceTransformer

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
DB_DIR = BASE_DIR / "data" / "chroma_db"

# Initial experiment settings
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
BATCH_SIZE = 32

COLLECTION_NAME = "mini_rag"

# Local embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def chunk_text(text: str) -> list[str]:
    """Split text into fixed-size character chunks with overlap."""
    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def main():
    if not DOCUMENTS_DIR.exists():
        raise FileNotFoundError(
            f"Documents directory not found: {DOCUMENTS_DIR}"
        )

    files = sorted(DOCUMENTS_DIR.glob("*.txt"))

    if not files:
        raise ValueError(
            "No .txt documents found in data/documents."
        )

    print(f"Found {len(files)} documents.")

    # Read and chunk the source documents.
    all_chunks = []
    all_ids = []
    all_metadata = []

    for path in files:
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):
            chunk_id = f"{path.stem}_{index}"

            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadata.append(
                {
                    "source": path.name,
                    "chunk_index": index,
                }
            )

    print(f"Created {len(all_chunks)} chunks.")

    # Load the embedding model.
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    # Persistent local vector database.
    client = chromadb.PersistentClient(path=str(DB_DIR))

    # Rebuild this experiment's collection on each run,
    # so repeated runs don't duplicate old records.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception as exc:
        # Only a missing collection is expected here.
        # Re-raise other failures rather than hiding them.
        if "does not exist" not in str(exc).lower():
            raise

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Measure embedding and database insertion time.
    embedding_seconds = 0.0
    insertion_seconds = 0.0

    for start in range(0, len(all_chunks), BATCH_SIZE):
        end = start + BATCH_SIZE

        batch_chunks = all_chunks[start:end]
        batch_ids = all_ids[start:end]
        batch_metadata = all_metadata[start:end]

        t0 = perf_counter()
        embeddings = model.encode(
            batch_chunks,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        embedding_seconds += perf_counter() - t0

        t0 = perf_counter()
        collection.add(
            ids=batch_ids,
            documents=batch_chunks,
            metadatas=batch_metadata,
            embeddings=embeddings.tolist(),
        )
        insertion_seconds += perf_counter() - t0

    print("\nIngestion complete!")
    print(f"Documents: {len(files)}")
    print(f"Chunks stored: {collection.count()}")
    print(f"Embedding time: {embedding_seconds:.3f} seconds")
    print(f"Database insertion time: {insertion_seconds:.3f} seconds")
    print(f"Total measured processing time: "
          f"{embedding_seconds + insertion_seconds:.3f} seconds")
    print(f"Database location: {DB_DIR}")


if __name__ == "__main__":
    main()
