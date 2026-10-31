# Week 2, Day 2: Tool selection and descriptions

Run from this directory with `python -m pytest -q` (or from the repository root with `python -m pytest Week2/day2 -q`). No network or model is used.

## Files

- `tools.py` holds the mock catalog, tool descriptions, input checks, and three standalone functions. Each description states its use, non-use, arguments, and return shape. The functions validate inputs themselves so callers cannot skip the contract accidentally.
- `tool_selector.py` uses small regular-expression rules to recognize search, detail, and basket-total requests. `Selection` records the selected name, extracted arguments, and reason. Unsupported or incomplete requests return `tool_name=None` so the assistant can clarify instead of guessing.
- `test_tools.py` covers normal behavior, bad arguments, all three example selections, and unclear/unsupported requests.

Try `select_tool("Find rice under 20.")`, `select_tool("Show details for product P101.")`, and `select_tool("Calculate the total for 2 units of P101 and 1 unit of P102.")`. It intentionally cannot infer complex language or safely complete missing arguments; ask a follow-up when it returns no tool.
