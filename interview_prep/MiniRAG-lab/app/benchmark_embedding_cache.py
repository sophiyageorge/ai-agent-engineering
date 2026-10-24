
from pathlib import Path
from time import perf_counter
import statistics
import csv

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data" / "benchmark_db"
METRICS_DIR = BASE_DIR / "metrics"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QUERY = "How can I improve vector search performance?"
COLLECTION_NAME = "benchmark_1000"
TOP_K = 3
RUNS = 100


def main():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    # Cache one vector for each exact query.
    embedding_cache = {}

    def get_embedding(query):
        if query not in embedding_cache:
            embedding_cache[query] = model.encode(
                query,
                normalize_embeddings=True,
            ).tolist()
        return embedding_cache[query]

    # Warm up the model and database.
    vector = get_embedding(QUERY)
    collection.query(
        query_embeddings=[vector],
        n_results=min(TOP_K, collection.count()),
    )

    baseline_times = []
    cached_times = []

    for _ in range(RUNS):
        # Baseline: embed on every request.
        start = perf_counter()
        vector = model.encode(
            QUERY,
            normalize_embeddings=True,
        ).tolist()
        collection.query(
            query_embeddings=[vector],
            n_results=min(TOP_K, collection.count()),
        )
        baseline_times.append((perf_counter() - start) * 1000)

        # Cached: reuse the existing vector.
        start = perf_counter()
        vector = get_embedding(QUERY)
        collection.query(
            query_embeddings=[vector],
            n_results=min(TOP_K, collection.count()),
        )
        cached_times.append((perf_counter() - start) * 1000)

    baseline_ms = statistics.median(baseline_times)
    cached_ms = statistics.median(cached_times)
    improvement = (
        (baseline_ms - cached_ms) / baseline_ms * 100
        if baseline_ms else 0
    )

    print(f"\nCollection chunks: {collection.count()}")
    print(f"Runs: {RUNS}")
    print(f"Baseline median: {baseline_ms:.3f} ms")
    print(f"Cached median: {cached_ms:.3f} ms")
    print(f"Latency reduction: {improvement:.1f}%")

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    output = METRICS_DIR / "embedding_cache_benchmark.csv"

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["mode", "median_latency_ms", "runs", "chunks"]
        )
        writer.writerow(
            ["baseline", round(baseline_ms, 3), RUNS, collection.count()]
        )
        writer.writerow(
            ["cached", round(cached_ms, 3), RUNS, collection.count()]
        )

    print(f"Results saved to: {output}")


if __name__ == "__main__":
    main()
