
import pytest
from pydantic import ValidationError

from tools import (
    calculator,
    mock_database_lookup,
    mock_wellness_summary,
)


def test_calculator_addition():
    assert calculator({
        "operation": "add",
        "a": 10,
        "b": 5,
    }) == {"result": 15}


def test_calculator_division():
    assert calculator({
        "operation": "divide",
        "a": 10,
        "b": 2,
    }) == {"result": 5}


def test_division_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator({
            "operation": "divide",
            "a": 10,
            "b": 0,
        })


def test_invalid_operation():
    with pytest.raises(ValidationError):
        calculator({
            "operation": "power",
            "a": 2,
            "b": 3,
        })


def test_extra_calculator_field():
    with pytest.raises(ValidationError):
        calculator({
            "operation": "add",
            "a": 10,
            "b": 5,
            "admin": True,
        })


def test_invalid_numeric_type():
    with pytest.raises(ValidationError):
        calculator({
            "operation": "add",
            "a": "10",
            "b": 5,
        })


def test_known_student():
    result = mock_database_lookup({"student_id": "S101"})

    assert result == {
        "found": True,
        "record": {"name": "Anu", "marks": 85},
    }


def test_unknown_student():
    result = mock_database_lookup({"student_id": "S999"})

    assert result == {"found": False, "record": None}


def test_wellness_field_allowlist():
    result = mock_wellness_summary({
        "record_id": "W101",
        "permitted_fields": ["sleep_hours", "mood"],
    })

    assert result == {
        "found": True,
        "record": {
            "sleep_hours": 7.5,
            "mood": "good",
        },
    }

    assert "private_notes" not in result["record"]


def test_invalid_wellness_field():
    with pytest.raises(ValidationError):
        mock_wellness_summary({
            "record_id": "W101",
            "permitted_fields": ["private_notes"],
        })


def test_unknown_wellness_record():
    result = mock_wellness_summary({
        "record_id": "W999",
        "permitted_fields": ["mood"],
    })

    assert result == {"found": False, "record": None}
