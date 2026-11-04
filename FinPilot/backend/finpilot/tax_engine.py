"""Deterministic, scope-limited 2026 federal W-2 planning for Texas households."""

import json
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from .analytics import Analytics
from .money import decimal, fmt, money
from .payroll import tax_profile, latest_paystubs, MONEY_LABELS
from .scenario import simulate

RULES = json.loads((Path(__file__).parent / "rules/us_tx_2026.json").read_text())
D = decimal
ZERO = Decimal(0)


class TaxChanges(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employment_key: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    extra_traditional_per_check: Decimal = Field(default=ZERO, ge=0, le=100000, decimal_places=2)
    extra_roth_per_check: Decimal = Field(default=ZERO, ge=0, le=100000, decimal_places=2)
    extra_hsa_per_check: Decimal = Field(default=ZERO, ge=0, le=100000, decimal_places=2)
    extra_withholding_per_check: Decimal = Field(default=ZERO, ge=0, le=100000, decimal_places=2)


def bracket_breakdown(taxable_income, status, year=2026):
    if year != RULES["tax_year"] or status not in RULES["brackets"]:
        raise ValueError("Unsupported tax year or filing status; no estimate generated")
    income = D(taxable_income)
    if income < 0:
        raise ValueError("Taxable income cannot be negative")
    previous = ZERO
    bands = []
    for upper, rate in RULES["brackets"][status]:
        top = D(upper) if upper is not None else income
        portion = max(ZERO, min(income, top) - previous)
        if portion:
            bands.append(
                {
                    "lower_bound": fmt(previous),
                    "upper_bound": fmt(top) if upper is not None else None,
                    "rate": str(D(rate) * 100),
                    "taxable_amount": fmt(portion),
                    "tax": fmt(portion * D(rate)),
                }
            )
        if upper is None or income <= top:
            break
        previous = top
    return bands


def progressive_tax(taxable_income, status, year=2026):
    return fmt(sum((D(b["tax"]) for b in bracket_breakdown(taxable_income, status, year)), ZERO))


def annual_safe_harbor(
    tax, withholding, estimated, prior_tax=None, prior_agi=None, prior_full_year=False
):
    tax, withholding, estimated = map(D, (tax, withholding, estimated))
    if min(tax, withholding, estimated) < 0:
        raise ValueError("Tax and payments must be nonnegative")
    current = money(tax * D(RULES["safe_harbor"]["current_year_fraction"]))
    prior = None
    if prior_full_year and prior_tax is not None and prior_agi is not None:
        fraction = D("1.10") if D(prior_agi) > D("150000") else D("1.00")
        prior = money(D(prior_tax) * fraction)
    unknown = prior_tax is None or prior_agi is None
    target = min(current, prior) if prior is not None else current
    paid = withholding + estimated
    low_balance = tax - withholding < D("1000")
    passed = True if low_balance or paid >= target else None if unknown else False
    return {
        "current_year_target": fmt(current),
        "prior_year_target": fmt(prior) if prior is not None else None,
        "required_annual_payment": None
        if unknown and not low_balance and paid < current
        else fmt(target),
        "projected_payments": fmt(paid),
        "shortfall": None
        if passed is None
        else fmt(ZERO if low_balance else max(ZERO, target - paid)),
        "annual_screen_passed": passed,
        "less_than_1000_after_withholding": low_balance,
        "note": "Annual screening only. Estimated-payment installment timing, annualized-income exceptions, penalties, and special circumstances are not calculated. A late estimated payment may not fix an earlier installment shortfall.",
    }


def project_tax(conn, changes=None, user_id="demo"):
    profile = tax_profile(conn, user_id)
    if not profile["confirmed"] or not profile["supported_scope_confirmed"]:
        raise ValueError("Review and confirm the tax profile and supported scope first")
    c = TaxChanges.model_validate(changes or {})
    if c.extra_hsa_per_check and not profile["hsa_payroll_cafeteria_plan_confirmed"]:
        raise ValueError("HSA payroll tax savings require confirming a pre-tax cafeteria plan")
    stubs = latest_paystubs(conn, profile, user_id)
    employment_keys = {s["facts"]["employment_key"] for s in stubs}
    positive = any(
        v > 0
        for v in [
            c.extra_traditional_per_check,
            c.extra_roth_per_check,
            c.extra_hsa_per_check,
            c.extra_withholding_per_check,
        ]
    )
    if positive and c.employment_key not in employment_keys:
        raise ValueError("Select one confirmed employment for payroll changes")
    workers = []
    for stub in stubs:
        f = stub["facts"]
        remaining = f["remaining_periods"]
        selected = c.employment_key == f["employment_key"]
        additions = {
            "traditional_401k": c.extra_traditional_per_check if selected else ZERO,
            "roth_401k": c.extra_roth_per_check if selected else ZERO,
            "hsa": c.extra_hsa_per_check if selected else ZERO,
            "federal_withholding": c.extra_withholding_per_check if selected else ZERO,
        }
        if selected and positive and remaining == 0:
            raise ValueError(
                "No remaining paychecks; payroll changes cannot be applied to this tax year"
            )
        if additions["traditional_401k"] + additions["hsa"] > D(
            f["federal_taxable_current"]
        ) or additions["hsa"] > min(
            D(f["social_security_wages_current"]), D(f["medicare_wages_current"])
        ):
            raise ValueError("Contributions exceed eligible remaining wage bases")
        projected = {
            key: D(f[key + "_ytd"])
            + (D(f[key + "_current"]) + additions.get(key, ZERO)) * remaining
            for key in MONEY_LABELS
        }
        projected["federal_taxable"] -= (
            additions["traditional_401k"] + additions["hsa"]
        ) * remaining
        projected["social_security_wages"] -= additions["hsa"] * remaining
        projected["medicare_wages"] -= additions["hsa"] * remaining
        if projected["traditional_401k"] + projected["roth_401k"] > D(RULES["employee_401k_limit"]):
            raise ValueError(
                "Projected employee traditional plus Roth 401(k) deferrals exceed the 2026 $24,500 limit"
            )
        future_ss_wages = max(
            ZERO, projected["social_security_wages"] - D(f["social_security_wages_ytd"])
        )
        future_ss = money(
            min(
                future_ss_wages,
                max(
                    ZERO,
                    D(RULES["social_security"]["wage_base"]) - D(f["social_security_wages_ytd"]),
                ),
            )
            * D(RULES["social_security"]["rate"])
        )
        future_med = money(
            (projected["medicare_wages"] - D(f["medicare_wages_ytd"])) * D(RULES["medicare_rate"])
        )
        threshold = D(RULES["additional_medicare"]["employer_threshold"])
        future_add = money(
            (
                max(ZERO, projected["medicare_wages"] - threshold)
                - max(ZERO, D(f["medicare_wages_ytd"]) - threshold)
            )
            * D(RULES["additional_medicare"]["rate"])
        )
        workers.append(
            {
                "employment_key": f["employment_key"],
                "employee_key": f["employee_key"],
                "employee_name": f["employee_name"],
                "employer_name": f["employer_name"],
                "pay_date": f["pay_date"],
                "annual_periods": f["annual_periods"],
                "remaining_periods": remaining,
                "projected": {key: fmt(v) for key, v in projected.items()},
                "future_ss_withholding": fmt(future_ss),
                "future_medicare_withholding": fmt(future_med),
                "future_additional_medicare_withholding": fmt(future_add),
                "additional_medicare_withholding_ytd": f["additional_medicare_withholding_ytd"],
                "document_id": stub["document_id"],
                "paystub_id": stub["id"],
                "current": f,
            }
        )
    projected_hsa = sum(
        (D(w["projected"]["hsa"]) + D(w["projected"]["employer_hsa"]) for w in workers), ZERO
    )
    hsa_limit = money(
        D(RULES["hsa_limit"][profile["hsa_coverage"]]) * D(profile["hsa_eligible_months"]) / 12
    )
    if projected_hsa and (
        not profile["hsa_eligibility_confirmed"] or profile["hsa_coverage"] == "none"
    ):
        raise ValueError(
            "HSA eligibility must be explicitly confirmed before modeling payroll tax exclusions"
        )
    if (
        profile["hsa_coverage"] == "self_only"
        and sum(D(w["projected"]["hsa"]) + D(w["projected"]["employer_hsa"]) > 0 for w in workers)
        > 1
    ):
        raise ValueError(
            "Separate self-only HSA eligibility for multiple workers is outside this household model"
        )
    if projected_hsa > hsa_limit:
        raise ValueError(
            "Projected employee plus employer HSA contributions exceed the eligible household HSA limit"
        )
    wages = sum((D(w["projected"]["federal_taxable"]) for w in workers), ZERO)
    agi = wages + D(profile["other_ordinary_income"])
    deduction = D(RULES["standard_deduction"][profile["filing_status"]])
    taxable = max(ZERO, agi - deduction)
    bands = bracket_breakdown(taxable, profile["filing_status"])
    before_credits = D(progressive_tax(taxable, profile["filing_status"]))
    tax = max(ZERO, before_credits - D(profile["nonrefundable_credits"]))
    ss = money(
        sum(
            (
                min(
                    D(w["projected"]["social_security_wages"]),
                    D(RULES["social_security"]["wage_base"]),
                )
                * D(RULES["social_security"]["rate"])
                for w in workers
            ),
            ZERO,
        )
    )
    med_wages = sum((D(w["projected"]["medicare_wages"]) for w in workers), ZERO)
    med = money(med_wages * D(RULES["medicare_rate"]))
    additional = money(
        max(ZERO, med_wages - D(RULES["additional_medicare"][profile["filing_status"]]))
        * D(RULES["additional_medicare"]["rate"])
    )
    withheld = sum((D(w["projected"]["federal_withholding"]) for w in workers), ZERO)
    add_withheld = sum(
        (
            D(w["additional_medicare_withholding_ytd"])
            + D(w["future_additional_medicare_withholding"])
            for w in workers
        ),
        ZERO,
    )
    settlement = tax + additional
    payments = withheld + add_withheld + D(profile["estimated_payments"])
    difference = settlement - payments
    safe = annual_safe_harbor(
        settlement,
        withheld + add_withheld,
        D(profile["estimated_payments"]),
        profile["prior_year_total_tax"],
        profile["prior_year_agi"],
        profile["prior_year_full_year_return"],
    )
    checks = sum(w["remaining_periods"] for w in workers)

    def per_check(total):
        return (
            format((total / D(checks)).quantize(Decimal(".01"), rounding=ROUND_CEILING), ".2f")
            if checks
            else None
        )

    return {
        "tax_year": 2026,
        "state": "TX",
        "rule_version": RULES["version"],
        "profile_revision": profile["revision"],
        "as_of": profile["as_of"],
        "filing_status": profile["filing_status"],
        "figures": {
            "projected_federal_wages": fmt(wages),
            "adjusted_gross_income": fmt(agi),
            "standard_deduction": fmt(deduction),
            "taxable_income": fmt(taxable),
            "federal_tax_before_credits": fmt(before_credits),
            "federal_income_tax": fmt(tax),
            "social_security_tax": fmt(ss),
            "medicare_tax": fmt(med),
            "additional_medicare_tax": fmt(additional),
            "federal_settlement_tax": fmt(settlement),
            "projected_federal_withholding": fmt(withheld),
            "projected_additional_medicare_withholding": fmt(add_withheld),
            "estimated_payments": profile["estimated_payments"],
            "balance_due": fmt(max(ZERO, difference)),
            "projected_refund": fmt(max(ZERO, -difference)),
            "settlement_difference": fmt(difference),
            "state_income_tax": "0.00",
            "projected_hsa_contributions": fmt(projected_hsa),
            "hsa_limit": fmt(hsa_limit),
        },
        "workers": workers,
        "brackets": bands,
        "safe_harbor": safe,
        "remaining_paychecks": checks,
        "suggested_extra_per_household_paycheck": per_check(max(ZERO, difference)),
        "safe_harbor_extra_per_household_paycheck": per_check(D(safe["shortfall"]))
        if safe["shortfall"] is not None
        else None,
        "sources": RULES["sources"],
        "completeness": "partial evidence",
        "assumptions": [
            "Synthetic demo unless you replace and explicitly confirm the inputs. Only the latest confirmed YTD record per employment is counted.",
            "Remaining paychecks repeat the latest reviewed regular wage bases and contribution rates. No future bonus, raise, equity, or job change is assumed.",
            "Texas has no individual state income tax. Property and sales taxes are separate expenses, not modeled income taxes.",
            "2026 full-year U.S. tax residents, single or married-filing-jointly W-2 workers aged 18–49, one employer per worker, standard deduction and confirmed nonrefundable credits only.",
            "Excludes AMT, NIIT, self-employment, capital gains, itemized/special deductions, refundable credits, retirement catch-ups, tips/overtime/car-interest special deductions, and tax filing.",
            "HSA limits include employer contributions, are prorated by confirmed eligible months, and do not apply the last-month rule. HSA changes are payroll cafeteria-plan contributions.",
            "401(k) elective contributions do not reduce Social Security or Medicare wages. Roth contributions do not reduce federal taxable income.",
            "Withholding is a tax payment, not a deduction or tax saving. Estimated-payment timing is not a penalty calculation.",
            "Bracket-schedule estimate rounded to cents; filed-return tax tables and whole-dollar conventions may differ. This is not a completed Form 1040 or W-4.",
        ],
    }


def validate_tax_projection(result):
    f = result["figures"]
    errors = []
    if (
        result["tax_year"] != RULES["tax_year"]
        or result["state"] != "TX"
        or result["rule_version"] != RULES["version"]
    ):
        errors.append("Unsupported tax-year, jurisdiction, or rule version")
    if D(f["state_income_tax"]) != 0:
        errors.append("Texas individual state income tax must be zero")
    sum_wages = sum((D(w["projected"]["federal_taxable"]) for w in result["workers"]), ZERO)
    if D(f["projected_federal_wages"]) != sum_wages:
        errors.append("Projected wage identity mismatch")
    for w in result["workers"]:
        current = w["current"]
        n = w["remaining_periods"]
        if D(w["projected"]["gross"]) != D(current["gross_ytd"]) + D(current["gross_current"]) * n:
            errors.append("Current/YTD gross identity mismatch")
    if D(f["federal_tax_before_credits"]) != sum((D(b["tax"]) for b in result["brackets"]), ZERO):
        errors.append("Bracket total mismatch")
    expected = (
        D(f["federal_income_tax"])
        + D(f["additional_medicare_tax"])
        - D(f["projected_federal_withholding"])
        - D(f["projected_additional_medicare_withholding"])
        - D(f["estimated_payments"])
    )
    if (
        D(f["settlement_difference"]) != expected
        or D(f["balance_due"]) != max(ZERO, expected)
        or D(f["projected_refund"]) != max(ZERO, -expected)
    ):
        errors.append("Federal settlement identity mismatch")
    return {
        "passed": not errors,
        "checks": [
            "current versus YTD identity",
            "bracket total",
            "federal settlement identity",
            "verified tax-year rule version",
        ],
        "errors": errors,
    }


def tax_strategy(conn, changes, user_id="demo"):
    c = TaxChanges.model_validate(changes)
    baseline = project_tax(conn, user_id=user_id)
    alternative = project_tax(conn, c.model_dump(mode="json"), user_id)
    selected = next(
        (w for w in baseline["workers"] if w["employment_key"] == c.employment_key), None
    )
    n = selected["remaining_periods"] if selected else 0
    contributions = (
        c.extra_traditional_per_check + c.extra_roth_per_check + c.extra_hsa_per_check
    ) * n
    income_saving = D(baseline["figures"]["federal_income_tax"]) - D(
        alternative["figures"]["federal_income_tax"]
    )
    payroll_saving = sum(
        (
            D(baseline["figures"][key]) - D(alternative["figures"][key])
            for key in ["social_security_tax", "medicare_tax", "additional_medicare_tax"]
        ),
        ZERO,
    )

    def future_withheld(result):
        return sum(
            (
                D(w[key])
                for w in result["workers"]
                for key in [
                    "future_ss_withholding",
                    "future_medicare_withholding",
                    "future_additional_medicare_withholding",
                ]
            ),
            ZERO,
        )

    immediate_fica_saving = future_withheld(baseline) - future_withheld(alternative)
    cash_cost = money(contributions + c.extra_withholding_per_check * n - immediate_fica_saving)
    monthly = (
        money(cash_cost / D(n) * D(selected["annual_periods"]) / 12) if selected and n else ZERO
    )
    if selected and n and cash_cost / D(n) > D(selected["current"]["net_pay_current"]):
        raise ValueError("Proposed deductions would exceed available take-home pay")
    reserve = D(alternative["figures"]["balance_due"])
    goals = simulate(
        Analytics(conn, user_id),
        {"extra_contributions": fmt(monthly), "cash_purchase": fmt(reserve)},
    )
    from .agents import validate_scenarios

    goal_validation = validate_scenarios([goals])
    goals["assumptions"] = [a for a in goals["assumptions"] if not a.startswith("Vehicle tax,")]
    return {
        "baseline": baseline,
        "alternative": alternative,
        "changes": c.model_dump(mode="json"),
        "comparison": {
            "additional_contributions": fmt(contributions),
            "federal_tax_savings": fmt(income_saving),
            "payroll_tax_savings": fmt(payroll_saving),
            "remaining_take_home_reduction": fmt(cash_cost),
            "monthly_take_home_reduction": fmt(monthly),
            "economic_after_tax_cost": fmt(contributions - income_saving - payroll_saving),
            "tax_reserve": fmt(reserve),
        },
        "goal_scenario": {"name": "Payroll changes + projected tax reserve", **goals},
        "validation": {
            "passed": validate_tax_projection(baseline)["passed"]
            and validate_tax_projection(alternative)["passed"]
            and goal_validation["passed"],
            "checks": validate_tax_projection(alternative)["checks"] + goal_validation["checks"],
            "errors": validate_tax_projection(baseline)["errors"]
            + validate_tax_projection(alternative)["errors"]
            + goal_validation["errors"],
        },
        "assumptions": alternative["assumptions"]
        + [
            "This scenario holds federal income withholding fixed except for explicit extra withholding. Real payroll may automatically recompute withholding after deductions change; obtain a payroll or IRS estimate for an actual next-paycheck forecast.",
            "Monthly cash impact is an average equivalent over remaining paychecks. The house timeline assumes this rate continues; tax estimates apply only to 2026.",
            "The goal simulator reserves the projected positive tax balance from existing cash and models net payroll cash reduction as extra allocations, not as an additional gross contribution. This avoids counting both gross contributions and their net cost.",
            "The tax reserve is earmarked immediately for planning; this is not a payment instruction or actual money movement.",
        ],
    }
