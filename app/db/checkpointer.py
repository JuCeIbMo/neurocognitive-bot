from contextlib import asynccontextmanager
from typing import AsyncGenerator

from psycopg import AsyncConnection
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings


@asynccontextmanager
async def get_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """Create and initialize the LangGraph PostgreSQL checkpointer.

    This persists graph state (messages, flags, phase) across conversation turns.
    Uses the Supabase PostgreSQL connection directly.

    prepare_threshold=0 disables prepared statements, required for
    Supabase's PgBouncer (transaction pooling mode).
    """
    conn = await AsyncConnection.connect(
        settings.supabase_db_url,
        autocommit=True,
        prepare_threshold=None,
    )
    checkpointer = AsyncPostgresSaver(conn)
    try:
        await checkpointer.setup()
        yield checkpointer
    finally:
        await conn.close()
