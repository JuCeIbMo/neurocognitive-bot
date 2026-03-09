"""Tool to send a payment link via n8n webhook."""

import httpx
from langchain_core.tools import tool

from app.config import settings


@tool
async def send_payment_link(
    contact_id: str, program: str, contact_name: str
) -> str:
    """Send a payment link to the contact for enrollment.

    Use when a lead in the closing phase confirms they want to enroll.

    Args:
        contact_id: Kommo contact ID
        program: Program name (e.g. "diplomado", "curso_30h", "seminario")
        contact_name: Contact's name for the payment reference
    """
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            settings.webhook_send_payment_url,
            json={
                "contact_id": contact_id,
                "program": program,
                "contact_name": contact_name,
            },
        )
        response.raise_for_status()
    return f"Link de pago para '{program}' enviado"
