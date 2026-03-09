# Neurocognitive Academy Chatbot

WhatsApp chatbot for Neurocognitive Academy. Handles 3 user types (leads, students, patients) through a single WhatsApp number via Kommo CRM.

## Stack

- **Runtime:** Python 3.12+ with uv
- **Backend:** FastAPI + uvicorn
- **Agent:** LangGraph with PostgreSQL checkpointer
- **LLM:** OpenAI API (GPT-4o / GPT-4o-mini)
- **DB:** Supabase (PostgreSQL)
- **Observability:** Langfuse (self-hosted) + Logfire
- **Deploy:** Hetzner VPS + Dokploy

## Commands

```bash
uv sync                          # Install dependencies
uv run uvicorn app.main:app --reload  # Run dev server
uv run pytest                    # Run tests
uv run pytest -x -v              # Run tests verbose, stop on first failure
```

## Project Structure

All application code lives in `app/`. Key areas:
- `app/graph/` — LangGraph state machines (main graph + 3 sub-graphs: lead, student, patient)
- `app/prompts/` — 4-layer prompt system (narrative → phase → knowledge → corrections)
- `app/tools/` — Webhook tools (notify advisor, send file, send payment link)
- `app/buffer/` — Message buffer for WhatsApp race conditions (3s accumulation)
- `app/knowledge/` — Mock RAG: loads complete knowledge sections by deterministic rules
- `app/db/` — Supabase client + LangGraph checkpointer

## Architecture Decisions

- **Deterministic transitions:** LLM converses freely within a phase but NEVER decides phase transitions. Code validates flags extracted via structured output.
- **4-layer prompts:** Narrative base (rare change) → Phase instructions (rare) → Knowledge data (frequent) → Corrections (on-bug). Each layer is independently editable.
- **Mock RAG:** Load complete knowledge sections by user_type + phase instead of embedding search. Swap for real RAG later without changing anything else.
- **Progressive migration:** n8n still receives Kommo webhooks and forwards to this FastAPI service. Tools call back to n8n webhooks.

## Code Conventions

- Python 3.12+, type hints on all function signatures
- async/await for all I/O (DB, HTTP, LLM calls)
- pydantic models for all data boundaries (webhook payloads, state, config)
- pydantic-settings for configuration via environment variables
- httpx for async HTTP calls
- All prompts in `app/prompts/`, never inline in graph nodes
- Spanish for user-facing content, English for code (variables, functions, comments)
- Tests with pytest + pytest-asyncio

## Environment Variables

See `.env.example` for all required variables. Key ones:
- `OPENAI_API_KEY` — OpenAI API key
- `SUPABASE_URL` / `SUPABASE_KEY` — Supabase connection
- `SUPABASE_DB_URL` — Direct PostgreSQL URL (for checkpointer)
- `LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_HOST` — Langfuse
- `WEBHOOK_NOTIFY_ADVISOR_URL` — n8n webhook for notifying human advisors
- `WEBHOOK_SEND_FILE_URL` — n8n webhook for sending files
- `WEBHOOK_SEND_PAYMENT_URL` — n8n webhook for sending payment links
- `SHADOW_MODE` — When true, process but don't return responses (for testing)
