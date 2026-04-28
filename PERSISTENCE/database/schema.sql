-- ==========================================
-- NAYA SUPREME V19 — DATABASE SCHEMA
-- PostgreSQL 15+  |  UTF-8
-- ==========================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- PROSPECTS
-- ==========================================
CREATE TABLE IF NOT EXISTS prospects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_name   TEXT NOT NULL,
    contact_name    TEXT,
    email           TEXT,
    phone           TEXT,
    linkedin_url    TEXT,
    website         TEXT,
    industry        TEXT,
    country         TEXT DEFAULT 'FR',
    pain_score      NUMERIC(4,2) DEFAULT 0,
    revenue_potential NUMERIC(12,2) DEFAULT 0,
    status          TEXT DEFAULT 'new',         -- new | contacted | qualified | deal | closed | lost
    source          TEXT DEFAULT 'hunt',
    raw_data        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status);
CREATE INDEX IF NOT EXISTS idx_prospects_pain_score ON prospects(pain_score DESC);
CREATE INDEX IF NOT EXISTS idx_prospects_created ON prospects(created_at DESC);

-- ==========================================
-- DEALS / PIPELINE
-- ==========================================
CREATE TABLE IF NOT EXISTS deals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prospect_id     UUID REFERENCES prospects(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    amount_eur      NUMERIC(12,2) NOT NULL DEFAULT 0,
    stage           TEXT DEFAULT 'discovery',   -- discovery | proposal | negotiation | contract | won | lost
    probability     NUMERIC(5,2) DEFAULT 0,
    project_type    TEXT,                        -- cash_rapide | mega_project | botanica | tiny_house | marches_oublies
    offer_text      TEXT,
    contract_url    TEXT,
    payment_link    TEXT,
    closed_at       TIMESTAMPTZ,
    notes           TEXT,
    raw_data        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage);
CREATE INDEX IF NOT EXISTS idx_deals_amount ON deals(amount_eur DESC);
CREATE INDEX IF NOT EXISTS idx_deals_created ON deals(created_at DESC);

-- ==========================================
-- OUTREACH SEQUENCES
-- ==========================================
CREATE TABLE IF NOT EXISTS outreach_sequences (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prospect_id     UUID REFERENCES prospects(id) ON DELETE CASCADE,
    deal_id         UUID REFERENCES deals(id) ON DELETE SET NULL,
    channel         TEXT DEFAULT 'email',       -- email | linkedin | whatsapp | telegram
    step            INTEGER DEFAULT 1,
    status          TEXT DEFAULT 'pending',     -- pending | sent | replied | bounced | opted_out
    subject         TEXT,
    body            TEXT,
    sent_at         TIMESTAMPTZ,
    reply_at        TIMESTAMPTZ,
    reply_text      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_outreach_prospect ON outreach_sequences(prospect_id);
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_sequences(status);

-- ==========================================
-- PAYMENTS
-- ==========================================
CREATE TABLE IF NOT EXISTS payments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id         UUID REFERENCES deals(id) ON DELETE SET NULL,
    amount_eur      NUMERIC(12,2) NOT NULL,
    currency        TEXT DEFAULT 'EUR',
    provider        TEXT,                       -- stripe | paypal | bank_transfer | crypto
    provider_ref    TEXT,
    status          TEXT DEFAULT 'pending',     -- pending | processing | completed | failed | refunded
    paid_at         TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_deal ON payments(deal_id);

-- ==========================================
-- REVENUE METRICS (daily snapshots)
-- ==========================================
CREATE TABLE IF NOT EXISTS revenue_metrics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date            DATE NOT NULL DEFAULT CURRENT_DATE,
    total_revenue   NUMERIC(12,2) DEFAULT 0,
    deals_won       INTEGER DEFAULT 0,
    deals_lost      INTEGER DEFAULT 0,
    prospects_new   INTEGER DEFAULT 0,
    emails_sent     INTEGER DEFAULT 0,
    conversion_rate NUMERIC(5,2) DEFAULT 0,
    avg_deal_size   NUMERIC(10,2) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (date)
);

-- ==========================================
-- AI / LLM USAGE LOG
-- ==========================================
CREATE TABLE IF NOT EXISTS llm_usage_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider        TEXT NOT NULL,
    model           TEXT,
    task_type       TEXT,
    tokens_used     INTEGER DEFAULT 0,
    latency_ms      NUMERIC(8,1),
    cached          BOOLEAN DEFAULT FALSE,
    success         BOOLEAN DEFAULT TRUE,
    error_msg       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_llm_provider ON llm_usage_log(provider);
CREATE INDEX IF NOT EXISTS idx_llm_created ON llm_usage_log(created_at DESC);

-- ==========================================
-- SYSTEM EVENTS / AUDIT LOG
-- ==========================================
CREATE TABLE IF NOT EXISTS system_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type      TEXT NOT NULL,
    source_module   TEXT,
    severity        TEXT DEFAULT 'info',        -- debug | info | warning | error | critical
    message         TEXT,
    payload         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_events_type ON system_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_severity ON system_events(severity);
CREATE INDEX IF NOT EXISTS idx_events_created ON system_events(created_at DESC);

-- ==========================================
-- CONTENT / PUBLICATIONS
-- ==========================================
CREATE TABLE IF NOT EXISTS content_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel         TEXT NOT NULL,              -- linkedin | instagram | tiktok | blog
    title           TEXT,
    body            TEXT NOT NULL,
    hashtags        TEXT[],
    status          TEXT DEFAULT 'draft',       -- draft | scheduled | published | archived
    published_at    TIMESTAMPTZ,
    engagement      JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- SCHEDULER TASKS
-- ==========================================
CREATE TABLE IF NOT EXISTS scheduler_tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_name       TEXT NOT NULL,
    module          TEXT,
    cron_expr       TEXT,
    next_run        TIMESTAMPTZ,
    last_run        TIMESTAMPTZ,
    last_status     TEXT DEFAULT 'pending',
    run_count       INTEGER DEFAULT 0,
    error_count     INTEGER DEFAULT 0,
    enabled         BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TELEGRAM NOTIFICATIONS LOG
-- ==========================================
CREATE TABLE IF NOT EXISTS telegram_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id         TEXT,
    message         TEXT NOT NULL,
    status          TEXT DEFAULT 'sent',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- UPDATE TRIGGER (updated_at)
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['prospects', 'deals']
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger
            WHERE tgname = 'trigger_' || t || '_updated_at'
        ) THEN
            EXECUTE format(
                'CREATE TRIGGER trigger_%s_updated_at BEFORE UPDATE ON %s FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
                t, t
            );
        END IF;
    END LOOP;
END;
$$;
