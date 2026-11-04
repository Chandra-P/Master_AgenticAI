"""Deterministic digital twin. House savings are earmarked within total cash."""

from decimal import Decimal, ROUND_CEILING
from pydantic import BaseModel, Field, ConfigDict
from .money import decimal, fmt, money


class Changes(BaseModel):
    model_config = ConfigDict(extra="forbid")
    monthly_payment: Decimal = Field(default=Decimal(0), ge=0, le=1000000, decimal_places=2)
    down_payment: Decimal = Field(default=Decimal(0), ge=0, le=10000000, decimal_places=2)
    cash_purchase: Decimal = Field(default=Decimal(0), ge=0, le=10000000, decimal_places=2)
    immediate_inflow: Decimal = Field(default=Decimal(0), ge=0, le=10000000, decimal_places=2)
    income_reduction_pct: Decimal = Field(default=Decimal(0), ge=0, le=100)
    cancel_subscription_ids: list[str] = Field(default_factory=list, max_length=50)
    extra_contributions: Decimal = Field(default=Decimal(0), ge=0, le=1000000, decimal_places=2)


def loan_payment(principal: Decimal, apr: Decimal | None, months: int):
    if apr is None:
        raise ValueError("Missing APR; a loan-specific projection requires an interest rate")
    principal, apr = decimal(principal), decimal(apr)
    if not 1 <= months <= 600 or principal < 0 or not 0 <= apr <= 100:
        raise ValueError("Invalid loan principal, APR, or term")
    if apr == 0:
        return money(principal / Decimal(months))
    r = apr / Decimal(1200)
    return money(principal * r / (1 - (1 + r) ** (-months)))


def months_to_goal(gap, contribution):
    if gap <= 0:
        return 0
    return (
        int((gap / contribution).to_integral_value(rounding=ROUND_CEILING))
        if contribution > 0
        else None
    )


