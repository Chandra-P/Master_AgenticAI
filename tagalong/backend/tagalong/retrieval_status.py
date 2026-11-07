"""Per-plan freshness of the current source versions in the vector index."""


def indexing_status(state, plan_id):
    current_sources=[source for source in state.get('sources',{}).values()
                     if source.get('plan_id')==plan_id and not source.get('deleted')]
    counts={'current_sources':len(current_sources),'indexed_sources':0,'pending_sources':0,'failed_sources':0}
    jobs=state.get('jobs',{}).values()
    for source in current_sources:
        key=plan_id+':'+source['id']
        current_jobs=[job for job in jobs if job.get('source_key')==key and job.get('version')==source.get('version')]
        statuses={job.get('status') for job in current_jobs}
        if 'done' in statuses:
            counts['indexed_sources']+=1
        elif 'failed' in statuses:
            counts['failed_sources']+=1
        else:
            counts['pending_sources']+=1
    status='failed' if counts['failed_sources'] else 'pending' if counts['pending_sources'] else 'current'
    return {'status':status,**counts}
