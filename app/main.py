import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from langchain_core.messages import HumanMessage

from app.buffer.message_buffer import MessageBuffer
from app.config import settings
from app.db.checkpointer import get_checkpointer
from app.graph.main_graph import build_main_graph
from app.models.webhook import IncomingMessage
from app.observability.langfuse_setup import get_langfuse_handler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    checkpointer = await get_checkpointer()
    graph = build_main_graph().compile(checkpointer=checkpointer)

    app.state.graph = graph
    app.state.checkpointer = checkpointer
    app.state.buffer = MessageBuffer()

    # Wire the buffer to process messages through the graph
    async def on_buffer_flush(contact_id: str, combined_message: str):
        await _process_message(app, contact_id, combined_message)

    app.state.buffer.set_callback(on_buffer_flush)

    yield
    await app.state.buffer.flush_all()
    await checkpointer.close()


app = FastAPI(title="Neurocognitive Bot", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/message")
async def receive_message(payload: IncomingMessage):
    """Receive a message forwarded from n8n.

    The message is buffered for a few seconds to handle WhatsApp race conditions
    (media + text sent as separate webhooks). The buffer callback invokes the graph.
    """
    buffer: MessageBuffer = app.state.buffer

    text = payload.message_text
    if payload.media_url:
        text = f"[{payload.message_type}: {payload.media_url}]\n{text}" if text else f"[{payload.message_type}: {payload.media_url}]"

    await buffer.add_message(payload.contact_id, text)

    # Return immediately — processing happens when buffer flushes
    return {"status": "buffered", "contact_id": payload.contact_id}


async def _process_message(app: FastAPI, contact_id: str, message_text: str) -> None:
    """Process a buffered message through the LangGraph conversation graph."""
    graph = app.state.graph

    # Thread ID = contact_id for conversation persistence
    config = {"configurable": {"thread_id": contact_id}}

    # Add Langfuse tracing if configured
    langfuse_handler = get_langfuse_handler(
        session_id=contact_id,
        user_id=contact_id,
        metadata={"source": "webhook"},
    )
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]

    # Build initial state for this turn
    input_state = {
        "messages": [HumanMessage(content=message_text)],
        "contact_id": contact_id,
    }

    # Invoke the graph
    result = await graph.ainvoke(input_state, config)
    bot_response = result.get("bot_response", "")

    if settings.shadow_mode:
        logger.info(
            "SHADOW MODE — response NOT sent | contact=%s | response=%s",
            contact_id,
            bot_response[:200],
        )
        return

    # In production, the response is returned via the n8n webhook response
    # For now, we store it and n8n polls or we use a callback
    logger.info("Response for %s: %s", contact_id, bot_response[:200])


@app.post("/webhook/message/sync")
async def receive_message_sync(payload: IncomingMessage):
    """Synchronous endpoint — processes immediately and returns the response.

    Use this for testing or when n8n expects a synchronous reply.
    Bypasses the buffer (no race-condition protection).
    """
    graph = app.state.graph

    config = {"configurable": {"thread_id": payload.contact_id}}

    langfuse_handler = get_langfuse_handler(
        session_id=payload.contact_id,
        user_id=payload.contact_id,
    )
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]

    input_state = {
        "messages": [HumanMessage(content=payload.message_text)],
        "contact_id": payload.contact_id,
        "contact_name": payload.contact_name,
    }

    result = await graph.ainvoke(input_state, config)
    bot_response = result.get("bot_response", "")

    if settings.shadow_mode:
        return {"status": "shadow", "response": bot_response}

    return {"status": "ok", "response": bot_response}
