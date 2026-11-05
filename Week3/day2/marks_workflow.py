"""Week 3, Day 2: LangGraph state, reducers, and parallel updates.

Deterministic examples; no model, credentials, or network access required.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict

from langgraph.errors import InvalidUpdateError
from langgraph.graph import END, START, StateGraph


class StudentState(TypedDict, total=False):
    student: str
    marks: dict[str, int]
    total: int
    status: str
    subjects: Annotated[list[str], add]
    notes: Annotated[list[str], add]


class ParallelState(TypedDict, total=False):
    student: str
    subjects: Annotated[list[str], add]
    notes: Annotated[list[str], add]


class ConflictingParallelState(TypedDict, total=False):
    student: str
    subjects: list[str]
    notes: Annotated[list[str], add]


SAMPLE_MARKS = {"math": 92, "science": 88, "english": 85}


def validate_student(state: StudentState) -> StudentState:
    student = state.get("student", "").strip()
    if not student:
        raise ValueError("student must be a non-empty name")
    return {"student": student, "status": "validated"}


def retrieve_marks(state: StudentState) -> StudentState:
    """Return only this node's partial state update."""
    if "marks" not in state:
        raise ValueError("marks are required before calculating a total")
    marks = state["marks"]
    if not marks or any(not isinstance(mark, int) or mark < 0 for mark in marks.values()):
        raise ValueError("marks must contain non-negative integer scores")
    return {"marks": dict(marks), "subjects": list(marks)}


def calculate_total(state: StudentState) -> StudentState:
    return {"total": sum(state["marks"].values())}


def retrieve_math(state: dict[str, object]) -> dict[str, object]:
    return {"subjects": ["math"], "notes": ["math retrieval complete"]}


def retrieve_science(state: dict[str, object]) -> dict[str, object]:
    return {"subjects": ["science"], "notes": ["science retrieval complete"]}


def replace_with_latest(state: StudentState) -> StudentState:
    """A plain field uses replacement: this becomes the new status value."""
    return {"status": "calculated"}


def build_serial_workflow():
    graph = StateGraph(StudentState)
    graph.add_node("validate", validate_student)
    graph.add_node("retrieve_marks", retrieve_marks)
    graph.add_node("calculate_total", calculate_total)
    graph.add_node("replace_status", replace_with_latest)
    graph.add_edge(START, "validate")
    graph.add_edge("validate", "retrieve_marks")
    graph.add_edge("retrieve_marks", "calculate_total")
    graph.add_edge("calculate_total", "replace_status")
    graph.add_edge("replace_status", END)
    return graph.compile()


def build_parallel_workflow(*, with_reducer: bool):
    """Fan out to two retrieval nodes; both write the `subjects` channel."""
    schema = ParallelState if with_reducer else ConflictingParallelState
    graph = StateGraph(schema)
    graph.add_node("math", retrieve_math)
    graph.add_node("science", retrieve_science)
    graph.add_edge(START, "math")
    graph.add_edge(START, "science")
    graph.add_edge("math", END)
    graph.add_edge("science", END)
    return graph.compile()


def unique_in_order(existing: list[str], incoming: list[str]) -> list[str]:
    """Custom reducer: combine values while keeping first-seen order."""
    return list(dict.fromkeys([*existing, *incoming]))


class UniqueState(TypedDict, total=False):
    subjects: Annotated[list[str], unique_in_order]


def build_custom_reducer_workflow():
    graph = StateGraph(UniqueState)
    graph.add_node("first", lambda state: {"subjects": ["math", "science"]})
    graph.add_node("second", lambda state: {"subjects": ["science", "english"]})
    graph.add_edge(START, "first")
    graph.add_edge(START, "second")
    graph.add_edge("first", END)
    graph.add_edge("second", END)
    return graph.compile()


def run_examples() -> None:
    app = build_serial_workflow()
    initial = {"student": "  Asha  ", "marks": SAMPLE_MARKS, "notes": ["started"]}
    result = app.invoke(initial)
    print("Serial workflow (partial updates and replacement):")
    print(f"  student={result['student']!r}, total={result['total']}, status={result['status']!r}")
    print(f"  marks retained={result['marks'] == SAMPLE_MARKS}; notes retained={result['notes']}")

    print("\nParallel retrieval (two nodes write the same unreduced channel):")
    try:
        build_parallel_workflow(with_reducer=False).invoke({"student": "Asha"})
    except InvalidUpdateError as error:
        print(f"  Expected concurrent update error: {error}")
    else:
        raise AssertionError("expected an InvalidUpdateError for concurrent writes")

    parallel = build_parallel_workflow(with_reducer=True).invoke({"student": "Asha"})
    print(f"\nParallel retrieval with list reducer: subjects={parallel['subjects']}, notes={parallel['notes']}")
    unique = build_custom_reducer_workflow().invoke({})
    print(f"Custom reducer (stable unique merge): {unique['subjects']}")

    # Validation and node errors are ordinary Python exceptions and can be handled by callers.
    try:
        app.invoke({"student": "  ", "marks": SAMPLE_MARKS})
    except ValueError as error:
        print(f"\nValidation handled: {error}")
    else:
        raise AssertionError("expected blank student validation to fail")
    try:
        app.invoke({"student": "Asha", "marks": {"math": -1}})
    except ValueError as error:
        print(f"Invalid marks handled: {error}")
    else:
        raise AssertionError("expected negative marks validation to fail")

    assert result["total"] == 265
    assert result["status"] == "calculated"  # plain fields take the latest update
    assert unique["subjects"] == ["math", "science", "english"]
    print("\nChecks passed.")


if __name__ == "__main__":
    run_examples()
