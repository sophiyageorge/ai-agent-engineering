# Week 3, Day 1: Explain LangGraph Workflows

## Practical: Support request triage

Build and run a small LangGraph workflow that classifies an incoming support
request, chooses a route, and drafts a response. It is deterministic: no model,
credentials, or network access is needed. This makes the workflow structure
visible before adding an LLM.

### Setup and run

From the repository root:

```powershell
python -m pip install -r requirements.txt
python Week3/day1/workflow_lab.py
```

Or activate the repository's virtual environment first and use its `python`.

### What to observe

- **State** (`SupportState`) carries the request and results between nodes.
- **Nodes** are ordinary Python functions. Each returns only the fields it
  updates; LangGraph merges those updates into the shared state.
- **Edges** run `START → classify → choose_route` in order.
- **Conditional routing** sends urgent requests to `urgent_draft` and routine
  requests to `routine_draft`.
- **END** marks completion. The `trace` field makes the chosen path inspectable.
- Urgent drafts are flagged for human review; this demo never sends a reply.

Run the script and compare the two printed traces. Then try changing the sample
requests in `run_examples()` (for example, “The service is down” and “How do I
change my profile?”). The final two assertions check that both branches behave
as intended.

### Workout extensions

1. Add a `sentiment` or `language` field to state and populate it in a new node.
2. Add a `billing` route and a dedicated draft node. Update the router and
   conditional edge map; check that all supported route labels are handled.
3. Add a node before drafting that validates the request is non-empty. Decide
   how invalid input should end without creating a draft.
4. Add an `approval_status` field and keep the human review as an explicit
   boundary. Do not add a node that sends messages or changes a real account.

### Concepts to retain

Use a graph when you need visible, stateful steps and explicit control over
branching or cycles. A straight-line function is simpler when there is only one
small operation. LangGraph does not make keyword classification intelligent;
an LLM can replace the classifier later while routing and review boundaries
remain explicit.
