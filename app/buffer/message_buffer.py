"""Message buffer to handle WhatsApp race conditions.

When Kommo/WhatsApp sends media + text as separate webhooks milliseconds apart,
this buffer accumulates messages from the same contact for a configurable window
(default 3s) before processing them as a single combined message.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from app.config import settings


@dataclass
class BufferedContact:
    messages: list[str] = field(default_factory=list)
    timer: asyncio.Task | None = None


class MessageBuffer:
    def __init__(self, delay: float | None = None):
        self._delay = delay or settings.message_buffer_seconds
        self._contacts: dict[str, BufferedContact] = {}
        self._callback: Callable[[str, str], Awaitable[None]] | None = None

    def set_callback(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        """Set the function to call when buffer expires.

        callback(contact_id, combined_message)
        """
        self._callback = callback

    async def add_message(self, contact_id: str, text: str) -> None:
        """Add a message to the buffer for a contact.

        If a timer is already running for this contact, it resets.
        When the timer expires, all accumulated messages are combined
        and passed to the callback.
        """
        if contact_id not in self._contacts:
            self._contacts[contact_id] = BufferedContact()

        entry = self._contacts[contact_id]
        entry.messages.append(text)

        # Cancel existing timer and start a new one
        if entry.timer is not None and not entry.timer.done():
            entry.timer.cancel()

        entry.timer = asyncio.create_task(self._flush_after_delay(contact_id))

    async def _flush_after_delay(self, contact_id: str) -> None:
        """Wait for the buffer delay, then flush all messages for the contact."""
        await asyncio.sleep(self._delay)
        await self._flush(contact_id)

    async def _flush(self, contact_id: str) -> None:
        """Combine buffered messages and invoke the callback."""
        entry = self._contacts.pop(contact_id, None)
        if entry is None or not entry.messages:
            return

        combined = "\n".join(entry.messages)

        if self._callback:
            await self._callback(contact_id, combined)

    async def flush_all(self) -> None:
        """Force-flush all pending buffers (for graceful shutdown)."""
        contact_ids = list(self._contacts.keys())
        for contact_id in contact_ids:
            entry = self._contacts.get(contact_id)
            if entry and entry.timer and not entry.timer.done():
                entry.timer.cancel()
            await self._flush(contact_id)
