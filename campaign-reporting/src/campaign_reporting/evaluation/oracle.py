from dataclasses import replace
from datetime import timedelta

from ..compute import compute_report_facts
from ..contracts import Account, Match, SourceBundle
from ..synthetic import portfolio_configs


def oracle_result(case):
    config = portfolio_configs()[0]
    home = config.in_home[0]
    scenario = case.oracle_scenario
    opened = home + timedelta(days=1)
    if scenario == "dm_inhome":
        opened = home
    elif scenario == "dm_day60":
        opened = home + timedelta(days=60)
    elif scenario == "dm_day61":
        opened = home + timedelta(days=61)
    a = Account(
        account_id="oracle-a",
        member_ids=("oracle-m1",),
        open_date=opened,
        client_id=config.client_id,
        campaign_id=config.campaign_id,
    )
    accounts = [a]
    matches = [Match(account_id=a.account_id, channel="dm", mailing=1, flag=1)]
    if scenario == "member_grain":
        accounts += [
            replace(a, account_id="oracle-b"),
            replace(a, account_id="oracle-s", member_ids=("oracle-m2",), product="Savings"),
        ]
        matches += [replace(matches[0], account_id=x.account_id) for x in accounts[1:]]
    if scenario == "late_arrival":
        accounts[0] = replace(a, observed_on=config.digital_start + timedelta(days=100))
    if scenario == "zero_activity":
        accounts, matches = [], []
    source = SourceBundle(
        accounts=tuple(accounts),
        matches=tuple(matches),
        new_member_ids=("oracle-m1", "oracle-m2"),
        client_id=config.client_id,
        campaign_id=config.campaign_id,
        coverage_end=config.final_date,
    )
    f = compute_report_facts(source, config, case.period)
    return {
        "checking_accounts": f.checking_accounts,
        "new_members": f.new_members,
        "cpa": str(f.cpa) if f.cpa is not None else None,
    }
