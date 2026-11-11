from campaign_reporting.openai_adapter import build_narrative_input


def test_report_tools_supply_confirmed_goals(tmp_path):
    from campaign_reporting.contracts import CampaignConfig
    from campaign_reporting.repository import ActorContext, Repository
    from campaign_reporting.runs import prepare_run
    from campaign_reporting.tools import ReportTools

    repo = Repository.local(tmp_path / "report.sqlite")
    cfg = CampaignConfig()
    run = prepare_run(repo, cfg)
    tools = ReportTools(repo, ActorContext("reviewer", cfg.client_id, "review"))
    payload = build_narrative_input(tools.get_metrics(run["run_id"]), tools.get_flag_status(run["run_id"]))
    assert "status_flags" in payload


def test_live_contract_failure_is_sanitized_and_critical(tmp_path):
    from campaign_reporting.evaluation.dataset import edge_cases
    from campaign_reporting.evaluation.results import EvaluationStore
    from campaign_reporting.evaluation.runner import run_experiment, summarize
    from campaign_reporting.openai_adapter import NarrativeContractError

    def target(case):
        raise NarrativeContractError()

    store = EvaluationStore(tmp_path / "eval.sqlite")
    exp = run_experiment(store, edge_cases()[:1], dataset_hash="fixed", mode="live", target=target)
    assert summarize(store, exp)["critical_failures"] == 1
    assert summarize(store, exp)["release_gate"] == "blocked"


def test_only_aggregate_facts_and_deterministic_goal_flags_enter_prompt():
    metrics = {
        "periods": {
            "30": {
                "checking_accounts": 550,
                "new_members": 650,
                "forecast": 620,
                "forecast_low": 580,
                "forecast_high": 670,
                "cpa": None,
                "member_name": "PRIVATE_CANARY",
            }
        },
        "goals": {"checking": 601, "members": 605},
        "secret": "PRIVATE_CANARY",
    }
    result = build_narrative_input(metrics, {"correction": False})
    assert result["status_flags"]["30"]["checking_goal"] == "below"
    assert result["status_flags"]["30"]["member_goal"] == "met"
    assert result["status_flags"]["30"]["cpa"] == "unavailable"
    assert "PRIVATE_CANARY" not in str(result)
