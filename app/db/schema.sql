-- Neurocognitive Bot Database Schema
-- Run this against your Supabase PostgreSQL instance

-- Contacts: tracks each WhatsApp user across conversations
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    kommo_contact_id TEXT UNIQUE NOT NULL,
    user_type TEXT DEFAULT 'unknown',
    name TEXT,
    profession TEXT,
    is_eligible BOOLEAN,
    phase TEXT DEFAULT 'initial',
    program TEXT,
    collected_info JSONB DEFAULT '{}',
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contacts_kommo_id ON contacts(kommo_contact_id);

-- Knowledge sections: mock RAG - complete sections loaded by deterministic rules
CREATE TABLE IF NOT EXISTS knowledge_sections (
    id SERIAL PRIMARY KEY,
    section_key TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    applicable_user_types TEXT[] DEFAULT '{}',
    applicable_phases TEXT[] DEFAULT '{}',
    version INTEGER DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Corrections: behavioral patches (for future team UI, usable now by developer)
CREATE TABLE IF NOT EXISTS corrections (
    id SERIAL PRIMARY KEY,
    situation TEXT NOT NULL,
    correct_behavior TEXT NOT NULL,
    applicable_phase TEXT,
    applicable_user_type TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Note: LangGraph checkpointer tables are created automatically by AsyncPostgresSaver.setup()
