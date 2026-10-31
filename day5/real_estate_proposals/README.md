# Day 5 — Proposals versus execution

## Goal

Keep an AI suggestion separate from a real change to a property listing.

The AI can suggest changing a property's monthly rent. A suggestion is only a **proposal**: it does not update the listing. The application checks the proposal, and only the authenticated property owner can approve it. Approval executes the change.

## Run the practical

From this folder, run:

```powershell
python main.py
```

The example proposes a rent change for property `P101`, shows that the rent is still unchanged, then approves the proposal as its owner and shows the updated rent.

## Try it yourself

1. Try to approve as `agent` instead of `owner_1`. It should be denied and rent should stay unchanged.
2. Try an invalid rent such as `-500`. Proposal validation should reject it.
3. Approve the same proposal twice. The second approval should report that it was already executed and must not apply another change.
4. Try a made-up property ID. No proposal should be created.

## What to remember

- AI output is untrusted input, even when it looks sensible.
- Validate the proposed action before storing it.
- Use identity from the trusted application, not from the AI proposal.
- Keep proposal creation and execution as separate steps.
- This lab uses in-memory data for learning; production approval and execution need durable storage and audit records.

## Files

- `workflow.py` — proposal validation, owner approval, and execution.
- `main.py` — runs the example workflow.
