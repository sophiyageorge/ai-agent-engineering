
import json
import logging

from execution import execute_tool
from schemas import CalculatorInput
from tools import calculator


def test_successful_calculation(caplog):
    with caplog.at_level(logging.INFO, logger="agent.execution"):
        result = execute_tool(
            "calculator",
            calculator,
            CalculatorInput,
            {"operation": "add", "a": 10, "b": 5},
        )

    assert result["ok"] is True
    assert result["data"] == 15
    assert result["invocation_id"]
    assert result["request_id"]

    event = json.loads(caplog.records[-1].message)
    assert event["status"] == "success"


def test_division_by_zero(caplog):
    with caplog.at_level(logging.INFO, logger="agent.execution"):
        result = execute_tool(
            "calculator",
            calculator,
            CalculatorInput,
            {"operation": "divide", "a": 10, "b": 0},
        )

    assert result["ok"] is False
    assert result["invocation_id"]

    event = json.loads(caplog.records[-1].message)
    assert event["status"] == "failure"
    assert event["error_type"] == "ZeroDivisionError"


def test_invalid_schema(caplog):
    with caplog.at_level(logging.INFO, logger="agent.execution"):
        result = execute_tool(
            "calculator",
            calculator,
            CalculatorInput,
            {"operation": "power", "a": 2, "b": 3},
        )

    assert result["ok"] is False
    assert result["invocation_id"]

    event = json.loads(caplog.records[-1].message)
    assert event["status"] == "failure"
    assert event["error_type"] == "ValidationError"


def test_exception_details_are_not_exposed():
    def broken_tool(**kwargs):
        raise RuntimeError("SECRET_DATABASE_PASSWORD")

    result = execute_tool(
        "broken_tool",
        broken_tool,
        CalculatorInput,
        {"operation": "add", "a": 1, "b": 2},
    )

    assert result["ok"] is False
    assert "SECRET_DATABASE_PASSWORD" not in str(result)


def test_each_attempt_has_an_invocation_id():
    first = execute_tool(
        "calculator", calculator, CalculatorInput,
        {"operation": "add", "a": 1, "b": 2},
    )
    second = execute_tool(
        "calculator", calculator, CalculatorInput,
        {"operation": "add", "a": 3, "b": 4},
    )

    assert first["invocation_id"] != second["invocation_id"]


def test_failure_and_success_statuses_are_logged(caplog):
    with caplog.at_level(logging.INFO, logger="agent.execution"):
        execute_tool(
            "calculator", calculator, CalculatorInput,
            {"operation": "add", "a": 1, "b": 2},
        )
        execute_tool(
            "calculator", calculator, CalculatorInput,
            {"operation": "divide", "a": 1, "b": 0},
        )

    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "agent.execution"
    ]

    statuses = [event["status"] for event in events]
    assert "success" in statuses
    assert "failure" in statuses
