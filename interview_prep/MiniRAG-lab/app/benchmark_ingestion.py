
from pathlib import Path
from time import perf_counter
import csv
import gc

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "benchmark_db"
METRICS_DIR = BASE_DIR / "metrics"

DATASET_SIZES = [20, 200, 1000]
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
BATCH_SIZE = 32

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def chunk_text(text: str) -> list[str]:
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
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(DB_DIR))

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    csv_path = METRICS_DIR / "ingestion_benchmark.csv"
    rows = []

    for size in DATASET_SIZES:
        dataset_dir = DATA_DIR / f"dataset_{size}"
        files = sorted(dataset_dir.glob("*.txt"))

        if len(files) != size:
            raise ValueError(
                f"Expected {size} documents in {dataset_dir}, "
                f"but found {len(files)}."
            )

        chunks = []
        ids = []
        metadatas = []

        # Measure document reading and chunking.
        start = perf_counter()

        for path in files:
            text = path.read_text(encoding="utf-8")

            for index, chunk in enumerate(chunk_text(text)):
                chunks.append(chunk)
                ids.append(f"doc{path.stem}_{index}")
                metadatas.append(
                    {
                        "source": path.name,
                        "chunk_index": index,
                    }
                )

        chunking_seconds = perf_counter() - start

        collection_name = f"benchmark_{size}"

        # Make reruns reproducible.
        try:
            client.delete_collection(collection_name)
        except Exception as exc:
            if "does not exist" not in str(exc).lower():
                raise

        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        embedding_seconds = 0.0
        insertion_seconds = 0.0

        for start_idx in range(0, len(chunks), BATCH_SIZE):
            end_idx = start_idx + BATCH_SIZE

            batch_chunks = chunks[start_idx:end_idx]
            batch_ids = ids[start_idx:end_idx]
            batch_metadata = metadatas[start_idx:end_idx]

            t0 = perf_counter()
            vectors = model.encode(
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
                embeddings=vectors.tolist(),
            )
            insertion_seconds += perf_counter() - t0

        # Flush pending database work before measuring disk usage.
        client = None
        gc.collect()

        disk_bytes = sum(
            p.stat().st_size
            for p in DB_DIR.rglob("*")
            if p.is_file()
        )

        # Reopen the persistent database for the next experiment.
        client = chromadb.PersistentClient(path=str(DB_DIR))
        collection = client.get_collection(collection_name)

        row = {
            "documents": size,
            "chunks": collection.count(),
            "chunking_seconds": round(chunking_seconds, 4),
            "embedding_seconds": round(embedding_seconds, 4),
            "insertion_seconds": round(insertion_seconds, 4),
            "processing_seconds": round(
                chunking_seconds + embedding_seconds + insertion_seconds,
                4,
            ),
            "database_bytes": disk_bytes,
        }

        rows.append(row)

        print(f"\nDataset: {size} documents")
        for key, value in row.items():
            print(f"{key}: {value}")

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nBenchmark saved to: {csv_path}")


if __name__ == "__main__":
    main()
