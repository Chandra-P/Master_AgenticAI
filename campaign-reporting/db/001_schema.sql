-- Explicit local provisioning only. Run as the database owner; never from app imports.
BEGIN;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE TABLE IF NOT EXISTS report_runs (
 run_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, campaign_id TEXT NOT NULL,
 identity_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK (status IN ('computed','review','approved','rejected','delivered')),
 version INTEGER NOT NULL CHECK (version > 0), data TEXT NOT NULL,
 UNIQUE(client_id,campaign_id,version)
);
CREATE TABLE IF NOT EXISTS audit_events (
 event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES report_runs(run_id),
 client_id TEXT NOT NULL, action TEXT NOT NULL, actor_id TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS campaign_configs (
 config_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, campaign_id TEXT NOT NULL,
 confirmed_by TEXT NOT NULL, confirmed_at TEXT NOT NULL, data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_snapshots (
 snapshot_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, campaign_id TEXT NOT NULL,
 coverage_end DATE NOT NULL, ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 content_hash TEXT NOT NULL, payload JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS mart_account_outcomes (
 snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
 client_id TEXT NOT NULL, campaign_id TEXT NOT NULL, account_id TEXT NOT NULL,
 member_ids TEXT[] NOT NULL, product_type TEXT NOT NULL, account_open_date DATE NOT NULL,
 observed_on DATE NOT NULL, dm_mailings INTEGER[] NOT NULL DEFAULT '{}',
 digital_matched BOOLEAN NOT NULL, new_member_ids TEXT[] NOT NULL DEFAULT '{}',
 branch TEXT NOT NULL, zip_code TEXT NOT NULL, opening_balance NUMERIC(18,2),
 PRIMARY KEY(snapshot_id,client_id,account_id)
);
CREATE TABLE IF NOT EXISTS service_bindings (
 login_name NAME PRIMARY KEY, client_id TEXT NOT NULL, service_role TEXT NOT NULL
 CHECK (service_role IN ('ingestion','compute','narrative','review','delivery'))
);
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
COMMIT;
