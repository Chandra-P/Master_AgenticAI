"""Optional bounded reviews. Models cannot calculate, alter facts, or authorize actions."""

import json
import os
import re
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ROLES = ("Evidence reviewer", "Constraint reviewer", "Assumption reviewer")
ROUTES = {"affordability", "scenario", "subscription_scenario", "goal_comparison", "tax"}
CONCERNS = Literal["missing_evidence", "constraints", "assumptions", "validation"]


class Vote(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    verdict: Literal["approve", "caution", "block"]
    concerns: list[CONCERNS] = Field(max_length=4)
    evidence_refs: list[str] = Field(min_length=1, max_length=12)


def evidence_packet(answer):
    # Deliberately omit all free-form user/document text and financial identifiers.
    facts = [
        {
            "ref": f"fact:{i}",
            "value": f["value"],
            "unit": f["unit"],
            "tool": f.get("source", "deterministic_fact"),
        }
        for i, f in enumerate(answer.get("facts", []))
    ]
    scenarios = [
        {
            "ref": f"scenario:{i}",
            "passed": s["passed"],
            "baseline": s.get("baseline", {}),
            "result": s.get("result", {}),
            "goal_impact": s.get("goal_impact", {}),
            "constraints": {k: c["passed"] for k, c in s["constraints"].items()},
        }
        for i, s in enumerate(answer.get("scenarios", []))
    ]
    refs = {f["ref"] for f in facts} | {s["ref"] for s in scenarios} | {"validation"}
    packet = {
        "route": answer["route"],
        "validation": answer["validation"]["passed"],
        "complete_evidence": answer["completeness"] == "complete evidence",
        "facts": facts,
        "scenarios": scenarios,
        "source_count": len(answer.get("sources", [])),
        "assumption_count": len(answer.get("assumptions", [])),
        "limitation_count": len(answer.get("limitations", [])),
    }
    return packet, refs


def live_vote(model, role, packet, refs):
    from openai import OpenAI

    response = OpenAI(timeout=8, max_retries=0).chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=250,
        messages=[
            {
                "role": "system",
                "content": f"You are FinPilot's {role}. Review only the supplied structured evidence. "
                "Never calculate money, infer missing facts, or authorize an action. "
                "This compact packet omits document passages, user intent and assumption text: "
                "you cannot verify semantic citation support or suitability. Use caution if that "
                "prevents your review. Failed validation or missing evidence requires block. "
                "Any failing scenario constraint requires caution or block. "
                "Return only the specified JSON schema. Cite supplied refs (validation is allowed).",
            },
            {"role": "user", "content": json.dumps(packet)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "council_review",
                "strict": True,
                "schema": Vote.model_json_schema(),
            },
        },
    )
    content = response.choices[0].message.content
    if not isinstance(content, str) or len(content) > 4096:
        raise ValueError("Invalid review payload")
    vote = Vote.model_validate_json(content)
    if not set(vote.evidence_refs) <= refs:
        raise ValueError("Unknown evidence reference")
    if vote.verdict == "approve" and vote.concerns:
        raise ValueError("Inconsistent approval")
    if vote.verdict != "approve" and not vote.concerns:
        raise ValueError("Missing concern")
    return vote.model_dump()


def review_council(answer, enabled=True):
    started = time.perf_counter()
    mode = os.getenv("COUNCIL_MODE", "off").lower() if enabled else "off"
    result = {
        "mode": mode,
        "status": "off",
        "reviews": [],
        "disagreement": False,
        "latency_ms": 0,
        "reconciliation": "Council disabled; deterministic validation remains authoritative.",
    }
    if mode == "off":
        return result
    if answer["route"] not in ROUTES:
        result.update(status="skipped", reconciliation="Simple question: no council review needed.")
        return result
    packet, refs = evidence_packet(answer)
    violations = any(
        not passed for s in packet["scenarios"] for passed in s["constraints"].values()
    )
    veto = not packet["validation"] or not packet["complete_evidence"] or violations
    models = [
        m.strip() for m in os.getenv("COUNCIL_MODELS", "gpt-4.1-mini,gpt-4.1,gpt-4o").split(",")
    ]
    configured = (
        mode in {"demo", "openai"}
        and len(models) == 3
        and all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}", m) for m in models)
        and (mode == "demo" or bool(os.getenv("OPENAI_API_KEY")))
    )
    for i, role in enumerate(ROLES):
        item = {
            "role": role,
            "model": "simulated policy"
            if mode == "demo"
            else models[i]
            if configured
            else "unconfigured",
            "simulated": mode == "demo",
            "verdict": "unavailable",
            "concerns": [],
            "evidence_refs": [],
            "error": None,
        }
        try:
            if not configured:
                raise ValueError("Council not configured")
            if mode == "demo":
                concerns = (
                    (["validation"] if not packet["validation"] else [])
                    + (["missing_evidence"] if not packet["complete_evidence"] else [])
                    + (["constraints"] if violations else [])
                )
                item.update(
                    verdict="block"
                    if not packet["validation"] or not packet["complete_evidence"]
                    else "caution"
                    if violations
                    else "approve",
                    concerns=concerns,
                    evidence_refs=["validation"],
                )
            else:
                item.update(live_vote(models[i], role, packet, refs))
        except Exception as exc:
            item["error"] = f"Review unavailable ({type(exc).__name__}); no simulated replacement."
        result["reviews"].append(item)
    verdicts = {r["verdict"] for r in result["reviews"] if r["verdict"] != "unavailable"}
    result["disagreement"] = len(verdicts) > 1
    unavailable = any(r["verdict"] == "unavailable" for r in result["reviews"])
    result["status"] = (
        "incomplete" if unavailable else "held" if veto or verdicts != {"approve"} else "approved"
    )
    result["reconciliation"] = {
        "incomplete": "Council incomplete. Do not treat the original analysis as council-approved.",
        "held": "Recommendation held for review. Resolve objections and constraint warnings; agreement cannot override deterministic checks.",
        "approved": "All reviewers accepted the compact evidence packet. This is not approval to act or professional financial advice.",
    }[result["status"]]
    result["latency_ms"] = round((time.perf_counter() - started) * 1000)
    return result
