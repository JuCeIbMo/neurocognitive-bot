"""Prompt composer — assembles the 4-layer prompt for each LLM call.

Layer 1: Narrative base (personality)
Layer 2: Phase instructions (current goal)
Layer 3: Knowledge section (factual data)
Layer 4: Corrections (behavioral patches)
"""

from app.prompts.narratives import (
    LEAD_NARRATIVE,
    STUDENT_NARRATIVE,
    PATIENT_NARRATIVE,
    UNKNOWN_NARRATIVE,
)
from app.prompts.phases import (
    LEAD_DISCOVERY, LEAD_PAIN, LEAD_GAP, LEAD_SOLUTION,
    LEAD_CLOSING, LEAD_FOLLOWUP, LEAD_REDIRECT,
    STUDENT_IDENTIFY_ISSUE, STUDENT_PROVIDE_INFO, STUDENT_ESCALATE,
    PATIENT_EMPATHIZE, PATIENT_PRESENT_CLINIC, PATIENT_COLLECT_INFO,
    PATIENT_NOTIFY_STAFF,
)
from app.knowledge.loader import load_knowledge
from app.prompts.corrections import load_corrections


_NARRATIVES = {
    "lead": LEAD_NARRATIVE,
    "student": STUDENT_NARRATIVE,
    "patient": PATIENT_NARRATIVE,
    "unknown": UNKNOWN_NARRATIVE,
}

_PHASE_INSTRUCTIONS = {
    "discovery": LEAD_DISCOVERY,
    "pain": LEAD_PAIN,
    "gap": LEAD_GAP,
    "solution": LEAD_SOLUTION,
    "closing": LEAD_CLOSING,
    "followup": LEAD_FOLLOWUP,
    "redirect": LEAD_REDIRECT,
    "identify_issue": STUDENT_IDENTIFY_ISSUE,
    "provide_info": STUDENT_PROVIDE_INFO,
    "escalate": STUDENT_ESCALATE,
    "empathize": PATIENT_EMPATHIZE,
    "present_clinic": PATIENT_PRESENT_CLINIC,
    "collect_info": PATIENT_COLLECT_INFO,
    "notify_staff": PATIENT_NOTIFY_STAFF,
}


async def compose_system_prompt(user_type: str, phase: str) -> str:
    """Assemble the full system prompt from all 4 layers.

    Returns a single string ready to use as the system message.
    """
    parts = []

    # Layer 1: Narrative
    narrative = _NARRATIVES.get(user_type, UNKNOWN_NARRATIVE)
    parts.append(narrative)

    # Layer 2: Phase instructions
    phase_instructions = _PHASE_INSTRUCTIONS.get(phase)
    if phase_instructions:
        parts.append(phase_instructions)

    # Layer 3: Knowledge (from Supabase)
    knowledge = await load_knowledge(user_type, phase)
    if knowledge:
        parts.append(knowledge)

    # Layer 4: Corrections (from Supabase)
    corrections = await load_corrections(user_type, phase)
    if corrections:
        parts.append(corrections)

    return "\n\n".join(parts)
