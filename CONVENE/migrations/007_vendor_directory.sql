CREATE TABLE vendor_records (
 id text PRIMARY KEY,
 head_version integer NOT NULL DEFAULT 0 CHECK(head_version>=0),
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','approved','suspended','retired')),
 published_version integer,
 published_decision uuid,
 published_action text NOT NULL DEFAULT 'approved' CHECK(published_action='approved'),
 CHECK((published_version IS NULL)=(published_decision IS NULL)),
 CHECK(status<>'approved' OR published_version IS NOT NULL)
);
CREATE TABLE vendor_versions (
 vendor_id text NOT NULL REFERENCES vendor_records(id),
 version integer NOT NULL CHECK(version>0),
 body jsonb NOT NULL,
 content_hash text NOT NULL,
 source_evidence jsonb NOT NULL,
 created_by text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(vendor_id,version)
);
CREATE TABLE vendor_approval_history (
 id uuid PRIMARY KEY,
 vendor_id text NOT NULL,
 version integer NOT NULL,
 action text NOT NULL CHECK(action IN ('approved','suspended')),
 actor_label text NOT NULL,
 actor_kind text NOT NULL CHECK(actor_kind IN ('local_operator','conversation_approval')),
 approved_on date NOT NULL,
 reason text NOT NULL,
 content_hash text NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(vendor_id,version) REFERENCES vendor_versions(vendor_id,version),
 UNIQUE(vendor_id,version,id,action)
);
ALTER TABLE vendor_records ADD CONSTRAINT published_vendor_decision
 FOREIGN KEY(id,published_version,published_decision,published_action)
 REFERENCES vendor_approval_history(vendor_id,version,id,action);
ALTER TABLE vendor_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_records FORCE ROW LEVEL SECURITY;
ALTER TABLE vendor_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE vendor_approval_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_approval_history FORCE ROW LEVEL SECURITY;
CREATE POLICY directory_record_read ON vendor_records FOR SELECT USING
 (status='approved' OR current_setting('convene.directory_admin',true)='true');
CREATE POLICY directory_record_insert ON vendor_records FOR INSERT WITH CHECK
 (current_setting('convene.directory_admin',true)='true');
CREATE POLICY directory_record_update ON vendor_records FOR UPDATE USING
 (current_setting('convene.directory_admin',true)='true') WITH CHECK
 (current_setting('convene.directory_admin',true)='true');
CREATE POLICY directory_version_read ON vendor_versions FOR SELECT USING
 (current_setting('convene.directory_admin',true)='true' OR EXISTS
  (SELECT 1 FROM vendor_records r WHERE r.id=vendor_id AND r.status='approved' AND r.published_version=version));
CREATE POLICY directory_version_insert ON vendor_versions FOR INSERT WITH CHECK
 (current_setting('convene.directory_admin',true)='true');
CREATE POLICY directory_approval_read ON vendor_approval_history FOR SELECT USING
 (current_setting('convene.directory_admin',true)='true' OR EXISTS
  (SELECT 1 FROM vendor_records r WHERE r.id=vendor_id AND r.status='approved' AND r.published_decision=vendor_approval_history.id));
CREATE POLICY directory_approval_insert ON vendor_approval_history FOR INSERT WITH CHECK
 (current_setting('convene.directory_admin',true)='true');
