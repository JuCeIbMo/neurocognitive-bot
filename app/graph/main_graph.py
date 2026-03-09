"""Main conversation graph.

Orchestrates: classify_user → route to sub-graph → persist contact info.
Each invocation processes ONE message turn.
"""

from langgraph.graph import StateGraph, END

from app.models.state import ConversationState
from app.graph.classifier import classify_user
from app.graph.unknown_node import unknown_node
from app.graph.lead.graph import build_lead_graph
from app.graph.student.graph import build_student_graph
from app.graph.patient.graph import build_patient_graph
from app.db.supabase_client import upsert_contact


# Build sub-graphs (compiled as sub-graph nodes)
_lead_graph = build_lead_graph().compile()
_student_graph = build_student_graph().compile()
_patient_graph = build_patient_graph().compile()


async def lead_subgraph_node(state: ConversationState) -> dict:
    """Invoke the lead sub-graph."""
    result = await _lead_graph.ainvoke(state)
    return {k: result[k] for k in result if k != "messages" or k == "messages"}


async def student_subgraph_node(state: ConversationState) -> dict:
    """Invoke the student sub-graph."""
    result = await _student_graph.ainvoke(state)
    return {k: result[k] for k in result if k != "messages" or k == "messages"}


async def patient_subgraph_node(state: ConversationState) -> dict:
    """Invoke the patient sub-graph."""
    result = await _patient_graph.ainvoke(state)
    return {k: result[k] for k in result if k != "messages" or k == "messages"}


async def persist_contact(state: ConversationState) -> dict:
    """Persist updated contact info to Supabase after processing."""
    contact_data = {
        "kommo_contact_id": state["contact_id"],
        "user_type": state.get("user_type", "unknown"),
        "name": state.get("contact_name"),
        "profession": state.get("profession"),
        "is_eligible": state.get("is_eligible"),
        "phase": state.get("phase", "initial"),
        "program": state.get("program"),
        "collected_info": {
            k: state.get(k)
            for k in [
                "experience", "frustration_articulated", "gap_acknowledged",
                "interest_expressed", "payment_link_sent",
                "condition_described", "clinic_presented",
            ]
            if state.get(k) is not None
        },
    }
    await upsert_contact(contact_data)
    return {}


def _route_user_type(state: ConversationState) -> str:
    """Route to the appropriate sub-graph based on user type."""
    user_type = state.get("user_type", "unknown")
    if user_type == "lead":
        return "lead_graph"
    elif user_type == "student":
        return "student_graph"
    elif user_type == "patient":
        return "patient_graph"
    else:
        return "unknown_handler"


def build_main_graph() -> StateGraph:
    builder = StateGraph(ConversationState)

    # Nodes
    builder.add_node("classify", classify_user)
    builder.add_node("lead_graph", lead_subgraph_node)
    builder.add_node("student_graph", student_subgraph_node)
    builder.add_node("patient_graph", patient_subgraph_node)
    builder.add_node("unknown_handler", unknown_node)
    builder.add_node("persist", persist_contact)

    # Flow: classify → route → sub-graph → persist
    builder.set_entry_point("classify")
    builder.add_conditional_edges("classify", _route_user_type, {
        "lead_graph": "lead_graph",
        "student_graph": "student_graph",
        "patient_graph": "patient_graph",
        "unknown_handler": "unknown_handler",
    })

    # All sub-graphs lead to persist
    builder.add_edge("lead_graph", "persist")
    builder.add_edge("student_graph", "persist")
    builder.add_edge("patient_graph", "persist")
    builder.add_edge("unknown_handler", "persist")
    builder.add_edge("persist", END)

    return builder
