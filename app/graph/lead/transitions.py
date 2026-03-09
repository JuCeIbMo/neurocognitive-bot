"""Deterministic transition logic for lead conversations.

The LLM converses freely within a phase but NEVER decides when to transition.
After each LLM response, we extract structured data (flags) from the conversation
and apply deterministic rules to decide if the phase should advance.
"""

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.state import ConversationState

# Eligible professions for the diplomado
ELIGIBLE_PROFESSIONS = {
    "fisioterapeuta", "kinesiólogo", "kinesióloga", "terapeuta ocupacional",
    "terapeuta físico", "terapeuta fisica", "médico rehabilitador",
    "medico rehabilitador", "fisiatra", "licenciado en fisioterapia",
    "licenciado en kinesiología", "licenciada en fisioterapia",
    "licenciada en kinesiología", "licenciado en terapia física",
    "licenciada en terapia física", "licenciado en terapia ocupacional",
    "licenciada en terapia ocupacional",
}

# Professions that are NOT eligible (redirect to curso 30h)
INELIGIBLE_PROFESSIONS = {
    "entrenador personal", "coach deportivo", "nutriólogo", "nutrióloga",
    "nutricionista", "psicólogo", "psicóloga", "masajista", "quiropráctico",
    "quiropráctica", "preparador físico", "instructor de yoga",
    "instructor de pilates", "coach", "educador físico",
}


class ExtractedFlags(BaseModel):
    """Structured data extracted from the conversation after each LLM turn."""

    profession: str | None = Field(
        None,
        description="The user's profession if mentioned (e.g. 'fisioterapeuta', 'entrenador personal'). Null if not mentioned yet.",
    )
    has_experience: bool | None = Field(
        None,
        description="Whether the user mentioned having clinical experience or currently practicing. Null if not discussed.",
    )
    is_student_last_year: bool | None = Field(
        None,
        description="Whether the user mentioned being a last-year student of an eligible career. Null if not discussed.",
    )
    frustration_articulated: bool = Field(
        False,
        description="Whether the user has expressed a specific frustration or 'ceiling' with their patients.",
    )
    gap_acknowledged: bool = Field(
        False,
        description="Whether the user acknowledged the gap between their current situation and where they want to be.",
    )
    interest_expressed: bool = Field(
        False,
        description="Whether the user has expressed explicit interest in enrolling (e.g. 'me interesa', 'quiero inscribirme', 'envíame el link').",
    )


EXTRACTION_PROMPT = """Analiza la conversación y extrae la información disponible.
Solo marca como verdadero lo que el usuario haya dicho EXPLÍCITAMENTE.
No infieras ni asumas — si no se mencionó, déjalo como null o false."""


async def extract_flags(state: ConversationState) -> dict:
    """Extract structured flags from the conversation using LLM."""
    messages = state.get("messages", [])
    if not messages:
        return {}

    # Get recent conversation for context
    recent = messages[-6:]  # Last 3 exchanges
    conversation_text = "\n".join(
        f"{'Usuario' if msg.type == 'human' else 'Bot'}: {msg.content}"
        for msg in recent
        if hasattr(msg, "content")
    )

    llm = ChatOpenAI(model=settings.fast_model, temperature=0)
    extractor = llm.with_structured_output(ExtractedFlags)

    flags = await extractor.ainvoke([
        SystemMessage(content=EXTRACTION_PROMPT),
        HumanMessage(content=f"Conversación:\n{conversation_text}"),
    ])

    return _flags_to_state_update(flags, state)


def _flags_to_state_update(flags: ExtractedFlags, state: ConversationState) -> dict:
    """Convert extracted flags to a state update dict."""
    update: dict = {}

    if flags.profession:
        update["profession"] = flags.profession
        eligible = _check_eligibility(flags.profession, flags.is_student_last_year)
        update["is_eligible"] = eligible

    if flags.has_experience is not None:
        update["experience"] = "practicing" if flags.has_experience else "not_practicing"

    if flags.frustration_articulated:
        update["frustration_articulated"] = True

    if flags.gap_acknowledged:
        update["gap_acknowledged"] = True

    if flags.interest_expressed:
        update["interest_expressed"] = True

    return update


def _check_eligibility(profession: str, is_student_last_year: bool | None) -> bool:
    """Determine if a profession is eligible for the diplomado."""
    profession_lower = profession.lower().strip()

    # Check direct match
    if profession_lower in ELIGIBLE_PROFESSIONS:
        return True

    # Check if it's a known ineligible profession
    if profession_lower in INELIGIBLE_PROFESSIONS:
        return False

    # Check partial matches for eligible
    eligible_keywords = ["fisioterapi", "kinesiolog", "terapia ocupacional", "terapia física", "rehabilitaci"]
    if any(kw in profession_lower for kw in eligible_keywords):
        return True

    # Student of last year of eligible career
    if is_student_last_year:
        return True

    # Unknown profession — default to not eligible to be safe
    # (will redirect to curso 30h, which is better than enrolling someone ineligible)
    return False


def determine_next_phase(state: ConversationState) -> str:
    """Deterministic phase transition logic.

    Returns the next phase based on current phase and collected flags.
    Returns the current phase if no transition should happen.
    """
    phase = state.get("phase", "discovery")

    match phase:
        case "discovery":
            profession = state.get("profession")
            experience = state.get("experience")
            is_eligible = state.get("is_eligible")

            if profession and is_eligible is False:
                return "redirect"
            if profession and experience and is_eligible:
                return "pain"
            return "discovery"

        case "pain":
            if state.get("frustration_articulated"):
                return "gap"
            return "pain"

        case "gap":
            if state.get("gap_acknowledged"):
                return "solution"
            return "gap"

        case "solution":
            if state.get("interest_expressed"):
                return "closing"
            return "solution"

        case "closing":
            if state.get("payment_link_sent"):
                return "done"
            return "closing"

        case _:
            return phase
