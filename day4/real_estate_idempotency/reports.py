from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


# Fictional property data for learning only.
PROPERTY_RENT = {
    "P101": 2400,
    "P102": 3100,
    "P103": 1850,
}


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    idempotency_key: str = Field(min_length=1, max_length=100)
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


# Demo store: key -> (month, report). A database is needed in production.
REPORTS_BY_KEY = {}


def create_monthly_report(arguments: dict) -> dict:
    request = ReportRequest.model_validate(arguments)
    previous = REPORTS_BY_KEY.get(request.idempotency_key)

    if previous is not None:
        previous_month, previous_report = previous
        if previous_month != request.month:
            return {
                "success": False,
                "error": "Idempotency key was already used for a different request.",
            }
        return {**previous_report, "replayed": True}

    report = {
        "success": True,
        "report_id": str(uuid4()),
        "month": request.month,
        "property_count": len(PROPERTY_RENT),
        "monthly_rent_total": sum(PROPERTY_RENT.values()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "replayed": False,
    }
    REPORTS_BY_KEY[request.idempotency_key] = (request.month, report)
    return report
