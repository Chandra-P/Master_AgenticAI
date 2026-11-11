"""Seeded invented sources; no production or attachment inputs."""

import random
from datetime import date, timedelta
from decimal import Decimal

from .contracts import Account, CampaignConfig, HistoryCurve, Household, Match, SourceBundle

BRANCHES = (
    "Juniper Central",
    "Cedar Crossing",
    "Willow Creek",
    "Mesa Grove",
    "Canyon Ridge",
    "Sage Meadows",
    "Copper Hills",
    "Pine Landing",
    "Riverbend",
    "Sunrise Commons",
    "Aspen Square",
    "Stonebridge",
)


def portfolio_configs() -> tuple[CampaignConfig, ...]:
    prefixes = ("Alder", "Birch", "Cedar", "Cypress", "Elm", "Juniper", "Maple", "Oak", "Pine", "Willow")
    suffixes = ("Valley", "Grove", "Ridge", "Meadows", "Crossing")
    result = []
    for i in range(50):
        start = date(2024 if i < 25 else 2025, 1, 15) + timedelta(days=(i % 25) * 6)
        result.append(
            CampaignConfig(
                client_id=f"synthetic-cu-{i + 1:03d}",
                campaign_id=f"checking-{start.year}-{i + 1:03d}",
                brand=f"{prefixes[i % 10]} {suffixes[i // 10]} Credit Union",
                digital_start=start,
                digital_end=start + timedelta(days=113),
                in_home=(start + timedelta(days=7), start + timedelta(days=70)),
                final_date=start + timedelta(days=144),
            )
        )
    return tuple(result)


def generate_sources(seed: int = 42, client_id: str = "juniper", *, config=None) -> SourceBundle:
    r = random.Random(seed)
    cfg = config or CampaignConfig(client_id=client_id)
    audience = tuple(
        Household(f"SYN_HH_{i:06d}", BRANCHES[i % 12], f"{i % 12 + 1:05d}", i < cfg.digital_reach)
        for i in range(cfg.audience_size)
    )
    accounts, matches, members = [], [], set()
    for i in range(760):
        product = "Checking" if i < 650 else ("Savings" if i % 2 else "Money market")
        opened = cfg.digital_start + timedelta(days=r.randint(8, 126))
        member = f"SYN_MEMBER_{i if i % 11 else max(0, i - 1):05d}"
        if i % 9:
            members.add(member)
        account_id = f"SYN_ACCOUNT_{i:05d}"
        accounts.append(
            Account(
                account_id=account_id,
                member_ids=(member,),
                open_date=opened,
                observed_on=opened + timedelta(days=r.randint(0, 6)),
                product=product,
                branch=BRANCHES[i % 12],
                zip_code=f"{i % 12 + 1:05d}",
                balance=Decimal(r.randint(500, 900000)) / 100,
                address=f"{10000 + i} Fabricated Fixture Road",
                client_id=client_id,
                campaign_id=cfg.campaign_id,
                closed_on=opened + timedelta(days=14) if i % 17 == 0 else None,
            )
        )
        # Independent source matches; dates govern DM, TU flag governs digital.
        digital = i % 5 != 0
        if digital:
            matches.append(
                Match(
                    account_id=account_id, channel="digital", flag=1, observed_on=opened + timedelta(days=2)
                )
            )
        for mailing, home in enumerate(cfg.in_home, 1):
            if home < opened <= home + timedelta(days=60) and i % 4 != 0:
                matches.append(Match(account_id=account_id, channel="dm", mailing=mailing, flag=1))
        if i % 19 == 0 and matches and matches[-1].account_id == account_id:
            matches.append(matches[-1])
    horizon = (cfg.final_date - cfg.digital_start).days
    history = []
    for j in range(24):
        hr = random.Random(seed * 100 + j)
        days = [hr.randint(8, 65) if k % 2 else hr.randint(71, 132) for k in range(700)]
        history.append(HistoryCurve(tuple(sum(x <= d for x in days) for d in range(horizon + 1))))
    return SourceBundle(
        tuple(accounts),
        tuple(matches),
        tuple(sorted(members)),
        audience,
        tuple(history),
        client_id=client_id,
        campaign_id=cfg.campaign_id,
        coverage_end=cfg.final_date,
    )
