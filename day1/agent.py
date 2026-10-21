
import logging
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


# 1. Configure logs
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger("day1_agent")


# 2. Define schemas for permitted inputs
class CalculationRequest(BaseModel):
    type: Literal["calculation"]
    operation: Literal["add", "subtract", "multiply", "divide"]
    a: float = Field(allow_inf_nan=False)
    b: float = Field(allow_inf_nan=False)


class StudentLookupRequest(BaseModel):
    type: Literal["student_lookup"]
    student_id: str = Field(min_length=1, max_length=20)


# 3. Tool 1: Calculator
def calculator(operation: str, a: float, b: float):
    logger.info("Tool started: calculator")

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
    else:
        raise ValueError("Unsupported operation")

    logger.info("Tool completed: calculator")
    return result


# 4. Tool 2: Mock database lookup
def mock_database_lookup(student_id: str):
    logger.info("Tool started: student_lookup")

    records = {
        "S101": {"name": "Anu", "marks": 85},
        "S102": {"name": "Rahul", "marks": 92},
        "S103": {"name": "Mia", "marks": 78},
    }

    result = records.get(student_id)

    logger.info(
        "Tool completed: student_lookup | found=%s",
        result is not None,
    )
    return result


# 5. Agent: validates and routes the request
def agent(request: dict):
    request_type = request.get("type")

    try:
        if request_type == "calculation":
            validated = CalculationRequest.model_validate(request)

            return {
                "status": "success",
                "result": calculator(
                    validated.operation,
                    validated.a,
                    validated.b,
                ),
            }

        elif request_type == "student_lookup":
            validated = StudentLookupRequest.model_validate(request)
            result = mock_database_lookup(validated.student_id)

            if result is None:
                return {
                    "status": "not_found",
                    "message": "Student record not found",
                }

            return {"status": "success", "result": result}

        else:
            return {
                "status": "unsupported",
                "message": "I cannot handle this request type",
            }

    except ValidationError:
        logger.warning("Request rejected: invalid input")
        return {
            "status": "invalid_input",
            "message": "Request fields or values are invalid",
        }

    except ValueError as exc:
        logger.warning("Tool rejected request: %s", exc)
        return {
            "status": "error",
            "message": str(exc),
        }

    except Exception:
        logger.exception("Unexpected agent failure")
        return {
            "status": "error",
            "message": "An unexpected error occurred",
        }


if __name__ == "__main__":
    tests = [
        {
            "type": "calculation",
            "operation": "multiply",
            "a": 250,
            "b": 4,
        },
        {
            "type": "calculation",
            "operation": "subtract",
            "a": 100,
            "b": 85,
        },
        {
            "type": "calculation",
            "operation": "divide",
            "a": 10,
            "b": 0,
        },
        {"type": "student_lookup", "student_id": "S101"},
        {"type": "student_lookup", "student_id": "S999"},
        {"type": "unknown"},
        {
            "type": "calculation",
            "operation": "delete_database",
            "a": 10,
            "b": 2,
        },
    ]

    for test in tests:
        print(f"\nRequest: {test}")
        print(f"Response: {agent(test)}")
