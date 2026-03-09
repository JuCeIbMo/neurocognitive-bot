"""Tests for the message buffer (anti race-condition)."""

import asyncio
import pytest


@pytest.fixture
def buffer():
    from app.buffer.message_buffer import MessageBuffer
    return MessageBuffer(delay=0.1)  # Short delay for tests


@pytest.mark.asyncio
async def test_single_message_flushes(buffer):
    """A single message should flush after the delay."""
    results = []

    async def callback(contact_id, combined):
        results.append((contact_id, combined))

    buffer.set_callback(callback)
    await buffer.add_message("contact_1", "Hola")

    # Wait for flush
    await asyncio.sleep(0.2)

    assert len(results) == 1
    assert results[0] == ("contact_1", "Hola")


@pytest.mark.asyncio
async def test_multiple_messages_combine(buffer):
    """Multiple messages within the buffer window should be combined."""
    results = []

    async def callback(contact_id, combined):
        results.append((contact_id, combined))

    buffer.set_callback(callback)
    await buffer.add_message("contact_1", "Hola")
    await asyncio.sleep(0.05)  # Within the 0.1s window
    await buffer.add_message("contact_1", "Tengo una pregunta")

    await asyncio.sleep(0.2)

    assert len(results) == 1
    assert results[0] == ("contact_1", "Hola\nTengo una pregunta")


@pytest.mark.asyncio
async def test_different_contacts_independent(buffer):
    """Messages from different contacts should be buffered independently."""
    results = []

    async def callback(contact_id, combined):
        results.append((contact_id, combined))

    buffer.set_callback(callback)
    await buffer.add_message("contact_1", "Hola soy Juan")
    await buffer.add_message("contact_2", "Hola soy María")

    await asyncio.sleep(0.2)

    assert len(results) == 2
    contact_ids = {r[0] for r in results}
    assert contact_ids == {"contact_1", "contact_2"}


@pytest.mark.asyncio
async def test_flush_all(buffer):
    """flush_all should immediately process all pending messages."""
    results = []

    async def callback(contact_id, combined):
        results.append((contact_id, combined))

    buffer.set_callback(callback)
    await buffer.add_message("contact_1", "Pending")

    await buffer.flush_all()

    assert len(results) == 1
    assert results[0] == ("contact_1", "Pending")
