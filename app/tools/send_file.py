"""Tool to send a file (study plan, brochure) via n8n webhook."""

import httpx
from langchain_core.tools import tool

from app.config import settings


@tool
async def send_file(contact_id: str, file_type: str) -> str:
    """Send a document to the contact via WhatsApp.

    Use when a lead asks for the study plan, syllabus, or program brochure.

    Args:
        contact_id: Kommo contact ID
        file_type: Type of file to send (e.g. "plan_estudios", "brochure", "syllabus")
    """
    if not settings.webhook_send_file_url or "example.com" in settings.webhook_send_file_url:
        return "Error: webhook de archivos no configurado. El archivo deberá enviarse manualmente."
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                settings.webhook_send_file_url,
                json={
                    "contact_id": contact_id,
                    "file_type": file_type,
                },
            )
            response.raise_for_status()
        return f"Archivo '{file_type}' enviado al contacto"
    except Exception as e:
        return f"Error al enviar archivo: {e}. Deberá enviarse manualmente."
