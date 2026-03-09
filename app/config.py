from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    # OpenAI
    openai_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_db_url: str = ""

    # Langfuse
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = ""

    # Webhook URLs (n8n)
    webhook_notify_advisor_url: str = ""
    webhook_send_file_url: str = ""
    webhook_send_payment_url: str = ""

    # App
    shadow_mode: bool = False
    message_buffer_seconds: float = 3.0

    # LLM models
    main_model: str = "gpt-4o"
    fast_model: str = "gpt-4o-mini"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
