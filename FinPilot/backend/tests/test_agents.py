import copy
import pytest
from finpilot.agents import run, classify, validate_scenarios
from finpilot.scenario import compare_car
from finpilot.analytics import Analytics


@pytest.mark.parametrize(
    "q,route",
    [
        ("How much did I spend last month?", "sql"),
        ("What APR does my uploaded car-loan offer show?", "rag"),
        ("What is my emergency-fund requirement?", "memory"),
        ("Can I afford this auto loan based on my current spending?", "affordability"),
        ("Why did my expenses increase this month?", "sql"),
        (
            "Would removing my selected subscriptions allow me to increase savings by $300 per month?",
            "subscription_scenario",
        ),
        ("Compare the loan offer to my current financial goals.", "goal_comparison"),
        ("Summarize my mortgage document.", "rag"),
        ("Can I afford it?", "clarification"),
    ],
)
def test_routing(q, route):
    assert classify(q) == route


def test_full_car_run(db):
    r = run(db, "Can I afford the $50,000 car in my current loan offer?")
    assert r["validation"]["passed"]
    assert len(r["scenarios"]) == 3
    assert {
        "get_cash_position",
        "get_monthly_cash_flow",
        "retrieve_documents",
        "get_user_memory",
        "simulate_scenario",
    } <= set(r["tools"])
    assert any(s["document_id"] == "auto-current" for s in r["sources"])
    assert r["completeness"] == "partial evidence"


def test_validator_rejects_mutation(db):
    scenarios = compare_car(Analytics(db), {"price": "50000", "apr": "6.49", "months": "60"})
    corrupt = copy.deepcopy(scenarios)
    corrupt[0]["result"]["remaining_cash"] = "999999.00"
    assert not validate_scenarios(corrupt)["passed"]
    corrupt = copy.deepcopy(scenarios)
    corrupt[0]["constraints"]["emergency_fund"]["passed"] = False
    assert not validate_scenarios(corrupt)["passed"]


def test_failure_and_abstention(db):
    r = run(db, "Can I afford this auto loan?", failure="database")
    assert r["completeness"] == "missing required data"
    assert not r["validation"]["passed"]
    assert not r["scenarios"]
    r = run(db, "Does my loan allow two skipped payments every year?")
    assert "not found" in r["summary"].lower()
    assert run(db, "How much did I spend at IKEA last month?")["facts"][0]["value"] is None


def test_affordability_summary_tracks_changed_constraints(db):
    db.execute("UPDATE user_preferences SET emergency_fund_minimum=5500000 WHERE user_id='demo'")
    result = run(db, "Can I afford the car in my current loan offer?", use_model=False)
    assert "0 of 2" in result["summary"]
    assert not any(s["constraints"]["emergency_fund"]["passed"] for s in result["scenarios"][:2])


def test_provenance_validator_rejects_fabricated_fact():
    from finpilot.agents import validate_facts

    output = {"value": "60000.00"}
    facts = [{"label": "Cash", "value": "99999", "source": "get_cash_position", "unit": "USD"}]
    assert not validate_facts(facts, [("get_cash_position", {}, output, 0)], [])["passed"]


def test_memory_summary_uses_confirmed_current_amount(db):
    db.execute("UPDATE user_preferences SET emergency_fund_minimum=3000000 WHERE user_id='demo'")
    result = run(db, "What is my emergency fund goal?", use_model=False)
    assert "$30000.00" in result["summary"]
    assert "current $25,000" not in result["summary"]
    assert result["validation"]["passed"]


def test_validator_rejects_unrelated_record_count():
    from finpilot.agents import validate_facts

    output = {"value": "60000.00", "included_record_count": 7}
    facts = [
        {"label": "Available cash", "value": "7", "source": "get_cash_position", "unit": "USD"}
    ]
    assert not validate_facts(facts, [("get_cash_position", {}, output, 0)], [])["passed"]


def test_long_uploaded_offer_cannot_hide_conflict(db):
    from finpilot.rag import ingest

    section = "SYNTHETIC auto loan offer\nVehicle price: $40,000\nAPR: 4.00%\nTerm: 60 months\nCan I afford the car in my current loan offer?"
    ingest(db, "Auto loan offer.txt", ("\n\n".join([section] * 7)).encode())
    result = run(db, "Can I afford the car in my current loan offer?", use_model=False)
    assert result["completeness"] == "missing required data"
    assert not result["scenarios"]
    assert "conflict" in result["summary"].lower()


def test_validator_recalculates_goal_timeline(db):
    scenarios = compare_car(Analytics(db), {"price": "50000", "apr": "6.49", "months": "60"})
    corrupt = copy.deepcopy(scenarios)
    corrupt[0]["goal_impact"]["projected_months"] = 8
    corrupt[0]["goal_impact"]["delay_months"] = 0
    corrupt[0]["constraints"]["house_goal"]["passed"] = True
    assert not validate_scenarios(corrupt)["passed"]


def test_failed_tool_is_visible_in_trace(db):
    result = run(db, "Can I afford this auto loan?", failure="database", use_model=False)
    assert any(
        e["tool"] == "get_cash_position" and e["status"] == "failed" for e in result["events"]
    )


def test_real_database_outage_still_returns_transparent_failure(db):
    db.close()
    result = run(db, "How much did I spend last month?", use_model=False)
    assert result["completeness"] == "missing required data"
    assert not result["validation"]["passed"]
    assert "unavailable" in result["tracing"]


@pytest.mark.parametrize(
    "question",
    [
        "Am I withholding enough federal tax?",
        "What do my paystubs imply for federal taxes?",
        "What if Alex increases traditional 401(k) by $250 per paycheck?",
    ],
)
def test_tax_route(question):
    assert classify(question) == "tax"


def test_tax_copilot_strategy_and_unsupported_scope(db):
    result = run(
        db, "What if Alex increases traditional 401(k) by $250 per paycheck?", use_model=False
    )
    assert result["validation"]["passed"]
    assert result["facts"][0]["value"] == "220.00"
    assert "simulate_tax_strategy" in result["tools"]
    assert result["sources"]
    missing = run(db, "Increase my traditional 401(k) by $250 per paycheck", use_model=False)
    assert missing["completeness"] == "missing required data"
    assert not missing["scenarios"]
    unsupported = run(db, "Calculate my 2025 federal tax", use_model=False)
    assert unsupported["completeness"] == "missing required data"


def test_tax_copilot_abstains_on_combined_strategy_types_with_one_amount(db):
    result = run(db, "Alex increase traditional 401k and HSA by $100 per paycheck", use_model=False)
    assert result["completeness"] == "missing required data"
    assert not result["scenarios"]
    assert "combined" in result["summary"].lower()