def simulate(analytics, changes: dict):
    c = Changes.model_validate(changes)
    cf = analytics.get_monthly_cash_flow()
    cash = analytics.get_cash_position()["value"]
    memory = analytics.memory()
    goals = analytics.get_goal_status()["items"]
    if cash is None or cf["surplus"] is None or not goals:
        raise ValueError("Missing required balance, cash-flow, or goal data")
    income, expense = decimal(cf["income"]), decimal(cf["expenses"])
    cash, emergency = decimal(cash), decimal(memory["emergency_fund_minimum"])
    goal = next((g for g in goals if g["id"] == "house"), goals[0])
    saved, target = decimal(goal["current_amount"]), decimal(goal["target_amount"])
    subs = {
        r["id"]: decimal(r["monthly_equivalent"])
        for r in analytics.find_recurring_subscriptions()["items"]
    }
    selected = set(c.cancel_subscription_ids)
    if not selected <= subs.keys():
        raise ValueError("Unknown or inactive subscription selected")
    removed = sum((subs[x] for x in selected), Decimal(0))
    new_income = money(income * (1 - c.income_reduction_pct / 100))
    surplus = money(new_income - expense - c.monthly_payment + removed - c.extra_contributions)
    outflow = c.down_payment + c.cash_purchase
    remaining = money(cash - outflow + c.immediate_inflow)
    unallocated = max(Decimal(0), cash - emergency - saved)
    house_used = min(saved, max(Decimal(0), outflow - c.immediate_inflow - unallocated))
    house_after = saved - house_used
    allocation = decimal(memory["rules"]["house_monthly_allocation"])
    baseline_contribution = min(max(Decimal(0), decimal(cf["surplus"])), allocation)
    new_contribution = min(max(Decimal(0), surplus), allocation)
    baseline_months = months_to_goal(target - saved, baseline_contribution)
    new_months = months_to_goal(target - house_after, new_contribution)
    delay = (
        max(0, new_months - baseline_months)
        if new_months is not None and baseline_months is not None
        else None
    )
    max_delay = int(memory["rules"]["max_goal_delay_months"])
    constraints = {
        "emergency_fund": {
            "passed": remaining >= emergency,
            "actual": fmt(remaining),
            "minimum": fmt(emergency),
            "rule": "remaining_cash >= emergency_fund_minimum",
        },
        "house_goal": {
            "passed": delay is not None and delay <= max_delay,
            "delay_months": delay,
            "maximum_delay_months": max_delay,
            "rule": "projected additional months <= allowed delay",
        },
        "cash_flow": {
            "passed": surplus >= 0,
            "actual": fmt(surplus),
            "rule": "monthly_surplus >= 0",
        },
        "earmarked_cash": {
            "passed": remaining >= emergency + house_after,
            "rule": "remaining_cash >= emergency_reserve + remaining_house_savings; earmarks cannot overlap",
        },
        "purchase_funding": {
            "passed": remaining >= 0,
            "rule": "cash outflows cannot exceed available cash plus inflows",
        },
    }
    return {
        "baseline": {
            "monthly_income": fmt(income),
            "monthly_expenses": fmt(expense),
            "monthly_surplus": cf["surplus"],
            "cash": fmt(cash),
            "emergency_reserve": fmt(emergency),
            "house_savings": fmt(saved),
            "unallocated_cash": fmt(unallocated),
            "house_months": baseline_months,
            "house_allocation_cap": fmt(allocation),
        },
        "changes": c.model_dump(mode="json"),
        "result": {
            "monthly_income": fmt(new_income),
            "monthly_expenses": fmt(expense + c.monthly_payment - removed + c.extra_contributions),
            "monthly_surplus": fmt(surplus),
            "remaining_cash": fmt(remaining),
            "house_savings": fmt(house_after),
            "house_savings_used": fmt(house_used),
            "monthly_house_contribution": fmt(new_contribution),
            "subscription_savings": fmt(removed),
        },
        "goal_impact": {
            "baseline_months": baseline_months,
            "projected_months": new_months,
            "delay_months": delay,
            "target": fmt(target),
            "target_date": goal["target_date"],
        },
        "constraints": constraints,
        "passed": all(x["passed"] for x in constraints.values()),
        "calculation_steps": [
            {
                "name": "Income after reduction",
                "expression": f"{fmt(income)} × (1 − {fmt(c.income_reduction_pct)} / 100)",
                "value": fmt(new_income),
            },
            {
                "name": "Monthly surplus",
                "expression": f"{fmt(new_income)} − {fmt(expense)} − {fmt(c.monthly_payment)} + {fmt(removed)} − {fmt(c.extra_contributions)}",
                "value": fmt(surplus),
            },
            {
                "name": "Remaining cash",
                "expression": f"{fmt(cash)} − {fmt(outflow)} + {fmt(c.immediate_inflow)}",
                "value": fmt(remaining),
            },
            {
                "name": "House savings consumed",
                "expression": "max(0, cash outflows − inflows − unallocated cash), capped at earmarked house savings",
                "value": fmt(house_used),
            },
        ],
        "assumptions": [
            "Baseline is the last complete calendar month; amounts are USD.",
            "House savings are included in cash. Outflows consume unallocated cash before house savings.",
            "House contributions use available surplus capped at the configured allocation; no interest or investment returns.",
            "Subscription cancellations take effect immediately; annual monthly equivalents may not be immediately refundable.",
            "Vehicle tax, fees, insurance changes, maintenance, and trade-in are unknown and excluded. Loan-only estimates are not final affordability advice.",
            memory["rules"]["assumption_status"],
        ],
        "source_data": {
            "cash": analytics.get_cash_position(),
            "cash_flow": cf,
            "memory_revision": memory["revision"],
            "goal": goal,
        },
        "currency": "USD",
    }


def compare_car(analytics, terms):
    price = decimal(terms["price"])
    scenarios = []
    for name, down in [
        ("Higher down payment", Decimal("20000")),
        ("Lower down payment", Decimal("10000")),
    ]:
        down = min(down, price)
        payment = loan_payment(
            price - down,
            decimal(terms["apr"]) if terms.get("apr") is not None else None,
            int(terms["months"]),
        )
        scenarios.append(
            {
                "name": name,
                "loan": {
                    "principal": fmt(price - down),
                    "apr": terms["apr"],
                    "months": terms["months"],
                    "payment": fmt(payment),
                },
                **simulate(analytics, {"down_payment": fmt(down), "monthly_payment": fmt(payment)}),
            }
        )
    scenarios.append({"name": "Postpone purchase", "loan": None, **simulate(analytics, {})})
    return scenarios
