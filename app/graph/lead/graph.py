"""Lead sub-graph.

State machine for lead conversations with deterministic transitions:
discovery → pain → gap → solution → closing → followup
         └→ redirect (if not eligible)
"""

from langgraph.graph import StateGraph, END

from app.models.state import ConversationState
from app.graph.lead.nodes import (
    discovery_node,
    pain_node,
    gap_node,
    solution_node,
    closing_node,
    followup_node,
    redirect_node,
)


def _route_by_phase(state: ConversationState) -> str:
    """Route to the correct node based on the current phase.

    This is called at the ENTRY of the sub-graph to direct to the right phase node.
    After each node runs, the phase may be updated, and the graph ends
    (the next invocation will re-enter at the new phase).
    """
    phase = state.get("phase", "discovery")
    if phase == "done":
        return END
    return phase


def build_lead_graph() -> StateGraph:
    builder = StateGraph(ConversationState)

    # Add all phase nodes
    builder.add_node("discovery", discovery_node)
    builder.add_node("pain", pain_node)
    builder.add_node("gap", gap_node)
    builder.add_node("solution", solution_node)
    builder.add_node("closing", closing_node)
    builder.add_node("followup", followup_node)
    builder.add_node("redirect", redirect_node)

    # Entry: route to current phase
    builder.set_conditional_entry_point(_route_by_phase, {
        "discovery": "discovery",
        "pain": "pain",
        "gap": "gap",
        "solution": "solution",
        "closing": "closing",
        "followup": "followup",
        "redirect": "redirect",
    })

    # Each node ends the sub-graph after one turn (next message re-enters)
    for node_name in ["discovery", "pain", "gap", "solution", "closing", "followup", "redirect"]:
        builder.add_edge(node_name, END)

    return builder
