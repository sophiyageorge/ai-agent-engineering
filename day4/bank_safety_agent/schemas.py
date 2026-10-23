from pydantic import BaseModel, ConfigDict, Field


class BalanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    account_no: str = Field(
        pattern=r"^ACC[0-9]{4}$"
    )


class AccountInfoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    account_no: str = Field(
        pattern=r"^ACC[0-9]{4}$"
    )


class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    action: str
    account_no: str