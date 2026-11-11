import inspect
import subprocess
from collections import defaultdict
from pathlib import Path
from statistics import median, quantiles
from time import perf_counter

from ..contracts import digest
from ..narrative import offline_narrative
from ..openai_adapter import NarrativeContractError
from .graders import grade_output
from .oracle import oracle_result


class EvaluationBlocked(ValueError):
    """Safe pre-invocation configuration/budget block, not a successful attempt."""


def _revision():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def _implementation_hash():
    root = Path(__file__).parent
    files = list(root.glob("*.py")) + [
        root.parent / name for name in ("openai_adapter.py", "tools.py", "compute.py")
    ]
    return digest({p.name: p.read_text(encoding="utf-8") for p in sorted(files)})


def run_experiment(
    store,
    cases,
    *,
    dataset_hash,
    mode="offline",
    target=None,
    repetitions=1,
    experiment_id=None,
    candidate_id="offline-baseline",
    model="offline",
    split="development",
    allow_heldout=False,
):
    cases = tuple(cases)
    if not cases or mode not in ("offline", "replay", "live") or not 1 <= repetitions <= 5:
        raise ValueError("invalid experiment")
    if any(c.split != split for c in cases):
        raise ValueError("experiment cannot mix dataset splits")
    if split == "test" and (not allow_heldout or not candidate_id or candidate_id == "offline-baseline"):
        raise PermissionError("locked test requires explicit selected candidate and exposure")
    if mode != "offline" and target is None:
        raise ValueError("replay/live requires an explicit target")
    metadata = {
        "dataset_hash": dataset_hash,
        "case_hash": digest([c.model_dump() for c in cases]),
        "mode": mode,
        "repetitions": repetitions,
        "candidate_id": candidate_id,
        "model": model,
        "split": split,
        "test_exposure": split == "test",
        "code_revision": _revision(),
        "implementation_hash": _implementation_hash(),
        "prompt_hash": digest(inspect.getsource(offline_narrative))
        if mode == "offline"
        else getattr(target, "prompt_hash", "unspecified"),
        "rubric_version": "reporting-rubric-v1",
        "grader_version": "reporting-code-v1",
        "sampling": {"live_temperature": "provider-default", "seed": None},
    }
    identity = store.create(metadata, cases, experiment_id)
    if target is not None and hasattr(target, "run_id"):
        target.run_id = identity
    for case in cases:
        for repetition in range(repetitions):
            if not store.claim(identity, case.case_id, repetition):
                continue  # Includes ambiguous interrupted attempts: never automatically reissue.
            started = perf_counter()
            store.start(identity, case.case_id, repetition)
            result = {
                "status": "completed",
                "started": True,
                "checks": [],
                "output": None,
                "cost_usd": 0 if mode != "live" else None,
                "input_tokens": None,
                "output_tokens": None,
                "source": mode,
                "cached": mode == "replay",
            }
            try:
                if case.task == "oracle":
                    output = oracle_result(case)
                    result["source"] = "deterministic_oracle"
                    result["cost_usd"] = 0
                elif mode == "offline":
                    output = offline_narrative({}, {"correction": case.facts.correction})
                else:
                    output = target(case)
                checks = grade_output(case, output)
                result["checks"] = [c.model_dump() for c in checks]
                result["output_hash"] = digest(output)
                # Unsafe/malformed bodies are discarded before persistence/export.
                if not any(c.severity == "critical" and c.status == "fail" for c in checks):
                    result["output"] = output
                result["requires_human"] = any(c.status == "needs_review" for c in checks)
            except NarrativeContractError:
                result.update(
                    status="error",
                    error_category="NarrativeContractError",
                    checks=[
                        {
                            "name": "live_output_contract",
                            "kind": "contract",
                            "status": "fail",
                            "severity": "critical",
                        }
                    ],
                )
            except EvaluationBlocked:
                result.update(
                    status="blocked", started=False, cost_usd=0, error_category="ConfigurationOrBudgetBlocked"
                )
            except Exception as exc:  # noqa: BLE001 -- persist categories, never unrestricted provider messages
                result.update(status="error", error_category=type(exc).__name__)
            except BaseException as exc:
                result.update(status="interrupted", error_category=type(exc).__name__)
                raise
            finally:
                usage = (
                    getattr(target, "last_usage", {}) if case.task == "narrative" and mode == "live" else {}
                )
                for key in ("cost_usd", "input_tokens", "output_tokens"):
                    if key in usage:
                        result[key] = usage[key]
                result["duration_ms"] = round((perf_counter() - started) * 1000, 3)
                store.finish(identity, case.case_id, repetition, result)
    return identity


