"""Student sub-graph.

Simple flow: identify_issue → provide_info → escalate_if_needed
Students mostly need quick answers. If the bot can't help, it escalates.
"""

from langgraph.graph import StateGraph, END

from app.models.state import ConversationState
from app.graph.student.nodes import (
    identify_issue_node,
    provide_info_node,
    escalate_node,
)


def _route_by_phase(state: ConversationState) -> str:
    phase = state.get("phase", "identify_issue")
    if phase in ("identify_issue", "provide_info", "escalate"):
        return phase
    return "provide_info"


def build_student_graph() -> StateGraph:
    builder = StateGraph(ConversationState)

    builder.add_node("identify_issue", identify_issue_node)
    builder.add_node("provide_info", provide_info_node)
    builder.add_node("escalate", escalate_node)

    builder.set_conditional_entry_point(_route_by_phase, {
        "identify_issue": "identify_issue",
        "provide_info": "provide_info",
        "escalate": "escalate",
    })

    # Each node processes one turn then ends
    for node_name in ["identify_issue", "provide_info", "escalate"]:
        builder.add_edge(node_name, END)

    return builder
