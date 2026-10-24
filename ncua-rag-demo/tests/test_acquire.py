"""Catches accepting error pages, incorrect identity, and corrupt resumes."""
import json
from pathlib import Path
import pytest

def test_error_html_is_not_a_report():
    from pipeline.acquire import validate_report
    with pytest.raises(ValueError):
        validate_report(b'<html><title>Error</title>Service unavailable</html>','5536')

def test_report_identity_must_match():
    from pipeline.acquire import validate_report
    html=b'<html>Financial Performance Report NAVY FEDERAL Charter Number: 5536<table><tr><td>TOTAL ASSETS</td><td>100</td></tr></table></html>'
    with pytest.raises(ValueError):
        validate_report(html,'9999')

def test_atomic_manifest_keeps_records(tmp_path):
    from pipeline.acquire import write_manifest
    p=tmp_path/'manifest.json'
    write_manifest(p,{'reports':[{'id':'5536-summary'}]})
    assert json.loads(p.read_text())['reports'][0]['id']=='5536-summary'
    assert not p.with_suffix('.tmp').exists()

def test_ncua_header_without_tr_is_accepted():
    from pipeline.acquire import validate_report
    html=b'<html>Financial Performance Report<table><thead><th>Charter</th><th>Name</th></thead><tbody><tr><td>5536</td><td>NAVY FEDERAL</td></tr></tbody></table><table><tr><td>TOTAL ASSETS Dec-2025</td><td>100</td></tr></table></html>'
    assert validate_report(html,'5536')['institution']=='NAVY FEDERAL'

def test_coverage_ignores_years_in_explanatory_notes():
    from pipeline.acquire import validate_report
    html=b'<html>Financial Performance Report<table><tr><td>5536</td><td>NAVY FEDERAL</td></tr></table><table><tr><th>Line Item</th><th>Dec-2025</th></tr><tr><td>Assets</td><td>100</td></tr></table><p>Before 2020 accounting rules differed.</p></html>'
    assert validate_report(html,'5536')['years']==['2025']
