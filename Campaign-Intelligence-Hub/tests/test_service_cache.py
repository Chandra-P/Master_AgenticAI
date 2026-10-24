def test_service_cache_invalidates_after_application_code_changes(tmp_path,monkeypatch):
    from campaign_hub.config import Settings
    import campaign_hub.ui.resources as resources
    settings=Settings(root=tmp_path)
    settings.data.mkdir()
    (settings.data/'manifest.json').write_text('{}')
    source=tmp_path/'src/campaign_hub/reporting/service.py'
    source.parent.mkdir(parents=True)
    source.write_text('revision one')
    monkeypatch.setattr(resources,'Settings',lambda:settings)
    identities=[]
    monkeypatch.setattr(resources,'_cached_service',lambda *args:identities.append(args))
    resources.service_for('model')
    source.write_text('revision two')
    resources.service_for('model')
    assert identities[0]!=identities[1]
