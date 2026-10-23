from schemas import BalanceRequest, AccountInfoRequest

# Fictional data for learning only.
BANK_DATABASE = {
    "ACC1001": {
        "owner_id": "user_1",
        "account_no": "ACC1001",
        "account_type": "Savings",
        "balance": 12500.50,
        "currency": "AED",
    },
    "ACC1002": {
        "owner_id": "user_2",
        "account_no": "ACC1002",
        "account_type": "Current",
        "balance": 8300.00,
        "currency": "AED",
    },
}


def check_balance(arguments: dict, caller_id: str) -> dict:
    request = BalanceRequest.model_validate(arguments)

    account = BANK_DATABASE.get(request.account_no)

    # Fail closed: do not reveal another customer's balance.
    if account is None or account["owner_id"] != caller_id:
        raise PermissionError("Account access denied")

    return {
        "balance": account["balance"],
        "currency": account["currency"],
    }


def get_account_info(arguments: dict, caller_id: str) -> dict:
    request = AccountInfoRequest.model_validate(arguments)

    account = BANK_DATABASE.get(request.account_no)

    if account is None or account["owner_id"] != caller_id:
        raise PermissionError("Account access denied")

    # Return only the fields needed by the caller.
    return {
        "account_no": account["account_no"],
        "account_type": account["account_type"],
        "currency": account["currency"],
    }