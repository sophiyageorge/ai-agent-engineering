
from pathlib import Path

DOCUMENTS_DIR = Path("data/documents")
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

documents = [
    ("python_basics", """
Python is a programming language used for automation,
data analysis, web development, and artificial intelligence.
Python supports functions, classes, modules, and packages.
"""),
    ("python_functions", """
A Python function is defined using the def keyword.
Functions accept parameters and can return values.
Reusable functions make software easier to test and maintain.
"""),
    ("python_lists", """
A Python list stores an ordered collection of elements.
Lists support indexing, slicing, appending, and removing items.
A list can contain strings, numbers, and other objects.
"""),
    ("python_dictionaries", """
A Python dictionary stores key-value pairs.
Dictionaries are useful for representing structured records.
Keys are unique, and values can be accessed using their keys.
"""),
    ("python_errors", """
Python exceptions represent errors that occur during execution.
Try and except blocks help handle expected failures.
Applications should log errors and return useful messages.
"""),
    ("sql_basics", """
SQL is used to query and manage relational databases.
SELECT retrieves data, INSERT adds rows, and UPDATE modifies rows.
WHERE filters records based on specified conditions.
"""),
    ("database_indexes", """
A database index can speed up queries that search specific columns.
Indexes require storage and add overhead to data modifications.
The best indexes depend on query patterns and data distribution.
"""),
    ("api_basics", """
An API allows software components to communicate.
HTTP APIs commonly use GET to retrieve data and POST to submit data.
APIs should validate input and handle errors consistently.
"""),
    ("fastapi", """
FastAPI is a Python framework for building APIs.
It supports request validation, type hints, and asynchronous endpoints.
Uvicorn can run a FastAPI application as an ASGI server.
"""),
    ("embeddings", """
Embeddings represent text as numerical vectors.
Semantically similar text can have vectors that are close together.
Embedding quality depends on the model and the type of text.
"""),
    ("vector_search", """
Vector search retrieves items using vector similarity.
It is commonly used to find semantically relevant document chunks.
Search quality depends on embeddings, indexing, and retrieval settings.
"""),
    ("rag_basics", """
Retrieval-Augmented Generation combines information retrieval with
language model generation. Retrieved context helps a language model
answer questions using a relevant external knowledge source.
"""),
    ("rag_chunking", """
Chunking divides long documents into smaller text segments.
Chunk size and overlap influence context, retrieval quality,
index size, and the number of embeddings that must be stored.
"""),
    ("rag_retrieval", """
A RAG retriever selects relevant chunks for a user question.
Top-k controls how many results are returned.
Retrieval should be evaluated for relevance and latency.
"""),
    ("rag_evaluation", """
RAG evaluation measures retrieval relevance and answer quality.
Useful metrics include recall at k, groundedness, latency, and cost.
A fixed test dataset helps compare changes consistently.
"""),
    ("llm_tokens", """
Language models process text as tokens.
Prompt length and generated output affect latency and API cost.
Reducing unnecessary context can improve efficiency.
"""),
    ("caching", """
Caching stores reusable results to avoid repeated computation.
A RAG system can cache embeddings, retrieval results, or answers.
Cache invalidation and user permissions must be handled carefully.
"""),
    ("background_jobs", """
Background jobs process tasks outside the main request-response path.
Document parsing and embedding generation can be handled asynchronously.
Queues help control workload and recover from transient failures.
"""),
    ("horizontal_scaling", """
Horizontal scaling adds multiple application instances.
A load balancer distributes requests among available instances.
Shared state and database capacity must be considered.
"""),
    ("vertical_scaling", """
Vertical scaling increases resources on a single machine.
Adding CPU or RAM can help when the machine is resource constrained.
Vertical scaling is limited by available machine sizes and cost.
"""),
]

for name, content in documents:
    file_path = DOCUMENTS_DIR / f"{name}.txt"
    file_path.write_text(content.strip(), encoding="utf-8")

print(f"Created {len(documents)} documents in {DOCUMENTS_DIR.resolve()}")

for path in sorted(DOCUMENTS_DIR.glob("*.txt")):
    print(f"- {path.name}")
