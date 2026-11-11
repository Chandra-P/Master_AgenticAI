from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from campaign_reporting.compute import compute_report_facts, eligible_accounts
from campaign_reporting.contracts import Account, CampaignConfig, Match, SourceBundle
from campaign_reporting.synthetic import generate_sources


def sample():
    cfg = CampaignConfig()
    accounts = (
        Account(account_id="a1", member_ids=("m1",), open_date=date(2026, 3, 17)),
        Account(account_id="a2", member_ids=("m1",), open_date=date(2026, 3, 18)),
        Account(account_id="s1", member_ids=("m2",), product="Savings", open_date=date(2026, 3, 19)),
        Account(account_id="a3", member_ids=("existing",), open_date=date(2026, 3, 20)),
    )
    matches = (
        Match(account_id="a1", channel="dm", mailing=1, flag=1),
        Match(account_id="a1", channel="digital", flag=1),
        Match(account_id="a1", channel="digital", flag=1),
        Match(account_id="a2", channel="dm", mailing=1, flag=1),
        Match(account_id="s1", channel="digital", flag=1),
        Match(account_id="a3", channel="digital", flag=1),
    )
    return cfg, SourceBundle(accounts=accounts, matches=matches, new_member_ids=("m1", "m2"))


def test_distinct_accounts_members_channels_and_any_product_halo():
    cfg, src = sample()
    f = compute_report_facts(src, cfg, "30")
    assert f.checking_accounts == 3
    assert f.new_members == 2
    assert f.direct_members == 1
    assert f.halo_members == 1
    assert f.channels == {"Both": 1, "DM Only": 1, "Digital Only": 1}
    assert f.cpa is None


@pytest.mark.parametrize(
    "opened,want",
    [
        (date(2026, 3, 16), 0),
        (date(2026, 3, 17), 1),
        (date(2026, 5, 15), 1),
        (date(2026, 5, 16), 0),
    ],
)
def test_dm_excludes_in_home_includes_day_sixty(opened, want):
    a = Account(account_id="a", member_ids=("m",), open_date=opened)
    s = SourceBundle(accounts=(a,), matches=(Match(account_id="a", channel="dm", mailing=1, flag=1),))
    assert len(eligible_accounts(s, CampaignConfig(), date(2026, 7, 31))) == want


def test_late_arrival_uses_open_date_but_does_not_leak_future_snapshot():
    cfg, src = sample()
    late = replace(src.accounts[0], observed_on=date(2026, 6, 1), closed_on=date(2026, 6, 2))
    src = replace(src, accounts=(late,), matches=src.matches[:2])
    assert compute_report_facts(src, cfg, "30").checking_accounts == 0
    assert compute_report_facts(src, cfg, "120").checking_accounts == 1


def test_cpa_requires_day_120_and_every_actual_launch():
    cfg, src = sample()
    assert compute_report_facts(src, cfg, "90").cpa is None
    assert compute_report_facts(src, cfg, "120").cpa == Decimal("71666.67")
    assert compute_report_facts(src, replace(cfg, launched_mailings=(1,)), "120").cpa is None
    assert compute_report_facts(SourceBundle(), cfg, "120").cpa is None


def test_joint_holders_and_duplicate_snapshots_do_not_multiply_accounts():
    cfg, src = sample()
    joint = replace(src.accounts[0], member_ids=("m1", "m2"))
    s = replace(src, accounts=(joint, joint), matches=src.matches[:2])
    f = compute_report_facts(s, cfg, "30")
    assert (f.checking_accounts, f.new_members) == (1, 2)


def test_synthetic_generation_reproduces_population_and_aggregate_reconciliation():
    a = generate_sources(42, "juniper")
    assert a == generate_sources(42, "juniper")
    assert a != generate_sources(43, "juniper")
    assert len(a.audience) == 100000
    assert sum(h.digital_reached for h in a.audience) == 80000
    for period in ("30", "60", "90", "120", "F"):
        f = compute_report_facts(a, CampaignConfig(), period)
        assert sum(f.channels.values()) == f.checking_accounts
        assert sum(b.accounts for b in f.branches) == f.checking_accounts
        assert sum(f.product_mix.values()) == f.checking_accounts
        assert f.direct_members + f.halo_members == f.new_members
        assert f.forecast_low <= f.forecast <= f.forecast_high
    final = compute_report_facts(a, CampaignConfig(), "F")
    assert final.forecast == final.checking_accounts


def test_missing_dates_and_conflicting_duplicate_accounts_fail_closed():
    with pytest.raises(ValueError):
        Account(account_id="a", member_ids=("m",), open_date=None)
    cfg, src = sample()
    s = replace(src, accounts=(src.accounts[0], replace(src.accounts[0], product="Savings")))
    with pytest.raises(ValueError, match="conflicting"):
        compute_report_facts(s, cfg, "30")


def test_digital_eligibility_comes_from_tu_flag_not_local_mail_window():
    a = Account(account_id="d", member_ids=("m",), open_date=date(2026, 7, 20))
    for flag, want in [(0, 0), (1, 1)]:
        s = SourceBundle(accounts=(a,), matches=(Match(account_id="d", channel="digital", flag=flag),))
        assert compute_report_facts(s, CampaignConfig(), "F").checking_accounts == want
