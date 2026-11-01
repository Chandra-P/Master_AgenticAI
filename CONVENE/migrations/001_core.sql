CREATE TABLE IF NOT EXISTS app_users (
 id uuid PRIMARY KEY,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS events (
 id uuid PRIMARY KEY,
 owner_id uuid NOT NULL REFERENCES app_users(id),
 active_version integer NOT NULL CHECK(active_version > 0),
 confirmed_version integer,
 status text NOT NULL DEFAULT 'planning' CHECK(status IN ('planning','archived')),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(confirmed_version IS NULL OR confirmed_version=active_version)
);
CREATE INDEX IF NOT EXISTS events_owner_idx ON events(owner_id);
CREATE TABLE IF NOT EXISTS brief_versions (
 event_id uuid NOT NULL REFERENCES events(id),
 version integer NOT NULL CHECK(version > 0),
 body jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(event_id,version)
);
CREATE TABLE IF NOT EXISTS approvals (
 id uuid PRIMARY KEY,
 event_id uuid NOT NULL REFERENCES events(id),
 body jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS inquiries (
 id uuid PRIMARY KEY,
 event_id uuid NOT NULL REFERENCES events(id),
 body jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS bookings (
 id uuid PRIMARY KEY,
 event_id uuid NOT NULL REFERENCES events(id),
 body jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS jobs (
 id uuid PRIMARY KEY,
 event_id uuid NOT NULL REFERENCES events(id),
 due_at timestamptz NOT NULL,
 status text NOT NULL CHECK(status IN ('queued','running','done','failed','cancelled')),
 dedupe_key text NOT NULL UNIQUE,
 body jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_due_idx ON jobs(due_at) WHERE status='queued';
CREATE TABLE IF NOT EXISTS audit_events (
 id uuid PRIMARY KEY,
 event_id uuid NOT NULL REFERENCES events(id),
 actor_id uuid NOT NULL,
 action text NOT NULL,
 metadata jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_users FORCE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE events FORCE ROW LEVEL SECURITY;
ALTER TABLE brief_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE brief_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals FORCE ROW LEVEL SECURITY;
ALTER TABLE inquiries ENABLE ROW LEVEL SECURITY;
ALTER TABLE inquiries FORCE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings FORCE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;
CREATE POLICY own_user ON app_users USING(id::text=current_setting('convene.actor_id',true))
 WITH CHECK(id::text=current_setting('convene.actor_id',true));
CREATE POLICY own_event ON events USING(owner_id::text=current_setting('convene.actor_id',true))
 WITH CHECK(owner_id::text=current_setting('convene.actor_id',true));
CREATE POLICY own_brief ON brief_versions USING(EXISTS(SELECT 1 FROM events WHERE id=event_id))
 WITH CHECK(EXISTS(SELECT 1 FROM events WHERE id=event_id));
CREATE POLICY own_approval ON approvals USING(EXISTS(SELECT 1 FROM events WHERE id=event_id))
 WITH CHECK(EXISTS(SELECT 1 FROM events WHERE id=event_id));
CREATE POLICY own_inquiry ON inquiries USING(EXISTS(SELECT 1 FROM events WHERE id=event_id))
 WITH CHECK(EXISTS(SELECT 1 FROM events WHERE id=event_id));
CREATE POLICY own_booking ON bookings USING(EXISTS(SELECT 1 FROM events WHERE id=event_id))
 WITH CHECK(EXISTS(SELECT 1 FROM events WHERE id=event_id));
CREATE POLICY own_job ON jobs USING(EXISTS(SELECT 1 FROM events WHERE id=event_id))
 WITH CHECK(EXISTS(SELECT 1 FROM events WHERE id=event_id));
CREATE POLICY own_audit ON audit_events USING(EXISTS(SELECT 1 FROM events WHERE id=event_id))
 WITH CHECK(EXISTS(SELECT 1 FROM events WHERE id=event_id));
