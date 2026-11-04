CREATE TABLE planner_runs (
    id uuid PRIMARY KEY,
    event_id uuid NOT NULL REFERENCES events(id),
    brief_version integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY(event_id,brief_version) REFERENCES brief_versions(event_id,version)
);
ALTER TABLE planner_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE planner_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY planner_run_owner ON planner_runs USING
    (EXISTS (SELECT 1 FROM events WHERE events.id=planner_runs.event_id));
