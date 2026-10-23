from schemas import AgentRequest
from safety import SafetyController


def run_agent(user_request: dict, authenticated_user_id: str):
    controller = SafetyController()

    try:
        request = AgentRequest.model_validate(user_request)
    except Exception:
        return {
            "ok": False,
            "error": "Invalid agent request.",
        }

    # Map only known actions to known tools.
    action_to_tool = {
        "balance": "check_balance",
        "account_info": "get_account_info",
    }

    tool_name = action_to_tool.get(request.action)

    if tool_name is None:
        return {
            "ok": False,
            "error": "I cannot perform that operation.",
        }

    arguments = {
        "account_no": request.account_no,
    }

    return controller.execute(
        tool_name=tool_name,
        arguments=arguments,
        caller_id=authenticated_user_id,
    )


if __name__ == "__main__":
    # Demo identity supplied by the trusted application.
    current_user = "user_1"

    response = run_agent(
        {
            "action": "balance",
            "account_no": "ACC1001",
        },
        authenticated_user_id=current_user,
    )

    print(response)