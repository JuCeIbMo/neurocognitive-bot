from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings


async def get_checkpointer() -> AsyncPostgresSaver:
    """Create and initialize the LangGraph PostgreSQL checkpointer.

    This persists graph state (messages, flags, phase) across conversation turns.
    Uses the Supabase PostgreSQL connection directly.
    """
    checkpointer = AsyncPostgresSaver.from_conn_string(settings.supabase_db_url)
    await checkpointer.setup()
    return checkpointer
