
from uuid import uuid4
from time import perf_counter

from pydantic import ValidationError
from tools import get_balance, transfer_money


TOOL_REGISTRY = {
    "get_balance": get_balance,
    "transfer_money": transfer_money,
}


def run_tool(tool_name: str, arguments: dict) -> dict:
    invocation_id = str(uuid4())
    started = perf_counter()

    log = {
        "invocation_id": invocation_id,
        "tool": tool_name,
    }

    try:
        tool = TOOL_REGISTRY.get(tool_name)

        if tool is None:
            result = {
                "success": False,
                "error": "Unknown tool",
            }
            log["status"] = "rejected"

        else:
            result = tool(arguments)
            log["status"] = (
                "success" if result.get("success") else "failure"
            )

    except ValidationError:
        result = {
            "success": False,
            "error": "Invalid tool arguments",
        }
        log["status"] = "validation_error"

    except Exception:
        # Keep internal exception details out of the response.
        result = {
            "success": False,
            "error": "Tool execution failed",
        }
        log["status"] = "error"

    log["duration_ms"] = round(
        (perf_counter() - started) * 1000, 2
    )

    # Demo logging only. A real system needs protected,
    # structured, persistent audit logging.
    return {
        "result": result,
        "log": log,
    }
