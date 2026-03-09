"""Langfuse integration for observability.

Provides a callback handler that traces every LLM call, tool execution,
and graph transition for debugging and quality monitoring.

Uses Langfuse v3 API: credentials are set once on the global client,
and CallbackHandler receives only per-request trace context.
"""

import uuid

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from app.config import settings

_langfuse_client: Langfuse | None = None


def _get_client() -> Langfuse | None:
    """Initialize the global Langfuse client once."""
    global _langfuse_client
    if not settings.langfuse_secret_key:
        return None
    if _langfuse_client is None:
        _langfuse_client = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_base_url or None,
        )
    return _langfuse_client


def get_langfuse_handler(
    session_id: str,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> CallbackHandler | None:
    """Create a Langfuse callback handler for a conversation turn.

    Returns None if Langfuse is not configured.
    """
    if not _get_client():
        return None

    # Langfuse requires a 32-char hex UUID as trace_id.
    # We derive a deterministic UUID from the session_id so traces are consistent.
    trace_id = uuid.uuid5(uuid.NAMESPACE_DNS, session_id).hex

    return CallbackHandler(
        trace_context={
            "trace_id": trace_id,
        }
    )
