from decimal import Decimal
import pytest
from finpilot.db import seed
from finpilot.analytics import Analytics
from finpilot.scenario import simulate, loan_payment


def test_seed_and_baseline(db):
    assert (
        db.execute("select count(distinct substr(posted_date,1,7)) from transactions").fetchone()[0]
        >= 6
    )
    a = Analytics(db)
    r = a.get_monthly_cash_flow("2026-10-01", "2026-11-01")
    assert r["income"] == "10000.00"
    assert r["expenses"] == "6000.00"
    assert r["surplus"] == "4000.00"
    seed(db)
    assert a.get_cash_position()["value"] == "60000.00"


def test_analytics_conventions(db):
    a = Analytics(db)
    assert (
        a.get_spending_by_merchant("Harbor Hotel", "2026-10-01", "2026-11-01")["value"] == "300.00"
    )
    assert (
        a.get_spending_by_category("2026-10-01", "2026-11-01", "Restaurants")["value"] == "650.00"
    )
    assert a.get_spending_by_merchant("IKEA", "2026-10-01", "2026-11-01")["value"] is None
    purchases = a.get_largest_purchases("2026-10-01", "2026-11-01")["items"]
    assert len(purchases) == 5
    assert [Decimal(x["amount"]) for x in purchases] == sorted(
        [Decimal(x["amount"]) for x in purchases], reverse=True
    )
    assert a.calculate_savings_rate("2026-10-01", "2026-11-01")["value"] == "40.00"
    assert a.get_total_income("2026-08-01", "2026-11-01")["value"] == "30000.00"
    assert a.find_recurring_subscriptions()["value"] == "250.00"
    assert a.calculate_savings_rate("2025-01-01", "2025-02-01")["value"] is None


@pytest.mark.parametrize(
    "changes,key,expected",
    [
        ({"monthly_payment": "600"}, "monthly_surplus", "3400.00"),
        ({"down_payment": "15000"}, "remaining_cash", "45000.00"),
        ({"cash_purchase": "40000"}, "remaining_cash", "20000.00"),
        ({"income_reduction_pct": "20"}, "monthly_income", "8000.00"),
        (
            {"cancel_subscription_ids": ["stream", "gym", "cloud", "music", "news"]},
            "monthly_surplus",
            "4250.00",
        ),
        (
            {
                "monthly_payment": "600",
                "cancel_subscription_ids": ["stream", "gym", "cloud", "music", "news"],
                "extra_contributions": "300",
            },
            "monthly_surplus",
            "3350.00",
        ),
    ],
)
def test_scenarios(db, changes, key, expected):
    assert simulate(Analytics(db), changes)["result"][key] == expected


def test_constraints_and_idempotence(db):
    a = Analytics(db)
    assert simulate(a, {"cash_purchase": "35000"})["constraints"]["emergency_fund"]["passed"]
    assert not simulate(a, {"cash_purchase": "40000"})["constraints"]["emergency_fund"]["passed"]
    assert not simulate(a, {"cash_purchase": "100000"})["constraints"]["emergency_fund"]["passed"]
    assert simulate(a, {"income_reduction_pct": "100"})["result"]["monthly_surplus"] == "-6000.00"
    assert simulate(a, {"monthly_payment": "600"}) == simulate(a, {"monthly_payment": "600"})
    with pytest.raises(ValueError, match="APR"):
        loan_payment(Decimal("50000"), None, 60)
    assert loan_payment(Decimal("36000"), Decimal("0"), 60) == Decimal("600.00")


def test_boundaries_and_zero_income(db):
    a = Analytics(db)
    assert a.get_total_income("2026-10-01", "2026-10-15")["value"] == "5000.00"
    assert a.get_total_income("2026-10-15", "2026-11-01")["value"] == "5000.00"
    assert (
        a.get_spending_by_merchant("COSTCO.COM", "2026-01-01", "2027-01-01")["value"] == "2400.00"
    )
    db.execute("UPDATE transactions SET amount=0 WHERE category='Income'")
    assert a.calculate_savings_rate("2026-10-01", "2026-11-01")["value"] is None
    with pytest.raises(ValueError):
        a.get_spending_by_category("2026-11-01", "2026-10-01")


def test_allocations_and_subscription_validation(db):
    a = Analytics(db)
    result = simulate(a, {"down_payment": "20000"})
    assert result["result"]["house_savings"] == "15000.00"
    assert result["baseline"]["unallocated_cash"] == "15000.00"
    assert (
        simulate(a, {"cancel_subscription_ids": ["stream", "stream"]})["result"][
            "subscription_savings"
        ]
        == "80.00"
    )
    with pytest.raises(ValueError):
        simulate(a, {"cancel_subscription_ids": ["unknown"]})


def test_annual_subscription_equivalent_is_not_posted_spending(db):
    db.execute(
        "INSERT INTO recurring_transactions VALUES('annual','demo','Annual plan',12000,'annual',1,'synthetic annual schedule')"
    )
    a = Analytics(db)
    assert a.find_recurring_subscriptions()["value"] == "260.00"
    assert (
        a.get_spending_by_category("2026-10-01", "2026-11-01", "Subscriptions")["value"] == "250.00"
    )


def test_fractional_cent_inputs_are_rejected(db):
    with pytest.raises(ValueError):
        simulate(Analytics(db), {"down_payment": "0.005"})


def test_conflicting_cash_earmarks_are_visible(db):
    db.execute("UPDATE user_preferences SET emergency_fund_minimum=5500000 WHERE user_id='demo'")
    result = simulate(Analytics(db), {})
    assert not result["constraints"]["earmarked_cash"]["passed"]
    assert not result["passed"]


def test_monthly_subscriptions_require_repeated_posted_evidence(db):
    db.execute(
        "INSERT INTO recurring_transactions VALUES('oneoff','demo','One-time service',1500,'monthly',1,'unverified import')"
    )
    result = Analytics(db).find_recurring_subscriptions()
    assert "oneoff" not in {r["id"] for r in result["items"]}
    assert all(r["observed_months"] >= 3 for r in result["items"] if r["frequency"] == "monthly")
