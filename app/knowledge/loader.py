"""Knowledge section loader (mock RAG).

Instead of embedding-based search, loads COMPLETE sections from Supabase
based on deterministic rules: user_type + phase → relevant sections.
This is more reliable for a ~21-page doc and can be swapped for real RAG later.
"""

from app.db.supabase_client import get_knowledge_sections


async def load_knowledge(user_type: str, phase: str) -> str:
    """Load relevant knowledge sections for the current context.

    Returns formatted text ready to inject into the prompt.
    """
    sections = await get_knowledge_sections(user_type, phase)
    if not sections:
        return ""

    parts = ["INFORMACIÓN DE REFERENCIA (usa estos datos para responder con precisión):"]
    for section in sections:
        parts.append(f"\n--- {section['section_key'].upper()} ---")
        parts.append(section["content"])

    return "\n".join(parts)