def _passes(row):
    checks = row["result"].get("checks", [])
    if row["status"] != "completed" or not checks:
        return None
    if any(c["status"] == "fail" for c in checks):
        return False
    if row["case"]["task"] == "oracle":
        return True
    annotation = row["annotation"]
    if not annotation:
        return None
    return bool(
        annotation["accepted"]
        and not annotation["critical_violation"]
        and annotation["factual_support"] >= 4
        and annotation["completeness"] >= 4
        and annotation["usefulness"] >= 3
        and annotation["clarity"] >= 3
    )


def summarize(store, identity, actor=None):
    meta, rows = store.metadata(identity), store.rows(identity, actor)
    groups = defaultdict(list)
    for row in rows:
        groups[row["case"]["case_id"]].append(row)
    complete, passed = [], []
    for case_id, records in groups.items():
        if len(records) == meta["repetitions"] and all(_passes(r) is not None for r in records):
            complete.append(case_id)
            if all(_passes(r) for r in records):
                passed.append(case_id)
    critical = sum(
        any(c["severity"] == "critical" and c["status"] == "fail" for c in r["result"].get("checks", []))
        or bool(r["annotation"] and r["annotation"]["critical_violation"])
        for r in rows
    )
    attempts = [r for r in rows if r["repetition"] is not None]
    started = [r for r in attempts if r["started"]]
    success = [r for r in started if r["status"] == "completed"]
    latency = [r["result"]["duration_ms"] for r in success]
    cost_values = [r["result"].get("cost_usd") for r in attempts]
    total = sum(float(c) for c in cost_values if c is not None)
    coverage = len(complete) / len(groups) if groups else 0
    quality = len(passed) / len(complete) if complete else None
    live_narratives = [k for k, g in groups.items() if g[0]["case"]["task"] == "narrative" and k in complete]
    live_passes = sum(k in passed for k in live_narratives)
    gate = "blocked" if critical else "unevaluated"
    # Promotion also requires frozen-set paired comparison, checked separately.
    by_task = {}
    for task in ("narrative", "oracle"):
        keys = [k for k, g in groups.items() if g[0]["case"]["task"] == task]
        by_task[task] = {
            "scheduled_cases": len(keys),
            "evaluated_cases": sum(k in complete for k in keys),
            "passed_cases": sum(k in passed for k in keys),
        }
    slices = {}
    for dimension in ("client_id", "year", "period", "tags"):
        buckets = defaultdict(set)
        for key, records in groups.items():
            value = records[0]["case"][dimension]
            for label in value if dimension == "tags" else (str(value),):
                buckets[label].add(key)
        slices[dimension] = {
            label: {
                "scheduled_cases": len(keys),
                "evaluated_cases": len(keys & set(complete)),
                "passed_cases": len(keys & set(passed)),
            }
            for label, keys in sorted(buckets.items())
        }
    reviewed = [r["annotation"] for r in rows if r["annotation"]]
    dimension_scores = {
        name: {
            "reviewed_attempts": len(reviewed),
            "mean": sum(a[name] for a in reviewed) / len(reviewed) if reviewed else None,
        }
        for name in ("factual_support", "completeness", "usefulness", "clarity")
    }
    repeated = [
        g
        for g in groups.values()
        if meta["repetitions"] > 1
        and len(g) == meta["repetitions"]
        and all(_passes(r) is not None for r in g)
    ]
    return {
        "experiment_id": identity,
        "mode": meta["mode"],
        "split": meta["split"],
        "scheduled_cases": len(groups),
        "fully_evaluated_cases": len(complete),
        "passed_cases": len(passed),
        "coverage": coverage,
        "completed_case_quality": quality,
        "live_quality_rate": live_passes / len(live_narratives)
        if meta["mode"] == "live" and live_narratives
        else None,
        "attempts_started": len(started),
        "reliability": len(success) / len(started) if started else None,
        "blocked_attempts": sum(r["status"] == "blocked" for r in attempts),
        "error_attempts": sum(r["status"] == "error" for r in attempts),
        "unresolved_attempts": sum(r["status"] in ("claimed", "interrupted") for r in attempts),
        "unreviewed_attempts": sum(
            r["case"]["task"] == "narrative" and r["status"] == "completed" and not r["annotation"]
            for r in attempts
        ),
        "critical_failures": critical,
        "actual_cost_usd": total,
        "unknown_cost_attempts": sum(c is None for c in cost_values),
        "latency_p50_ms": median(latency) if latency else None,
        "latency_p95_ms": quantiles(latency, n=100, method="inclusive")[94] if len(latency) >= 2 else None,
        "release_gate": gate,
        "by_task": by_task,
        "slices": slices,
        "dimension_scores": dimension_scores,
        "repetition_stability": {
            "evaluated_cases": len(repeated),
            "consistent_pass_fail_cases": sum(len({_passes(r) for r in g}) == 1 for g in repeated),
        },
        "limitations": [
            "Synthetic cases only.",
            "Offline/replay runs do not measure live-model accuracy.",
            "Promotion requires a reviewed paired frozen-test comparison; unresolved semantics never pass.",
        ],
    }


