-- Migration 0001: initial schema (revised for wide tables + risk_scores + EEG)

-- E+/PRAHARI database schema (revised: wide tables + risk_scores + EEG Phase 2)
-- Run this against your Supabase Postgres instance (SQL Editor or psql).

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- needed for gen_random_uuid()

-- Users of the app (patients / monitored individuals) -- unchanged
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    phone_number TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    date_of_birth DATE,
    region TEXT,                       -- matches environmental_readings.region for lookup
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Devices/phones registered per user -- unchanged
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_type TEXT NOT NULL,         -- 'phone', 'wearable', 'eeg_earbud'
    device_name TEXT,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Biometric readings -- wide table: one row per sample, one column per metric.
-- Chosen over a generic metric_type/value design so the risk engine can read
-- row["heart_rate"] / row["spo2"] directly with no pivot/join, and so the
-- Supabase table view stays legible for a judge demo without an EAV pattern
-- to justify. Fixed, small, known metric set -- not a general telemetry platform.
CREATE TABLE IF NOT EXISTS biometric_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    heart_rate INT,
    spo2 FLOAT,
    skin_temp FLOAT,
    steps INT,
    recorded_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_biometric_readings_user_time
    ON biometric_readings (user_id, recorded_at DESC);

-- Environmental hazard data -- also wide, region kept from the earlier design
-- (simpler and more demo-friendly than lat/lng matching).
CREATE TABLE IF NOT EXISTS environmental_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region TEXT NOT NULL,
    temperature FLOAT,
    heat_index FLOAT,
    aqi INT,
    rainfall_mm FLOAT,
    flood_risk_level TEXT,
    source TEXT,                       -- 'IMD', 'CPCB', 'OpenAQ'
    recorded_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_env_readings_region_time
    ON environmental_readings (region, recorded_at DESC);

-- Computed risk scores -- the risk engine's output, one row per computation.
CREATE TABLE IF NOT EXISTS risk_scores (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score FLOAT NOT NULL,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
    contributing_factors JSONB,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_risk_scores_user_time
    ON risk_scores (user_id, computed_at DESC);

-- Alerts -- now tied to the risk score that triggered them.
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    risk_score_id BIGINT REFERENCES risk_scores(id) ON DELETE SET NULL,
    alert_type TEXT NOT NULL,
    channel TEXT CHECK (channel IN ('sms', 'push', 'both')),
    message TEXT NOT NULL,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    delivery_status TEXT NOT NULL DEFAULT 'pending' CHECK (delivery_status IN (
        'pending', 'sent', 'failed', 'acknowledged'
    )),
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_alerts_user_time
    ON alerts (user_id, sent_at DESC);

-- DPDP Act 2023 consent tracking -- unchanged
CREATE TABLE IF NOT EXISTS consent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data_category TEXT NOT NULL,       -- 'biometric', 'location', 'health_history'
    purpose TEXT NOT NULL,             -- 'hazard_alerting', 'model_improvement'
    consented_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ
);

-- Phase 2: EEG earbud sessions and per-window predictions.
CREATE TABLE IF NOT EXISTS eeg_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    sample_rate_hz INT
);

CREATE TABLE IF NOT EXISTS eeg_predictions (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES eeg_sessions(id) ON DELETE CASCADE,
    predicted_class TEXT CHECK (predicted_class IN
        ('healthy', 'generalized_seizure', 'focal_seizure', 'seizure_event')),
    confidence FLOAT,
    window_start_ms BIGINT,
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
