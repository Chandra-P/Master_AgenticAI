def check_readiness(source, config):
    issues = []
    if source.client_id != config.client_id or source.campaign_id != config.campaign_id:
        issues.append("scope_mismatch")
    if not source.complete:
        issues.append("source_incomplete")
    if source.coverage_end < config.final_date:
        issues.append("coverage_incomplete")
    ids = {a.account_id for a in source.accounts}
    if any(m.account_id not in ids for m in source.matches):
        issues.append("orphan_match")
    return {"ready": not issues, "issues": issues, "snapshot_id": source.fingerprint()}
