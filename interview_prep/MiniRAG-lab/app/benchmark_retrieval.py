
from pathlib import Path
from time import perf_counter
import csv
import math

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data" / "benchmark_db"
METRICS_DIR = BASE_DIR / "metrics"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DATASET_SIZES = [20, 200, 1000]

QUERY = "How can I improve vector search performance?"
TOP_K = 3
WARMUP_RUNS = 5
MEASURED_RUNS = 30


def percentile(values, p):
    """Calculate a percentile using the nearest-rank method."""
    ordered = sorted(values)
    index = max(0, math.ceil(p * len(ordered)) - 1)
    return ordered[index]


def summarize(values):
    return {
        "p50_ms": round(percentile(values, 0.50), 3),
        "p95_ms": round(percentile(values, 0.95), 3),
    }


def main():
    client = chromadb.PersistentClient(path=str(DB_DIR))

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    # Warm up the model before collecting measurements.
    model.encode(QUERY, normalize_embeddings=True)

    rows = []

    for size in DATASET_SIZES:
        collection = client.get_collection(f"benchmark_{size}")
        count = collection.count()

        if count == 0:
            raise ValueError(f"Collection for {size} is empty.")

        query_embedding = model.encode(
            QUERY,
            normalize_embeddings=True,
        ).tolist()

        # Warm up database search.
        for _ in range(WARMUP_RUNS):
            collection.query(
                query_embeddings=[query_embedding],
                n_results=min(TOP_K, count),
            )

        embedding_times = []
        retrieval_times = []

        for _ in range(MEASURED_RUNS):
            start = perf_counter()
            vector = model.encode(
                QUERY,
                normalize_embeddings=True,
            ).tolist()
            embedding_times.append(
                (perf_counter() - start) * 1000
            )

            start = perf_counter()
            collection.query(
                query_embeddings=[vector],
                n_results=min(TOP_K, count),
            )
            retrieval_times.append(
                (perf_counter() - start) * 1000
            )

        embedding_stats = summarize(embedding_times)
        retrieval_stats = summarize(retrieval_times)

        row = {
            "documents": size,
            "chunks": count,
            "embedding_p50_ms": embedding_stats["p50_ms"],
            "embedding_p95_ms": embedding_stats["p95_ms"],
            "retrieval_p50_ms": retrieval_stats["p50_ms"],
            "retrieval_p95_ms": retrieval_stats["p95_ms"],
        }
        rows.append(row)

        print(f"\nDataset: {size} documents")
        for key, value in row.items():
            print(f"{key}: {value}")

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    output = METRICS_DIR / "retrieval_benchmark.csv"

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults saved to: {output}")


if __name__ == "__main__":
    main()
