from uuid import uuid4

from tools import check_balance, get_account_info


# Allowlist: only registered tools can execute.
TOOL_REGISTRY = {
    "check_balance": check_balance,
    "get_account_info": get_account_info,
}

MAX_TOOL_CALLS = 3
MAX_INPUT_LENGTH = 1000


class SafetyController:
    def __init__(self):
        self.calls_used = 0
        self.audit_log = []

    def execute(self, tool_name, arguments, caller_id):
        invocation_id = str(uuid4())

        def log(status, error_code=None):
            # Do not log account numbers, balances, or raw arguments.
            self.audit_log.append({
                "invocation_id": invocation_id,
                "tool": tool_name,
                "status": status,
                "error_code": error_code,
            })

        # 1. Bound the number of tool attempts.
        if self.calls_used >= MAX_TOOL_CALLS:
            log("rejected", "tool_call_limit")
            return {
                "ok": False,
                "error": "Tool-call limit reached.",
            }

        self.calls_used += 1

        # 2. Enforce the tool allowlist.
        tool = TOOL_REGISTRY.get(tool_name)

        if tool is None:
            log("rejected", "unknown_tool")
            return {
                "ok": False,
                "error": "Unsupported operation.",
            }

        # 3. Validate the argument container and its size.
        if not isinstance(arguments, dict):
            log("rejected", "invalid_input")
            return {"ok": False, "error": "Invalid input."}

        if len(str(arguments)) > MAX_INPUT_LENGTH:
            log("rejected", "input_too_large")
            return {"ok": False, "error": "Input too large."}

        # 4. Execute with controlled error handling.
        try:
            result = tool(arguments, caller_id)
            log("success")

            return {
                "ok": True,
                "result": result,
                "invocation_id": invocation_id,
            }

        except PermissionError:
            log("denied", "access_denied")
            return {
                "ok": False,
                "error": "Account access denied.",
            }

        except ValueError:
            log("rejected", "invalid_input")
            return {
                "ok": False,
                "error": "Invalid input.",
            }

        except Exception:
            # Never return raw exception details to the customer.
            log("failed", "internal_error")
            return {
                "ok": False,
                "error": "A temporary error occurred.",
            }