from supabase import create_client, Client

from app.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


async def get_contact(contact_id: str) -> dict | None:
    """Fetch a contact by kommo_contact_id. Returns None if not found."""
    client = get_supabase()
    result = (
        client.table("contacts")
        .select("*")
        .eq("kommo_contact_id", contact_id)
        .maybe_single()
        .execute()
    )
    if result is None:
        return None
    return result.data


async def upsert_contact(contact_data: dict) -> dict:
    """Create or update a contact record."""
    client = get_supabase()
    result = (
        client.table("contacts")
        .upsert(contact_data, on_conflict="kommo_contact_id")
        .execute()
    )
    return result.data[0]


async def get_knowledge_sections(
    user_type: str, phase: str
) -> list[dict]:
    """Load knowledge sections applicable to a user type and phase."""
    client = get_supabase()
    result = (
        client.table("knowledge_sections")
        .select("section_key, content")
        .contains("applicable_user_types", [user_type])
        .contains("applicable_phases", [phase])
        .execute()
    )
    return result.data


async def get_active_corrections(
    user_type: str | None = None, phase: str | None = None
) -> list[dict]:
    """Load active behavioral corrections, optionally filtered."""
    client = get_supabase()
    query = client.table("corrections").select("*").eq("active", True)
    if user_type:
        query = query.or_(
            f"applicable_user_type.eq.{user_type},applicable_user_type.is.null"
        )
    if phase:
        query = query.or_(
            f"applicable_phase.eq.{phase},applicable_phase.is.null"
        )
    result = query.execute()
    return result.data
