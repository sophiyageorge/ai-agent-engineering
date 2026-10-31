from reports import REPORTS_BY_KEY, create_monthly_report


if __name__ == "__main__":
    REPORTS_BY_KEY.clear()
    request = {
        "idempotency_key": "manager-42-april-report",
        "month": "2026-04",
    }

    first = create_monthly_report(request)
    retry = create_monthly_report(request)  # Simulate a lost reply and retry.
    wrong_reuse = create_monthly_report({
        "idempotency_key": request["idempotency_key"],
        "month": "2026-05",
    })

    print("First request:", first)
    print("Retry:", retry)
    print("Same report ID:", first.get("report_id") == retry.get("report_id"))
    print("Key reused for another month:", wrong_reuse)
