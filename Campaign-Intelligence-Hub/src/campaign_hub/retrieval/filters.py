"""Validated metadata values: OR within each field, AND across fields."""
FIELDS = ('campaign_id', 'client_name', 'campaign_type', 'region', 'year', 'period', 'document_type')


class FilterConflict(ValueError):
    """Constraints disagree; never retry without the conflicting constraint."""


def available_values(manifest):
    return {key: sorted({d[key] for d in manifest['documents'] if key in d}) for key in FIELDS}


def normalize_filters(filters, catalog):
    if not isinstance(filters, dict): raise ValueError('Metadata filters must be an object')
    result = {}
    for key, raw in filters.items():
        if key not in FIELDS: raise ValueError('Unsupported metadata field: '+key)
        values = raw if isinstance(raw, list) else [raw]
        if not values: continue
        allowed = catalog.get(key, [])
        if any(not any(type(v) is type(a) and v == a for a in allowed) for v in values):
            raise ValueError('Unsupported metadata value for '+key)
        result[key] = list(dict.fromkeys(values))
    return result


def merge_filters(*groups):
    result = {}
    for group in groups:
        for key, values in group.items():
            if key in result:
                values = [v for v in result[key] if v in values]
                if not values: raise FilterConflict('Conflicting filters for '+key)
            result[key] = list(values)
    return result


def chroma_where(filters):
    clauses = [{key: {'$in': values}} if isinstance(values, list) else {key: values}
               for key, values in (filters or {}).items()]
    if not clauses: return None
    return clauses[0] if len(clauses) == 1 else {'$and': clauses}
