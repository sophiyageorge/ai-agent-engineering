# Week 3, Day 2: State, reducers, and parallel nodes

## Practical: Student marks workflow

Run from the repository root:

```powershell
python -m pip install -r requirements.txt
python Week3/day2/marks_workflow.py
```

The exercise is deterministic and uses no model, credentials, or network calls.

### What to observe

- `StudentState` is a `TypedDict`. Nodes receive state and return partial
  dictionaries containing only the keys they update.
- `retrieve_marks` validates and returns marks; `calculate_total` adds a total.
  Other state, such as the student name and notes, remains in the state.
- A normal state field uses replacement. The status starts as `validated` and
  becomes `calculated` when the later node writes it.
- The parallel example starts two retrieval nodes in the same super-step. Each
  writes `subjects`; without a reducer LangGraph raises `InvalidUpdateError`.
- `Annotated[list[str], operator.add]` combines concurrent list updates. The
  custom reducer demonstrates a stable unique merge.
- Graph execution advances in super-steps: nodes enabled by the prior step run
  together, their writes are collected, reducers combine writes to shared
  channels, and then the next step begins. Nodes in one super-step should not
  rely on seeing each other's updates.
- Validation exceptions from nodes propagate to the caller; the script catches
  them at the invocation boundary and prints the errors.

### Try next

1. Add a history field and a reducer that keeps only the last three entries.
2. Add a validation rule that rejects marks above 100.
3. Add another parallel subject retrieval. Check which fields need reducers
   when multiple nodes can write them during the same super-step.
4. Use `app.stream(..., stream_mode="updates")` to inspect per-node updates and
   identify the super-step boundaries.
