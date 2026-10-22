
from schemas import (
    CalculatorInput,
    DatabaseLookupInput,
    WellnessSummaryInput,
)


def calculator(raw_input: dict) -> dict:
    data = CalculatorInput.model_validate(raw_input)

    if data.operation == "add":
        result = data.a + data.b

    elif data.operation == "subtract":
        result = data.a - data.b

    elif data.operation == "multiply":
        result = data.a * data.b

    elif data.operation == "divide":
        if data.b == 0:
            raise ValueError("Cannot divide by zero")

        result = data.a / data.b

    else:
        # Literal validation should reject unsupported operations
        # before execution reaches this point.
        raise ValueError("Unsupported operation")

    return {"result": result}


def mock_database_lookup(raw_input: dict) -> dict:
    data = DatabaseLookupInput.model_validate(raw_input)

    records = {
        "S101": {"name": "Anu", "marks": 85},
        "S102": {"name": "Rahul", "marks": 92},
    }

    record = records.get(data.student_id)

    if record is None:
        return {"found": False, "record": None}

    return {"found": True, "record": record}


def mock_wellness_summary(raw_input: dict) -> dict:
    data = WellnessSummaryInput.model_validate(raw_input)

    records = {
        "W101": {
            "sleep_hours": 7.5,
            "water_glasses": 8,
            "mood": "good",
            "private_notes": "Example private note",
        },
    }

    record = records.get(data.record_id)

    if record is None:
        return {"found": False, "record": None}

    # Return only explicitly permitted fields.
    safe_record = {
        field: record[field]
        for field in data.permitted_fields
        if field in record
    }

    return {"found": True, "record": safe_record}
