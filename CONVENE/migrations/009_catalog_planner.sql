ALTER TABLE planner_runs ADD COLUMN action text NOT NULL DEFAULT 'research'
 CHECK(action IN ('research','compare_catalog'));
CREATE TABLE catalog_comparisons (
 event_id uuid NOT NULL,
 brief_version integer NOT NULL,
 directory_revision text NOT NULL,
 run_id uuid NOT NULL REFERENCES planner_runs(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(event_id,brief_version,directory_revision),
 FOREIGN KEY(event_id,brief_version) REFERENCES brief_versions(event_id,version)
);
ALTER TABLE catalog_comparisons ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalog_comparisons FORCE ROW LEVEL SECURITY;
CREATE POLICY catalog_comparison_owner ON catalog_comparisons USING
 (EXISTS(SELECT 1 FROM events WHERE events.id=catalog_comparisons.event_id));
CREATE TABLE event_shortlist (
 event_id uuid NOT NULL,
 brief_version integer NOT NULL,
 vendor_id text NOT NULL,
 vendor_version integer NOT NULL,
 approval_id uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(event_id,brief_version,vendor_id),
 FOREIGN KEY(event_id,brief_version) REFERENCES brief_versions(event_id,version)
);
ALTER TABLE event_shortlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_shortlist FORCE ROW LEVEL SECURITY;
CREATE POLICY shortlist_owner ON event_shortlist USING
 (EXISTS(SELECT 1 FROM events WHERE events.id=event_shortlist.event_id));
