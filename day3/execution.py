
import logging
import time
import uuid
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("agent.execution")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


def execute_tool(
    tool_name: str,
    tool_func: Callable,
    input_schema: type[BaseModel],
    raw_input: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    request_id = request_id or str(uuid.uuid4())
    invocation_id = str(uuid.uuid4())
    start = time.perf_counter()

    def log_event(status: str, error_type: str | None = None):
        event = {
            "event": "tool_execution",
            "tool": tool_name,
            "request_id": request_id,
            "invocation_id": invocation_id,
            "status": status,
            "duration_ms": round(
                (time.perf_counter() - start) * 1000, 2
            ),
        }
        if error_type:
            event["error_type"] = error_type

        logger.info(__import__("json").dumps(event))

    try:
        validated = input_schema.model_validate(raw_input)
        result = tool_func(**validated.model_dump())

        log_event("success")
        return {
            "ok": True,
            "request_id": request_id,
            "invocation_id": invocation_id,
            "data": result,
        }

    except ValidationError:
        log_event("failure", "ValidationError")
        return {
            "ok": False,
            "request_id": request_id,
            "invocation_id": invocation_id,
            "error": "Invalid tool input.",
        }

    except ZeroDivisionError:
        log_event("failure", "ZeroDivisionError")
        return {
            "ok": False,
            "request_id": request_id,
            "invocation_id": invocation_id,
            "error": "The calculation could not be completed.",
        }

    except Exception:
        # Do not expose the raw exception to the user.
        log_event("failure", "InternalError")
        return {
            "ok": False,
            "request_id": request_id,
            "invocation_id": invocation_id,
            "error": "The tool could not complete the request.",
        }
