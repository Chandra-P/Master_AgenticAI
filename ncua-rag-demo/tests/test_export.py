def test_source_view_escapes_active_content_and_keeps_table_cells():
    from pipeline.export import source_view
    source='<html><script>alert(1)</script><table><tr><th>Assets</th><td><img src=x onerror=alert(2)>100</td></tr></table></html>'
    page=source_view(source,{'institution':'Example','filename':'example.html','charter':'1','retrieved_at':'2026-10-18','source_url':'https://fpr.ncua.gov/'})
    assert '<script>' not in page and 'onerror' not in page and '<img' not in page
    assert '<td>100</td>' in page
    assert 'table-1' in page
