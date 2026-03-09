from contextlib import asynccontextmanager
from typing import AsyncGenerator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings


@asynccontextmanager
async def get_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """Create and initialize the LangGraph PostgreSQL checkpointer.

    This persists graph state (messages, flags, phase) across conversation turns.
    Uses the Supabase PostgreSQL connection directly.
    """
    async with AsyncPostgresSaver.from_conn_string(settings.supabase_db_url) as checkpointer:
        await checkpointer.setup()
        yield checkpointer
