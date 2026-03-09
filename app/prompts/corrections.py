"""Loads active behavioral corrections from the database.

Corrections are "patches" on the base narrative — they override specific behaviors
without touching the narrative itself. Example: "NUNCA uses la palabra 'requisito'
cuando hables con leads no elegibles."
"""

from app.db.supabase_client import get_active_corrections


async def load_corrections(user_type: str, phase: str) -> str:
    """Load and format active corrections as a prompt section.

    Returns an empty string if no corrections are active.
    """
    corrections = await get_active_corrections(user_type, phase)
    if not corrections:
        return ""

    lines = ["CORRECCIONES ACTIVAS (estas reglas tienen prioridad sobre todo lo anterior):"]
    for c in corrections:
        lines.append(f"- Situación: {c['situation']}")
        lines.append(f"  Comportamiento correcto: {c['correct_behavior']}")

    return "\n".join(lines)
