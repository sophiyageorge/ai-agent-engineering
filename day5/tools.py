
from pydantic import BaseModel, ConfigDict, Field


# All data is fictional.
MOCK_ACCOUNTS = {
    "A1001": {"name": "Maya", "balance": 5000.0},
    "A1002": {"name": "Adam", "balance": 2500.0},
    "A1003": {"name": "Sara", "balance": 10000.0},
}


class BalanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    account_number: str = Field(
        pattern=r"^A\d{4}$"
    )


class TransferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source_account: str = Field(pattern=r"^A\d{4}$")
    destination_account: str = Field(pattern=r"^A\d{4}$")
    amount: float = Field(gt=0, le=10000)


def get_balance(arguments: dict) -> dict:
    request = BalanceRequest.model_validate(arguments)

    account = MOCK_ACCOUNTS.get(request.account_number)

    if account is None:
        return {
            "success": False,
            "error": "Account not found",
        }

    return {
        "success": True,
        "account_number": request.account_number,
        "balance": account["balance"],
    }


def transfer_money(arguments: dict) -> dict:
    request = TransferRequest.model_validate(arguments)

    if request.source_account == request.destination_account:
        return {
            "success": False,
            "error": "Source and destination must differ",
        }

    source = MOCK_ACCOUNTS.get(request.source_account)
    destination = MOCK_ACCOUNTS.get(request.destination_account)

    if source is None or destination is None:
        return {
            "success": False,
            "error": "Account not found",
        }

    if source["balance"] < request.amount:
        return {
            "success": False,
            "error": "Insufficient funds",
        }

    # Simulate a transfer in this in-memory demo only.
    source["balance"] -= request.amount
    destination["balance"] += request.amount

    return {
        "success": True,
        "message": "Simulated transfer completed",
        "amount": request.amount,
    }
