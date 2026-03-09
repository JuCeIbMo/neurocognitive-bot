"""Lead sub-graph nodes.

Each node represents a conversation phase. It:
1. Composes the 4-layer prompt for the current phase
2. Calls the LLM with conversation history
3. Returns the bot response + any state updates
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage

from app.config import settings
from app.models.state import ConversationState
from app.prompts.composer import compose_system_prompt
from app.graph.lead.transitions import extract_flags, determine_next_phase
from app.tools.notify_advisor import notify_advisor
from app.tools.send_payment import send_payment_link


async def _lead_phase_node(state: ConversationState, phase: str) -> dict:
    """Generic handler for any lead phase — composes prompt, calls LLM, extracts flags."""
    system_prompt = await compose_system_prompt("lead", phase)

    llm = ChatOpenAI(model=settings.main_model, temperature=0.7)
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    response = await llm.ainvoke(messages)

    # Extract flags from the updated conversation (including the new response)
    state_with_response = {**state, "messages": list(state["messages"]) + [response]}
    flag_updates = await extract_flags(state_with_response)

    # Determine next phase based on updated flags
    merged_state = {**state, **flag_updates}
    next_phase = determine_next_phase(merged_state)

    return {
        "messages": [response],
        "bot_response": response.content,
        "phase": next_phase,
        **flag_updates,
    }


async def discovery_node(state: ConversationState) -> dict:
    return await _lead_phase_node(state, "discovery")


async def pain_node(state: ConversationState) -> dict:
    return await _lead_phase_node(state, "pain")


async def gap_node(state: ConversationState) -> dict:
    return await _lead_phase_node(state, "gap")


async def solution_node(state: ConversationState) -> dict:
    return await _lead_phase_node(state, "solution")


async def closing_node(state: ConversationState) -> dict:
    """Closing phase — may trigger tool calls for payment link and advisor notification."""
    result = await _lead_phase_node(state, "closing")

    # If interest is expressed and we haven't sent payment yet, trigger tools
    if result.get("interest_expressed") and not state.get("payment_link_sent"):
        contact_id = state["contact_id"]
        contact_name = state.get("contact_name", "")

        await send_payment_link.ainvoke({
            "contact_id": contact_id,
            "program": "diplomado",
            "contact_name": contact_name,
        })
        await notify_advisor.ainvoke({
            "contact_id": contact_id,
            "contact_name": contact_name,
            "user_type": "lead",
            "context": "Lead listo para inscripción. Se envió link de pago.",
        })
        result["payment_link_sent"] = True

    return result


async def followup_node(state: ConversationState) -> dict:
    return await _lead_phase_node(state, "followup")


async def redirect_node(state: ConversationState) -> dict:
    """Redirect to Curso de Fundamentos (30h) for ineligible leads."""
    return await _lead_phase_node(state, "redirect")
