
import pytest
from pydantic import ValidationError

from tools import get_balance, transfer_money, MOCK_ACCOUNTS
from agent import run_tool
from agent import TOOL_REGISTRY


def setup_function():
    # Reset balances before each test.
    MOCK_ACCOUNTS["A1001"]["balance"] = 5000.0
    MOCK_ACCOUNTS["A1002"]["balance"] = 2500.0
    MOCK_ACCOUNTS["A1003"]["balance"] = 10000.0


# UNIT TESTS

def test_balance_success():
    result = get_balance({"account_number": "A1001"})

    assert result["success"] is True
    assert result["balance"] == 5000.0


def test_unknown_account():
    result = get_balance({"account_number": "A9999"})

    assert result["success"] is False
    assert result["error"] == "Account not found"


# SCHEMA TESTS

def test_missing_account_number():
    with pytest.raises(ValidationError):
        get_balance({})


def test_invalid_account_format():
    with pytest.raises(ValidationError):
        get_balance({"account_number": "12345"})


def test_extra_argument_rejected():
    with pytest.raises(ValidationError):
        get_balance({
            "account_number": "A1001",
            "admin": True,
        })


# TRANSFER TESTS

def test_simulated_transfer():
    result = transfer_money({
        "source_account": "A1001",
        "destination_account": "A1002",
        "amount": 500.0,
    })

    assert result["success"] is True
    assert MOCK_ACCOUNTS["A1001"]["balance"] == 4500.0
    assert MOCK_ACCOUNTS["A1002"]["balance"] == 3000.0


def test_negative_transfer_rejected():
    with pytest.raises(ValidationError):
        transfer_money({
            "source_account": "A1001",
            "destination_account": "A1002",
            "amount": -500.0,
        })


def test_transfer_insufficient_funds():
    result = transfer_money({
        "source_account": "A1002",
        "destination_account": "A1001",
        "amount": 3000.0,
    })

    assert result["success"] is False
    assert result["error"] == "Insufficient funds"


def test_transfer_to_same_account():
    result = transfer_money({
        "source_account": "A1001",
        "destination_account": "A1001",
        "amount": 100.0,
    })

    assert result["success"] is False
    assert MOCK_ACCOUNTS["A1001"]["balance"] == 5000.0





def test_integration_balance_lookup():
    response = run_tool(
        "get_balance",
        {"account_number": "A1001"},
    )

    assert response["result"]["success"] is True
    assert response["result"]["balance"] == 5000.0
    assert response["log"]["status"] == "success"
    assert response["log"]["invocation_id"]


def test_unknown_tool_is_rejected():
    response = run_tool("delete_everything", {})

    assert response["result"]["success"] is False
    assert response["result"]["error"] == "Unknown tool"
    assert response["log"]["status"] == "rejected"


def test_invalid_arguments_are_controlled():
    response = run_tool("get_balance", {})

    assert response["result"]["error"] == "Invalid tool arguments"
    assert response["log"]["status"] == "validation_error"


def test_tool_exception_is_hidden(monkeypatch):
    def broken_tool(arguments):
        raise RuntimeError("SECRET database credentials")

    monkeypatch.setitem(
        TOOL_REGISTRY, "get_balance", broken_tool
    )

    response = run_tool(
        "get_balance",
        {"account_number": "A1001"},
    )

    assert response["result"]["error"] == "Tool execution failed"
    assert "SECRET" not in str(response["result"])
    assert response["log"]["status"] == "error"

