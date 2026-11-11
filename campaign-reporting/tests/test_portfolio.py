from campaign_reporting.compute import compute_report_facts
from campaign_reporting.synthetic import generate_sources, portfolio_configs


def test_fifty_isolated_clients_across_2024_and_2025():
    configs = portfolio_configs()
    assert len(configs) == 50
    assert len({c.client_id for c in configs}) == 50
    assert len({c.brand for c in configs}) == 50
    assert sum(c.digital_start.year == 2024 for c in configs) == 25
    assert sum(c.digital_start.year == 2025 for c in configs) == 25
    assert len({c.digital_start for c in configs}) == 50
    for cfg in (configs[0], configs[24], configs[25], configs[-1]):
        src = generate_sources(42, cfg.client_id, config=cfg)
        assert {a.client_id for a in src.accounts} == {cfg.client_id}
        facts = compute_report_facts(src, cfg, "F")
        assert facts.checking_accounts > 0
        assert src.coverage_end == cfg.final_date
        assert facts.cpa is not None
