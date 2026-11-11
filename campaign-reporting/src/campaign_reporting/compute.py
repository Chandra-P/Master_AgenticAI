from collections import Counter
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from statistics import median

from .contracts import BranchFacts, CampaignConfig, ReportFacts, SourceBundle

CENT = Decimal("0.01")


def eligible_accounts(source: SourceBundle, cfg: CampaignConfig, as_of: date):
    if source.client_id != cfg.client_id or source.campaign_id != cfg.campaign_id:
        raise PermissionError("source scope mismatch")
    unique = {}
    for account in source.accounts:
        if account.client_id != cfg.client_id or account.campaign_id != cfg.campaign_id:
            raise PermissionError("account scope mismatch")
        if account.account_id in unique and unique[account.account_id] != account:
            raise ValueError("conflicting account snapshots require explicit reconciliation")
        unique[account.account_id] = account
    channels = {}
    for match in source.matches:
        a = unique.get(match.account_id)
        if not a or match.flag != 1 or a.open_date > as_of:
            continue
        if (a.observed_on and a.observed_on > as_of) or (match.observed_on and match.observed_on > as_of):
            continue
        if match.channel == "digital":
            valid = cfg.digital_launched
        else:
            home = cfg.in_home[match.mailing - 1]
            valid = match.mailing in cfg.launched_mailings and home < a.open_date <= home + timedelta(days=60)
        if valid:
            channels.setdefault(a.account_id, set()).add(match.channel)
    return [(unique[key], value) for key, value in channels.items()]


def compute_report_facts(source: SourceBundle, cfg: CampaignConfig, period: str) -> ReportFacts:
    as_of = cfg.period_date(period)
    rows = eligible_accounts(source, cfg, as_of)
    checking = [(a, c) for a, c in rows if a.product == "Checking"]
    n = len(checking)
    new = set(source.new_member_ids)
    all_members = {m for a, _ in rows for m in a.member_ids if m in new}
    direct = {m for a, _ in checking for m in a.member_ids if m in new}
    channels = {"Both": 0, "DM Only": 0, "Digital Only": 0}
    for _, c in checking:
        channels["Both" if len(c) == 2 else ("DM Only" if "dm" in c else "Digital Only")] += 1
    day = (as_of - cfg.digital_start).days
    fractions = sorted(
        h.counts[min(day, len(h.counts) - 1)] / h.counts[-1]
        for h in source.history
        if h.digital_support == cfg.digital_support and h.counts[-1]
    )
    limitations = [
        "Synthetic examples; attribution overlap is not incremental lift.",
        "Core-extract inclusion is funding evidence; no deposit dates are available.",
    ]
    if period == "F":
        center = low = high = n
        expected = cfg.checking_goal
    elif fractions and min(fractions) > 0:
        center = max(n, round(n / median(fractions)))
        low = max(n, round(n / fractions[int((len(fractions) - 1) * 0.9)]))
        high = max(center, round(n / fractions[int((len(fractions) - 1) * 0.1)]))
        expected = round(cfg.checking_goal * median(fractions))
    else:
        center = low = high = n
        expected = 0
        limitations.append("No compatible historical cohort: forecast unavailable beyond observed count.")
    ready_cpa = day >= 120 and cfg.digital_launched and set(cfg.launched_mailings) == {1, 2}
    cpa = (cfg.budget / n).quantize(CENT, ROUND_HALF_UP) if ready_cpa and n else None
    balances = sum((a.balance for a, _ in checking), Decimal(0))
    households = Counter(h.branch for h in source.audience)
    branch_names = sorted(set(households) | {a.branch for a, _ in checking})
    branches = []
    denom = len(source.audience)
    for branch in branch_names:
        accts = [a for a, _ in checking if a.branch == branch]
        count, hh = len(accts), households[branch]
        bal = sum((a.balance for a in accts), Decimal(0))
        share = Decimal(hh) / denom if denom else Decimal(0)
        cost = cfg.budget * share
        branches.append(
            BranchFacts(
                branch,
                next((a.zip_code for a in accts), "00000"),
                hh,
                count,
                bal,
                (Decimal(expected) * share).quantize(CENT),
                Decimal(count) / hh * 100 if hh else Decimal(0),
                Decimal(count) / n / share if n and share else Decimal(0),
                bal / balances / share if balances and share else Decimal(0),
                cost.quantize(CENT),
                (cost / count).quantize(CENT) if count and ready_cpa else None,
            )
        )
    return ReportFacts(
        period,
        as_of,
        n,
        len(all_members),
        len(direct),
        len(all_members - direct),
        channels,
        balances,
        cpa,
        center,
        low,
        high,
        expected,
        tuple(branches),
        dict(Counter(a.product for a, _ in checking)),
        tuple(limitations),
    )
