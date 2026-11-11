import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from decimal import Decimal


def canonical(value) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class CampaignConfig:
    client_id: str = "juniper"
    campaign_id: str = "checking-2026"
    brand: str = "Juniper Valley Credit Union"
    digital_start: date = date(2026, 3, 9)
    digital_end: date = date(2026, 6, 30)
    in_home: tuple[date, ...] = (date(2026, 3, 16), date(2026, 5, 18))
    final_date: date = date(2026, 7, 31)
    launched_mailings: tuple[int, ...] = (1, 2)
    digital_launched: bool = True
    digital_support: tuple[int, ...] = (1, 2)
    audience_size: int = 100000
    digital_reach: int = 80000
    budget: Decimal = Decimal(215000)
    mail_budget: Decimal = Decimal(150500)
    digital_budget: Decimal = Decimal(64500)
    checking_goal: int = 601
    member_goal: int = 605
    cpa_ceiling: Decimal = Decimal("358.17")
    rules_version: str = "checking-v1"

    def period_date(self, period: str) -> date:
        if period == "F":
            return self.final_date
        if period not in ("30", "60", "90", "120"):
            raise ValueError("unknown reporting period")
        return self.digital_start + timedelta(days=int(period))

    def __post_init__(self):
        if self.budget != self.mail_budget + self.digital_budget:
            raise ValueError("budget allocations must reconcile")
        if self.digital_reach > self.audience_size or self.audience_size < 1:
            raise ValueError("invalid audience")
        if not 0 < self.checking_goal or not 0 < self.member_goal:
            raise ValueError("invalid goals")
        if self.digital_end < self.digital_start or self.final_date < self.digital_end:
            raise ValueError("invalid campaign dates")
        if self.final_date < max(self.in_home) + timedelta(days=60):
            raise ValueError("final date precedes a DM window end")


@dataclass(frozen=True)
class Account:
    account_id: str
    member_ids: tuple[str, ...]
    open_date: date
    product: str = "Checking"
    observed_on: date | None = None
    closed_on: date | None = None
    branch: str = "Juniper Central"
    zip_code: str = "00001"
    balance: Decimal = Decimal(100)
    address: str = "1 Synthetic Lane"
    client_id: str = "juniper"
    campaign_id: str = "checking-2026"

    def __post_init__(self):
        if not isinstance(self.open_date, date) or not self.member_ids or self.balance < 0:
            raise ValueError("invalid account")
        if self.observed_on is not None and self.observed_on < self.open_date:
            raise ValueError("observation precedes opening")


@dataclass(frozen=True)
class Match:
    account_id: str
    channel: str
    flag: int
    mailing: int | None = None
    observed_on: date | None = None

    def __post_init__(self):
        if self.channel not in ("dm", "digital") or type(self.flag) is not int or self.flag not in (0, 1):
            raise ValueError("invalid attribution")
        if self.channel == "dm" and self.mailing not in (1, 2):
            raise ValueError("DM match requires mailing")


@dataclass(frozen=True)
class Household:
    household_id: str
    branch: str
    zip_code: str
    digital_reached: bool


@dataclass(frozen=True)
class HistoryCurve:
    counts: tuple[int, ...]
    digital_support: tuple[int, ...] = (1, 2)


@dataclass(frozen=True)
class SourceBundle:
    accounts: tuple[Account, ...] = ()
    matches: tuple[Match, ...] = ()
    new_member_ids: tuple[str, ...] = ()
    audience: tuple[Household, ...] = ()
    history: tuple[HistoryCurve, ...] = ()
    client_id: str = "juniper"
    campaign_id: str = "checking-2026"
    coverage_end: date = date(2026, 7, 31)
    complete: bool = True

    def fingerprint(self):
        return digest(asdict(self))


@dataclass(frozen=True)
class BranchFacts:
    name: str
    zip_code: str
    households: int
    accounts: int
    balance: Decimal
    expected: Decimal
    response_rate: Decimal
    fair_share_accounts: Decimal
    fair_share_balance: Decimal
    cost: Decimal
    cpa: Decimal | None


@dataclass(frozen=True)
class ReportFacts:
    period: str
    as_of: date
    checking_accounts: int
    new_members: int
    direct_members: int
    halo_members: int
    channels: dict[str, int]
    balance: Decimal
    cpa: Decimal | None
    forecast: int
    forecast_low: int
    forecast_high: int
    expected: int
    branches: tuple[BranchFacts, ...] = ()
    product_mix: dict[str, int] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    method: str = "Synthetic historical campaign completion fractions; empirical scenario range."

    def public_dict(self):
        return asdict(self)