def compare_experiments(store, baseline_id, candidate_id, actor=None, oracle_id=None):
    a, b = store.metadata(baseline_id), store.metadata(candidate_id)
    if any(a[k] != b[k] for k in ("dataset_hash", "case_hash", "split", "repetitions")):
        raise ValueError("paired comparison requires identical cases, dataset, split and repetition protocol")
    left = {(r["case"]["case_id"], r["repetition"]): r for r in store.rows(baseline_id, actor)}
    right = {(r["case"]["case_id"], r["repetition"]): r for r in store.rows(candidate_id, actor)}
    comparable, regressions, improvements = 0, [], []
    for key in left.keys() & right.keys():
        x, y = _passes(left[key]), _passes(right[key])
        if x is None or y is None:
            continue
        comparable += 1
        if x and not y:
            regressions.append(key[0])
        elif y and not x:
            improvements.append(key[0])
    critical = summarize(store, candidate_id, actor)["critical_failures"]
    expected_keys = {(case_id, rep) for case_id in {k[0] for k in left} for rep in range(a["repetitions"])}
    all_reviewed = (
        set(left) == set(right) == expected_keys and comparable == len(expected_keys) and bool(left)
    )
    failed_candidate = any(_passes(row) is False for row in right.values())
    oracle_ok = False
    if oracle_id is not None:
        from .dataset import edge_cases

        oracle_meta = store.metadata(oracle_id)
        required = {c.case_id: c.model_dump(mode="json") for c in edge_cases() if c.task == "oracle"}
        oracle_rows = [r for r in store.rows(oracle_id) if r["case"]["task"] == "oracle"]
        oracle_ok = (
            actor is None
            and oracle_meta["dataset_hash"] == b["dataset_hash"]
            and oracle_meta["implementation_hash"] == b["implementation_hash"]
            and {r["case"]["case_id"] for r in oracle_rows} == set(required)
            and all(r["case"] == required[r["case"]["case_id"]] and _passes(r) is True for r in oracle_rows)
            and summarize(store, oracle_id)["by_task"]["oracle"]["evaluated_cases"] == len(required)
        )
    gate = "blocked" if critical or regressions or failed_candidate else "unevaluated"
    if (
        all_reviewed
        and oracle_ok
        and not critical
        and not regressions
        and not failed_candidate
        and a["mode"] == b["mode"] == "live"
        and a["split"] == "test"
        and a["repetitions"] >= 3
        and actor is None
        and any(r["case"]["task"] == "narrative" for r in right.values())
        and summarize(store, candidate_id)["unknown_cost_attempts"] == 0
        and summarize(store, baseline_id)["unknown_cost_attempts"] == 0
        and all(r["status"] == "completed" for r in right.values())
    ):
        gate = "eligible_for_human_release_review"
    return {
        "baseline": baseline_id,
        "candidate": candidate_id,
        "comparable_attempts": comparable,
        "regressed_cases": sorted(set(regressions)),
        "improved_cases": sorted(set(improvements)),
        "release_gate": gate,
        "paired_labels_complete": all_reviewed,
        "oracle_gate_passed": oracle_ok,
    }


def public_summary(store, identity, actor=None):
    """Allowlist only aggregate experiment evidence; excludes outputs, inputs and human notes."""
    summary = summarize(store, identity, actor)
    return {
        k: summary[k]
        for k in (
            "experiment_id",
            "mode",
            "split",
            "scheduled_cases",
            "fully_evaluated_cases",
            "coverage",
            "live_quality_rate",
            "critical_failures",
            "actual_cost_usd",
            "unknown_cost_attempts",
            "release_gate",
        )
    }
