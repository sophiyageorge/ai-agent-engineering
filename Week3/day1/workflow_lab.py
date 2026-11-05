"""A deterministic LangGraph workflow for triaging support requests.

No model, API key, or network call is required. The keyword rules keep the
workflow predictable so the graph mechanics are easy to observe.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class SupportState(TypedDict, total=False):
    request: str
    category: str
    priority: Literal["urgent", "routine"]
    route: str
    draft: str
    needs_human_review: bool
    trace: list[str]


def _record(state: SupportState, step: str, **updates: object) -> SupportState:
    """Return only changed fields, as LangGraph nodes should."""
    return {"trace": [*state.get("trace", []), step], **updates}


def classify_request(state: SupportState) -> SupportState:
    text = state["request"].casefold()
    if any(word in text for word in ("charged twice", "fraud", "locked out", "outage")):
        category, priority = "account_or_billing", "urgent"
    elif any(word in text for word in ("how do i", "where can i", "question")):
        category, priority = "how_to", "routine"
    else:
        category, priority = "general", "routine"
    return _record(state, "classify", category=category, priority=priority)


def choose_route(state: SupportState) -> SupportState:
    route = "urgent_queue" if state["priority"] == "urgent" else "self_service"
    return _record(state, "route", route=route)


def draft_urgent_response(state: SupportState) -> SupportState:
    draft = (
        "I’m sorry this is happening. I’ve flagged your request for priority "
        "support. Please do not share passwords or full payment details here."
    )
    return _record(state, "urgent_draft", draft=draft, needs_human_review=True)


def draft_routine_response(state: SupportState) -> SupportState:
    draft = (
        "Thanks for your question. A support specialist can point you to the "
        "right instructions; please include the product area you mean."
    )
    return _record(state, "routine_draft", draft=draft, needs_human_review=False)


def route_request(state: SupportState) -> Literal["urgent", "routine"]:
    """Conditional edge: select a path using state produced by prior nodes."""
    return "urgent" if state["route"] == "urgent_queue" else "routine"


def build_workflow():
    builder = StateGraph(SupportState)
    builder.add_node("classify", classify_request)
    builder.add_node("choose_route", choose_route)
    builder.add_node("urgent_draft", draft_urgent_response)
    builder.add_node("routine_draft", draft_routine_response)

    builder.add_edge(START, "classify")
    builder.add_edge("classify", "choose_route")
    builder.add_conditional_edges(
        "choose_route",
        route_request,
        {"urgent": "urgent_draft", "routine": "routine_draft"},
    )
    builder.add_edge("urgent_draft", END)
    builder.add_edge("routine_draft", END)
    return builder.compile()


def run_examples() -> None:
    app = build_workflow()
    examples = (
        "I was charged twice and need help.",
        "How do I update my delivery address?",
    )
    for request in examples:
        result = app.invoke({"request": request, "trace": []})
        print(f"Request: {request}")
        print(f"Category: {result['category']} | priority: {result['priority']}")
        print(f"Route: {result['route']} | human review: {result['needs_human_review']}")
        print(f"Trace: {' -> '.join(result['trace'])}")
        print(f"Draft: {result['draft']}\n")

    urgent = app.invoke({"request": "Possible fraud on my account", "trace": []})
    routine = app.invoke({"request": "Where can I find my invoices?", "trace": []})
    assert urgent["route"] == "urgent_queue" and urgent["needs_human_review"]
    assert routine["route"] == "self_service" and not routine["needs_human_review"]
    print("Workflow checks passed.")


if __name__ == "__main__":
    run_examples()
