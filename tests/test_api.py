"""Tests for FastAPI webhook endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked dependencies."""
    import app.main as main_module

    with patch.object(main_module, "get_checkpointer") as mock_cp, \
         patch.object(main_module, "build_main_graph") as mock_build:

        # Mock checkpointer
        mock_checkpointer = AsyncMock()
        mock_cp.return_value = mock_checkpointer

        # Mock graph
        mock_compiled = AsyncMock()
        mock_compiled.ainvoke.return_value = {
            "bot_response": "Hola, ¿en qué puedo ayudarte?",
            "messages": [],
        }
        mock_build.return_value.compile.return_value = mock_compiled

        with TestClient(main_module.app) as c:
            yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_message_buffers(client):
    """Messages should be buffered (returns immediately)."""
    response = client.post("/webhook/message", json={
        "contact_id": "12345",
        "message_text": "Hola",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "buffered"


def test_webhook_sync_returns_response(client):
    """Sync endpoint should return the bot response directly."""
    response = client.post("/webhook/message/sync", json={
        "contact_id": "12345",
        "contact_name": "Juan",
        "message_text": "Hola, quiero información del diplomado",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Hola" in data["response"]


def test_webhook_invalid_payload(client):
    """Missing required fields should return 422."""
    response = client.post("/webhook/message", json={
        "contact_name": "Juan",
        # Missing contact_id and message_text
    })
    assert response.status_code == 422
