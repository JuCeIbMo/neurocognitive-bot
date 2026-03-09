"""Patient sub-graph.

Flow: empathize → present_clinic → collect_info → notify_staff
Maximum empathy throughout. Never diagnose.
"""

from langgraph.graph import StateGraph, END

from app.models.state import ConversationState
from app.graph.patient.nodes import (
    empathize_node,
    present_clinic_node,
    collect_info_node,
    notify_staff_node,
)


def _route_by_phase(state: ConversationState) -> str:
    phase = state.get("phase", "empathize")
    if phase in ("empathize", "present_clinic", "collect_info", "notify_staff"):
        return phase
    return "empathize"


def build_patient_graph() -> StateGraph:
    builder = StateGraph(ConversationState)

    builder.add_node("empathize", empathize_node)
    builder.add_node("present_clinic", present_clinic_node)
    builder.add_node("collect_info", collect_info_node)
    builder.add_node("notify_staff", notify_staff_node)

    builder.set_conditional_entry_point(_route_by_phase, {
        "empathize": "empathize",
        "present_clinic": "present_clinic",
        "collect_info": "collect_info",
        "notify_staff": "notify_staff",
    })

    for node_name in ["empathize", "present_clinic", "collect_info", "notify_staff"]:
        builder.add_edge(node_name, END)

    return builder
