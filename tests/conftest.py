import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set minimal env vars so Settings can load in tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("WEBHOOK_NOTIFY_ADVISOR_URL", "https://test.webhook/notify")
    monkeypatch.setenv("WEBHOOK_SEND_FILE_URL", "https://test.webhook/file")
    monkeypatch.setenv("WEBHOOK_SEND_PAYMENT_URL", "https://test.webhook/payment")
    # Clear cached settings so env vars take effect
    get_settings.cache_clear()
