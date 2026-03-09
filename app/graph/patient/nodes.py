"""Patient sub-graph nodes."""

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import ConversationState
from app.prompts.composer import compose_system_prompt
from app.tools.notify_advisor import notify_advisor


class PatientFlags(BaseModel):
    """Extracted patient information."""
    condition_described: bool = Field(
        False, description="Patient described their condition or health issue"
    )
    interested_in_clinic: bool = Field(
        False, description="Patient expressed interest in the clinic or receiving care"
    )
    name_provided: str | None = Field(
        None, description="Patient's full name if provided"
    )


PATIENT_EXTRACTION_PROMPT = """Analiza la conversación con este paciente y extrae la información disponible.
Solo marca como verdadero lo que el paciente haya dicho EXPLÍCITAMENTE."""


async def _patient_node(state: ConversationState, phase: str) -> dict:
    """Generic handler for patient phases."""
    system_prompt = await compose_system_prompt("patient", phase)

    llm = ChatOpenAI(model=settings.main_model, temperature=0.7)
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    response = await llm.ainvoke(messages)

    return {
        "messages": [response],
        "bot_response": response.content,
    }


async def _extract_patient_flags(state: ConversationState) -> dict:
    """Extract patient flags from conversation."""
    messages = state.get("messages", [])
    if not messages:
        return {}

    recent = messages[-6:]
    conversation_text = "\n".join(
        f"{'Paciente' if msg.type == 'human' else 'Bot'}: {msg.content}"
        for msg in recent if hasattr(msg, "content")
    )

    llm = ChatOpenAI(model=settings.fast_model, temperature=0)
    extractor = llm.with_structured_output(PatientFlags)

    flags = await extractor.ainvoke([
        SystemMessage(content=PATIENT_EXTRACTION_PROMPT),
        HumanMessage(content=f"Conversación:\n{conversation_text}"),
    ])

    update = {}
    if flags.condition_described:
        update["condition_described"] = True
    if flags.name_provided:
        update["contact_name"] = flags.name_provided
    return update


async def empathize_node(state: ConversationState) -> dict:
    result = await _patient_node(state, "empathize")
    flags = await _extract_patient_flags({**state, "messages": list(state["messages"]) + result["messages"]})

    next_phase = "empathize"
    if flags.get("condition_described"):
        next_phase = "present_clinic"

    result["phase"] = next_phase
    result.update(flags)
    return result


async def present_clinic_node(state: ConversationState) -> dict:
    result = await _patient_node(state, "present_clinic")
    result["clinic_presented"] = True
    result["phase"] = "collect_info"
    return result


async def collect_info_node(state: ConversationState) -> dict:
    result = await _patient_node(state, "collect_info")
    flags = await _extract_patient_flags({**state, "messages": list(state["messages"]) + result["messages"]})

    if flags.get("contact_name"):
        result["contact_name"] = flags["contact_name"]
        result["patient_info_collected"] = True
        result["phase"] = "notify_staff"
    else:
        result["phase"] = "collect_info"

    return result


async def notify_staff_node(state: ConversationState) -> dict:
    result = await _patient_node(state, "notify_staff")

    await notify_advisor.ainvoke({
        "contact_id": state["contact_id"],
        "contact_name": state.get("contact_name", ""),
        "user_type": "patient",
        "context": "Paciente interesado en atención clínica. Necesita ser contactado por el equipo médico.",
    })
    result["staff_notified"] = True
    return result
