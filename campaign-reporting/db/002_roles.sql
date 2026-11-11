-- Install after 001_schema.sql. Provision LOGIN roles/secrets separately.
BEGIN;
DO $$
DECLARE role_name TEXT;
BEGIN
 FOREACH role_name IN ARRAY ARRAY['campaign_ingestion','campaign_compute','campaign_narrative','campaign_review','campaign_delivery']
 LOOP
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=role_name) THEN
   EXECUTE format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOBYPASSRLS', role_name);
  END IF;
 END LOOP;
END $$;
CREATE OR REPLACE FUNCTION reporting_client() RETURNS TEXT
LANGUAGE SQL STABLE SECURITY DEFINER SET search_path=pg_catalog,public
AS $$ SELECT client_id FROM public.service_bindings WHERE login_name=session_user $$;
REVOKE ALL ON FUNCTION reporting_client() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION reporting_client() TO campaign_ingestion,campaign_compute,campaign_narrative,campaign_review,campaign_delivery;
GRANT USAGE ON SCHEMA public TO campaign_ingestion,campaign_compute,campaign_narrative,campaign_review,campaign_delivery;
DO $$
DECLARE table_name TEXT;
BEGIN
 FOREACH table_name IN ARRAY ARRAY['report_runs','audit_events','campaign_configs','source_snapshots','mart_account_outcomes']
 LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',table_name);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',table_name);
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename=table_name AND policyname='client_isolation') THEN
   EXECUTE format('CREATE POLICY client_isolation ON %I USING (client_id=reporting_client()) WITH CHECK (client_id=reporting_client())',table_name);
  END IF;
 END LOOP;
END $$;
GRANT SELECT,INSERT ON source_snapshots TO campaign_ingestion;
GRANT SELECT ON source_snapshots,campaign_configs TO campaign_compute;
GRANT SELECT,INSERT,UPDATE ON report_runs,mart_account_outcomes TO campaign_compute;
GRANT SELECT,INSERT ON audit_events TO campaign_compute,campaign_review,campaign_delivery;
GRANT SELECT,UPDATE ON report_runs TO campaign_review,campaign_delivery;
GRANT SELECT,INSERT ON campaign_configs TO campaign_review;
-- The view explicitly scopes by authenticated database session identity.
-- View owner must remain trusted. Narrative receives no base-table privileges.
CREATE OR REPLACE VIEW narrative_runs WITH (security_barrier=true) AS
 SELECT run_id,client_id,created_at,
   jsonb_build_object(
     'run_id',run_id,'client_id',client_id,'campaign_id',campaign_id,
     'facts',data::jsonb->'facts','config',data::jsonb->'config',
     'rules_version',data::jsonb->'rules_version','correction',data::jsonb->'correction',
     'version',version,'status',status
   )::text AS data
 FROM report_runs WHERE client_id=reporting_client();
GRANT SELECT ON narrative_runs TO campaign_narrative;
COMMIT;
