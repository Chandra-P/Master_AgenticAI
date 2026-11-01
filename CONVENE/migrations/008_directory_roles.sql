-- Administrative writes require the dedicated DB login, not a request-set flag.
ALTER POLICY directory_record_read ON vendor_records USING
 (status='approved' OR current_user='convene_directory_admin');
ALTER POLICY directory_record_insert ON vendor_records WITH CHECK(current_user='convene_directory_admin');
ALTER POLICY directory_record_update ON vendor_records USING(current_user='convene_directory_admin')
 WITH CHECK(current_user='convene_directory_admin');
ALTER POLICY directory_version_read ON vendor_versions USING
 (current_user='convene_directory_admin' OR EXISTS
  (SELECT 1 FROM vendor_records r WHERE r.id=vendor_id AND r.status='approved' AND r.published_version=version));
ALTER POLICY directory_version_insert ON vendor_versions WITH CHECK(current_user='convene_directory_admin');
ALTER POLICY directory_approval_read ON vendor_approval_history USING
 (current_user='convene_directory_admin' OR EXISTS
  (SELECT 1 FROM vendor_records r WHERE r.id=vendor_id AND r.status='approved' AND r.published_decision=vendor_approval_history.id));
ALTER POLICY directory_approval_insert ON vendor_approval_history WITH CHECK(current_user='convene_directory_admin');
