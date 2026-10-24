
import json
from pathlib import Path

from agent import run_tool
from tools import MOCK_ACCOUNTS


DATASET_PATH = Path(__file__).parent / "regression_dataset.json"


def reset_accounts():
    """Keep each test independent."""
    MOCK_ACCOUNTS["A1001"]["balance"] = 5000.0
    MOCK_ACCOUNTS["A1002"]["balance"] = 2500.0
    MOCK_ACCOUNTS["A1003"]["balance"] = 10000.0


def evaluate_case(case):
    reset_accounts()

    actual = run_tool(
        case["tool"],
        case["arguments"],
    )

    result = actual["result"]
    log = actual["log"]

    checks = {
        "status": log["status"] == case["expected_status"],
        "success": result.get("success") == case["expected_success"],
    }

    if "expected_balance" in case:
        checks["balance"] = (
            result.get("balance") == case["expected_balance"]
        )

    if "expected_error" in case:
        checks["error"] = (
            result.get("error") == case["expected_error"]
        )

    return {
        "id": case["id"],
        "request": case["request"],
        "passed": all(checks.values()),
        "checks": checks,
        "actual_status": log["status"],
    }


def main():
    with DATASET_PATH.open(encoding="utf-8") as file:
        dataset = json.load(file)

    results = [evaluate_case(case) for case in dataset]

    print("\nBANKING AGENT EVALUATION")
    print("-" * 55)

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f'{result["id"]}: {status}')
        print(f'  Request: {result["request"]}')

        for check, passed in result["checks"].items():
            print(f"  {check}: {'OK' if passed else 'MISMATCH'}")

    passed_count = sum(r["passed"] for r in results)
    total = len(results)
    rate = 100 * passed_count / total if total else 0

    print("-" * 55)
    print(f"Passed: {passed_count}/{total}")
    print(f"Evaluation pass rate: {rate:.1f}%")


if __name__ == "__main__":
    main()
