from pydantic import BaseModel


class IncomingMessage(BaseModel):
    """Payload that n8n forwards from Kommo webhook."""

    contact_id: str
    contact_name: str | None = None
    message_text: str
    message_type: str = "text"  # text, image, audio, document
    media_url: str | None = None
