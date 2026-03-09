"""Langfuse integration for observability.

Provides a callback handler that traces every LLM call, tool execution,
and graph transition for debugging and quality monitoring.
"""

from langfuse.langchain import CallbackHandler

from app.config import settings


def get_langfuse_handler(
    session_id: str,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> CallbackHandler | None:
    """Create a Langfuse callback handler for a conversation.

    Returns None if Langfuse is not configured.
    """
    if not settings.langfuse_secret_key:
        return None

    return CallbackHandler(
        secret_key=settings.langfuse_secret_key,
        public_key=settings.langfuse_public_key,
        host=settings.langfuse_host,
        session_id=session_id,
        user_id=user_id,
        metadata=metadata or {},
    )
