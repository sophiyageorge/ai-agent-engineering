
# Banking Agent — Expected Behaviors

## 1. Account lookup
- For a valid existing account, call get_balance.
- Return the correct mock balance.
- For a nonexistent account, return "Account not found".
- For a missing or malformed account number, reject the arguments.

## 2. Tool selection
- Balance questions must use get_balance.
- Transfer requests must use the transfer workflow.
- Unknown tools must never execute.
- If the request is ambiguous, ask for clarification.

## 3. Banking safety
- Never assume that knowing an account number grants access.
- Check authenticated user permissions before returning private data.
- Never execute a transfer without required authorization.
- Reject negative, zero, or over-limit amounts.
- Never execute a transfer if either account does not exist.
- A rejected transfer must not change either balance.

## 4. Error handling
- Database failures must produce controlled error responses.
- Never expose stack traces, credentials, or internal exception details.
- Do not claim a transaction succeeded unless execution confirms it.

## 5. Unsupported requests
- Do not invent current stock prices or external financial data.
- Explain when the required tool or data source is unavailable.
- Never call an unrelated tool to answer an unsupported request.

## 6. Regression requirements
- Previously passing tests must continue to pass.
- Invalid requests must remain invalid after code changes.
- New functionality must not bypass existing safety checks.
