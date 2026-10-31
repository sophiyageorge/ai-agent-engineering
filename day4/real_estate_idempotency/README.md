# Day 4 — Idempotency and safe retries

## Goal

Create a monthly property report without creating duplicates when a client retries a request.

Imagine a property manager asks for the April report. The server creates it, but the reply gets lost. The client sends the same request again. An **idempotency key** is a request ID that tells the server: “This is the same job; return the report you already made.”

## Run the practical

From this folder, run:

```powershell
python main.py
```

The example creates an April report, simulates a retry with the same key, then tries using that key for a different month. The first two calls return the same report ID. The last call is rejected because one key must identify one request.

## Try it yourself

1. In `main.py`, call `create_monthly_report` twice with the same key and same arguments. Check that both responses have the same report ID.
2. Change the key for the second call. Check that a new report is created.
3. Reuse a key but change the month. Check that the request is rejected.
4. Restart the program and observe that the in-memory store is empty again.

## What to remember

- A retry should return the original result, not repeat the work.
- The caller must reuse the same key when retrying.
- A key cannot safely represent two different requests.
- This lab uses memory, so it only protects retries while the program is running. A real service stores keys and results in a shared database with a unique constraint and an atomic write.

## Files

- `reports.py` — validates report requests and stores one result per key.
- `main.py` — runs the example calls.
