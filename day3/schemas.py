
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CalculatorInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    operation: Literal[
        "add", "subtract", "multiply", "divide"
    ]

    a: float = Field(
        ge=-1_000_000,
        le=1_000_000,
        allow_inf_nan=False,
    )

    b: float = Field(
        ge=-1_000_000,
        le=1_000_000,
        allow_inf_nan=False,
    )


class DatabaseLookupInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    student_id: str = Field(
        min_length=1,
        max_length=20,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class WellnessSummaryInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    record_id: str = Field(
        min_length=1,
        max_length=30,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    permitted_fields: list[
        Literal["sleep_hours", "water_glasses", "mood"]
    ] = Field(min_length=1, max_length=3)
