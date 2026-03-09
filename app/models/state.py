"""LangGraph conversation state shared across all sub-graphs."""

from typing import Annotated

from langgraph.graph import MessagesState
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ConversationState(MessagesState):
    """Full state for a conversation thread.

    Inherits `messages` from MessagesState (auto-appended via add_messages reducer).
    All other fields are conversation metadata tracked across turns.
    """

    # User classification
    contact_id: str
    contact_name: str | None = None
    user_type: str = "unknown"  # lead, student, patient, unknown
    phase: str = "initial"

    # Lead-specific flags (extracted via structured output after each LLM turn)
    profession: str | None = None
    experience: str | None = None
    is_eligible: bool | None = None
    frustration_articulated: bool = False
    gap_acknowledged: bool = False
    interest_expressed: bool = False
    payment_link_sent: bool = False

    # Student-specific
    program: str | None = None
    issue_identified: bool = False
    info_provided: bool = False

    # Patient-specific
    condition_described: bool = False
    clinic_presented: bool = False
    patient_info_collected: bool = False
    staff_notified: bool = False

    # Bot response (set by the active node, returned to the endpoint)
    bot_response: str = ""
