"""Tool to notify a human advisor via n8n webhook."""

import httpx
from langchain_core.tools import tool

from app.config import settings


@tool
async def notify_advisor(
    contact_id: str,
    contact_name: str,
    user_type: str,
    context: str,
) -> str:
    """Notify a human advisor that a contact needs attention.

    Use when:
    - A lead is ready for closing (wants to enroll)
    - A student issue cannot be resolved by the bot
    - A patient's info has been collected for the clinical team

    Args:
        contact_id: Kommo contact ID
        contact_name: Contact's name
        user_type: lead, student, or patient
        context: Brief summary of what happened and why escalation is needed
    """
    if not settings.webhook_notify_advisor_url or "example.com" in settings.webhook_notify_advisor_url:
        return "Error: webhook de asesor no configurado. La notificación deberá hacerse manualmente."
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                settings.webhook_notify_advisor_url,
                json={
                    "contact_id": contact_id,
                    "contact_name": contact_name,
                    "user_type": user_type,
                    "context": context,
                },
            )
            response.raise_for_status()
        return f"Asesor notificado para {contact_name}"
    except Exception as e:
        return f"Error al notificar asesor: {e}. La notificación deberá hacerse manualmente."
