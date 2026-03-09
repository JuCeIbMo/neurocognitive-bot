"""User classifier node.

Determines if user is a lead, student, or patient by:
1. Looking up contact_id in the contacts table (known user)
2. If unknown, using LLM structured output to infer from the message
3. Defaulting to 'lead' if still unclear after 2-3 messages
"""

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.db.supabase_client import get_contact
from app.models.contact import UserType, LeadPhase, StudentPhase, PatientPhase
from app.models.state import ConversationState


class ClassificationResult(BaseModel):
    user_type: str = Field(
        description="One of: lead, student, patient, unknown. "
        "'lead' if they ask about programs/training. "
        "'student' if they mention being enrolled, platform access, classes. "
        "'patient' if they mention personal health issues, injuries, rehabilitation needs. "
        "'unknown' if not enough context."
    )
    confidence: float = Field(
        description="Confidence level 0.0 to 1.0"
    )


CLASSIFICATION_PROMPT = """Eres un clasificador de mensajes para Neurocognitive Academy.
Analiza el mensaje del usuario y determina qué tipo de persona es:

- **lead**: Profesional de salud interesado en formación/programas educativos. Pregunta por diplomados, cursos, seminarios, formación, o quiere información académica.
- **student**: Alumno ya inscrito. Menciona acceso a plataforma, módulos, clases, tareas, certificados, problemas técnicos del sistema educativo.
- **patient**: Persona con problemas de salud. Menciona dolor, lesión, accidente cerebrovascular, rehabilitación personal, parálisis, necesita atención médica.
- **unknown**: No hay suficiente contexto (ej: solo "Hola" o "Buenos días").

IMPORTANTE: Solo clasifica con la información disponible. Si solo es un saludo, responde "unknown"."""


async def classify_user(state: ConversationState) -> dict:
    """Classify the user type based on DB lookup and message analysis."""
    contact_id = state["contact_id"]

    # Step 1: Check if user exists in contacts table
    contact = await get_contact(contact_id)
    if contact and contact.get("user_type") not in (None, "unknown"):
        return {
            "user_type": contact["user_type"],
            "phase": contact.get("phase", "initial"),
            "contact_name": contact.get("name") or state.get("contact_name"),
            "profession": contact.get("profession"),
            "is_eligible": contact.get("is_eligible"),
            "program": contact.get("program"),
        }

    # Step 2: Infer from messages using LLM structured output
    messages = state.get("messages", [])
    if not messages:
        return {"user_type": "unknown"}

    # Get the last few messages for context
    recent_messages = messages[-3:]
    message_text = "\n".join(
        msg.content for msg in recent_messages if hasattr(msg, "content")
    )

    llm = ChatOpenAI(model=settings.fast_model, temperature=0)
    classifier = llm.with_structured_output(ClassificationResult)

    result = await classifier.ainvoke([
        SystemMessage(content=CLASSIFICATION_PROMPT),
        HumanMessage(content=f"Mensaje(s) del usuario:\n{message_text}"),
    ])

    user_type = result.user_type
    if user_type == "unknown" and len(messages) >= 3:
        # After 3+ messages without clarity, default to lead
        user_type = "lead"

    # Set initial phase based on user type
    phase = _get_initial_phase(user_type)

    return {"user_type": user_type, "phase": phase}


def _get_initial_phase(user_type: str) -> str:
    match user_type:
        case "lead":
            return LeadPhase.DISCOVERY
        case "student":
            return StudentPhase.IDENTIFY_ISSUE
        case "patient":
            return PatientPhase.EMPATHIZE
        case _:
            return "initial"
