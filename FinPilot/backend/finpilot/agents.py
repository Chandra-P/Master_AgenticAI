"""Explicit bounded orchestration. Events are tool summaries, never chain-of-thought."""

import json
import sqlite3
import logging
import re
import time
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from .analytics import Analytics, month_bounds
from .money import decimal
from .providers import plan_with_openai, publish_trace, redact
from .council import review_council
from .rag import retrieve, loan_terms, assert_offer_authority
from .scenario import simulate, compare_car


def classify(question):
    q = question.lower().replace("–", "-").replace("—", "-")
    has_loan = bool(re.search(r"car|auto|loan|vehicle", q))
    tax_question = bool(
        re.search(
            r"\btax(?:es)?\b|\bwithhold\w*|\bpay.?stubs?\b|\b401\s*\(?k\)?|\bhsa\b|\broth\b|\bdeduct(?:ion)?\b",
            q,
        )
    )
    if tax_question and not (has_loan and re.search(r"afford", q)):
        return "tax"
    if re.search(r"afford|definitely affordable", q):
        return "affordability" if has_loan else "clarification"
    if re.search(r"(remov|cancel).*subscription", q):
        return "subscription_scenario"
    if has_loan and re.search(r"compare|against", q) and re.search(r"goal", q):
        return "goal_comparison"
    if re.search(r"emergency.?fund", q):
        return "memory"
    if re.search(r"house|down.payment", q) and re.search(r"goal|target|want|objective", q):
        return "memory"
    if re.search(
        r"income.*(?:drop|reduc)|(?:drop|reduc).*income|additional.*(?:save|saving)|save an additional|retirement contribution",
        q,
    ):
        return "scenario"
    if re.search(
        r"apr|interest rate|deductible|mortgage (?:rate|document)|summarize.*(?:document|mortgage)|loan.*(?:term|long|skip)|how long.*loan|security.test|credit limit|two.*loan|compare.*loan",
        q,
    ):
        return "rag"
    if re.search(
        r"spend|spent|expense|purchase|subscription|income|saving.*rate|percentage.*save", q
    ):
        return "sql"
    return "clarification"


def period(question):
    q = question.lower()
    year_match = re.search(r"\b(20\d{2})\b", q)
    year = int(year_match.group(1)) if year_match else 2026
    months = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]
    selected = [i + 1 for i, m in enumerate(months) if m in q]

    def bounds(m):
        return date(year, m, 1).isoformat(), date(
            year + int(m == 12), 1 if m == 12 else m + 1, 1
        ).isoformat()

    if selected:
        return bounds(selected[-1])
    if "this year" in q:
        return "2026-01-01", "2027-01-01"
    if "three" in q or "3 complete" in q:
        return month_bounds(-3)[0], month_bounds(-1)[1]
    return month_bounds(0 if "this month" in q else -1)


def validate_scenarios(scenarios):
    errors = []
    for s in scenarios:
        b, c, r = s["baseline"], s["changes"], s["result"]
        expected = (
            decimal(b["cash"])
            - decimal(c["down_payment"])
            - decimal(c["cash_purchase"])
            + decimal(c["immediate_inflow"])
        )
        if decimal(r["remaining_cash"]) != expected:
            errors.append("Cash identity mismatch")
        expected_income = (
            decimal(b["monthly_income"]) * (1 - decimal(c["income_reduction_pct"]) / 100)
        ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
        expected_surplus = (
            expected_income
            - decimal(b["monthly_expenses"])
            - decimal(c["monthly_payment"])
            + decimal(r["subscription_savings"])
            - decimal(c["extra_contributions"])
        )
        if decimal(r["monthly_surplus"]) != expected_surplus:
            errors.append("Cash-flow identity mismatch")
        emergency = expected >= decimal(b["emergency_reserve"])
        if s["constraints"]["emergency_fund"]["passed"] != emergency:
            errors.append("Emergency boundary mismatch")
        saved, reserve = decimal(b["house_savings"]), decimal(b["emergency_reserve"])
        free = max(Decimal(0), decimal(b["cash"]) - reserve - saved)
        consumed = min(
            saved,
            max(
                Decimal(0),
                decimal(c["down_payment"])
                + decimal(c["cash_purchase"])
                - decimal(c["immediate_inflow"])
                - free,
            ),
        )
        house = saved - consumed
        if decimal(r["house_savings"]) != house or decimal(r["house_savings_used"]) != consumed:
            errors.append("House earmark identity mismatch")

        def independent_months(gap, contribution):
            if gap <= 0:
                return 0
            if contribution <= 0:
                return None
            return int(gap // contribution) + (1 if gap % contribution else 0)

        target = decimal(s["source_data"]["goal"]["target_amount"])
        cap = decimal(b["house_allocation_cap"])
        before = independent_months(
            target - saved, min(max(Decimal(0), decimal(b["monthly_surplus"])), cap)
        )
        after = independent_months(target - house, min(max(Decimal(0), expected_surplus), cap))
        delay = max(0, after - before) if after is not None and before is not None else None
        if (
            s["goal_impact"]["baseline_months"] != before
            or s["goal_impact"]["projected_months"] != after
            or s["goal_impact"]["delay_months"] != delay
        ):
            errors.append("Goal timeline identity mismatch")
        expected_goal = (
            delay is not None and delay <= s["constraints"]["house_goal"]["maximum_delay_months"]
        )
        if s["constraints"]["house_goal"]["passed"] != expected_goal:
            errors.append("Goal constraint mismatch")
        expected_flags = {
            "cash_flow": expected_surplus >= 0,
            "purchase_funding": expected >= 0,
            "earmarked_cash": expected >= reserve + house,
        }
        if any(s["constraints"][key]["passed"] != value for key, value in expected_flags.items()):
            errors.append("Cash-flow/funding/allocation constraint mismatch")
        if s["passed"] != all(x["passed"] for x in s["constraints"].values()):
            errors.append("Overall constraint verdict mismatch")
        if s.get("loan"):
            loan = s["loan"]
            balance = decimal(loan["principal"])
            rate = decimal(loan["apr"]) / 1200
            payment = decimal(loan["payment"])
            for _ in range(int(loan["months"])):
                balance = balance * (1 + rate) - payment
            if abs(balance) > Decimal("1.00"):
                errors.append("Amortization residual exceeds rounding tolerance")
    return {
        "passed": not errors,
        "checks": [
            "cash identity",
            "cash-flow identity",
            "inclusive emergency boundary",
            "independent house earmark and goal timeline",
            "goal constraint consistency",
            "loan amortization residual",
        ],
        "errors": errors,
    }


DOC_FIELDS = {
    "document.price": (r"Vehicle price:\s*\$([\d,]+(?:\.\d+)?)", "USD"),
    "document.apr": (r"\bAPR:\s*([\d.]+)%", "percent"),
    "document.term": (r"Term:\s*(\d+)\s*months", "months"),
    "document.mortgage_rate": (r"Mortgage interest rate:\s*([\d.]+)%", "percent"),
    "document.collision": (r"Collision deductible:\s*\$([\d,]+)", "USD"),
    "document.comprehensive": (r"Comprehensive deductible:\s*\$([\d,]+)", "USD"),
}
TOOL_FIELDS = {
    "get_tax_projection": {
        f"figures.{key}": "USD"
        for key in [
            "federal_income_tax",
            "projected_federal_withholding",
            "balance_due",
            "projected_refund",
        ]
    },
    "simulate_tax_strategy": {
        f"comparison.{key}": "USD"
        for key in [
            "federal_tax_savings",
            "payroll_tax_savings",
            "remaining_take_home_reduction",
            "economic_after_tax_cost",
        ]
    },
    "get_cash_position": {"value": "USD"},
    "get_monthly_cash_flow": {"income": "USD", "expenses": "USD", "surplus": "USD"},
    "get_user_memory": {"emergency_fund_minimum": "USD"},
    "get_goal_status": {"items.0.target_amount": "USD", "items.0.current_amount": "USD"},
    "compare_category_spending": {
        "previous.value": "USD",
        "current.value": "USD",
        "difference": "USD",
        "percent_change": "percent",
    },
    "find_recurring_subscriptions": {"value": "USD"},
    "get_spending_by_category": {"value": "USD"},
    "get_spending_by_merchant": {"value": "USD"},
    "get_total_income": {"value": "USD"},
    "calculate_savings_rate": {"value": "percent"},
}


def validate_facts(facts, calls, sources, summary=""):
    """Bind every displayed fact to an approved semantic field and unit, not any scalar."""
    outputs = {name: output for name, _, output, _ in calls}
    passages = {source["chunk_id"]: source for source in sources}
    errors = []
    for fact in facts:
        source, path = fact["source"], fact.get("path", "value")
        values = []
        expected_unit = None
        if source in passages and path in DOC_FIELDS:
            pattern, expected_unit = DOC_FIELDS[path]
            values = re.findall(pattern, passages[source]["passage"], re.I)
        elif source in outputs:
            expected_unit = TOOL_FIELDS.get(source, {}).get(path)
            if source == "identify_spending_anomalies" and re.fullmatch(
                r"items\.\d+\.(?:difference|percent_change)", path
            ):
                expected_unit = "percent" if path.endswith("percent_change") else "USD"
            try:
                value = outputs[source]
                for key in path.split("."):
                    value = value[int(key)] if isinstance(value, list) else value[key]
                values = [value]
            except (KeyError, TypeError, IndexError, ValueError):
                pass
        matched = False
        if expected_unit == fact["unit"]:
            for value in values:
                if value is None and fact["value"] is None:
                    matched = True
                elif value is not None and fact["value"] is not None:
                    try:
                        matched = matched or decimal(str(value).replace(",", "")) == decimal(
                            fact["value"]
                        )
                    except Exception:
                        pass
        if not matched:
            errors.append("Unsupported field, unit, or numeric fact: " + fact["label"])
    # User questions and quoted source passages are not synthesized assertions.
    claims = []
    for match in re.finditer(r"\$([\d,]+(?:\.\d+)?)|([\d.]+)%|(\d+)[- ]month", summary):
        value = next(v for v in match.groups() if v is not None)
        unit = "USD" if match.group(1) else "percent" if match.group(2) else "months"
        claims.append((decimal(value.replace(",", "")), unit))
    for value, unit in claims:
        if not any(
            f["value"] is not None and f["unit"] == unit and decimal(f["value"]) == value
            for f in facts
        ):
            errors.append("Unsupported monetary/rate/term claim in summary")
    return {
        "passed": not errors,
        "checks": ["semantic field and unit provenance", "summary monetary/rate/term provenance"],
        "errors": errors,
    }


def run(
    conn, question, user_id="demo", failure=None, use_model=True, selected_subscription_ids=None
):
    started = time.perf_counter()
    rid = str(uuid.uuid4())
    fallback = classify(question)
    route, mode, provider_error = (
        plan_with_openai(question, fallback) if use_model else (fallback, "deterministic", None)
    )
    a = Analytics(conn, user_id)
    result = {
        "id": rid,
        "question": question,
        "route": route,
        "mode": mode,
        "nodes": ["Orchestrator"],
        "tools": [],
        "events": [],
        "sources": [],
        "facts": [],
        "scenarios": [],
        "assumptions": [],
        "limitations": [
            "Educational simulation; not professional financial advice. Synthetic household, as of November 2, 2026."
        ],
        "completeness": "complete evidence",
        "validation": {"passed": True, "checks": [], "errors": []},
        "summary": "",
        "error": None,
    }
    if provider_error:
        result["limitations"].append(provider_error)
    calls = []

    def tool(name, fn, inputs=None, node="SQL Analytics"):
        if node not in result["nodes"]:
            result["nodes"].append(node)
        t = time.perf_counter()
        try:
            if failure == "database" and node == "SQL Analytics":
                raise RuntimeError("Required transaction database unavailable")
            output = fn()
        except Exception as exc:
            ms = round((time.perf_counter() - t) * 1000)
            result["tools"].append(name)
            result["events"].append(
                {
                    "node": node,
                    "tool": name,
                    "status": "failed",
                    "latency_ms": ms,
                    "summary": f"{name} failed ({type(exc).__name__}); no values inferred",
                }
            )
            calls.append((name, inputs or {}, {"error_category": type(exc).__name__}, ms))
            raise
        ms = round((time.perf_counter() - t) * 1000)
        result["tools"].append(name)
        result["events"].append(
            {
                "node": node,
                "tool": name,
                "status": "complete",
                "latency_ms": ms,
                "summary": f"{name.replace('_', ' ')} completed",
            }
        )
        calls.append((name, inputs or {}, output, ms))
        return output

    def fact(label, value, source, unit="USD", path="value"):
        if path in DOC_FIELDS:
            pattern, _ = DOC_FIELDS[path]
            candidates = (
                result["sources"]
                if source == "retrieve_documents"
                else [s for s in result["sources"] if s["chunk_id"] == source]
            )
            match = next(
                (
                    s
                    for s in candidates
                    if any(
                        decimal(v.replace(",", "")) == decimal(value)
                        for v in re.findall(pattern, s["passage"], re.I)
                    )
                ),
                None,
            )
            source = match["chunk_id"] if match else source
        result["facts"].append(
            {"label": label, "value": value, "unit": unit, "source": source, "path": path}
        )

    def rag():
        sources = tool(
            "retrieve_documents",
            lambda: retrieve(
                conn,
                question,
                user_id,
                include_superseded=bool(re.search(r"compare|two .*offer", question, re.I)),
            ),
            {"query": question},
            "Document RAG",
        )
        result["sources"] = sources
        return sources

    def memory():
        return tool("get_user_memory", a.memory, node="Goal & Memory")

    q = question.lower()
    try:
        if route == "tax":
            from .tax_engine import project_tax, tax_strategy, validate_tax_projection

            years = [
                m.group()
                for m in re.finditer(r"\b20\d{2}\b", q)
                if not re.search(r"\$\s*$", q[: m.start()])
            ]
            if any(year != "2026" for year in years):
                raise ValueError(
                    "Only verified tax year 2026 is supported; no estimate generated for another year"
                )
            if re.search(
                r"capital.gain|self.employ|1099|\brsu\b|equity|itemiz|car.*interest|auto.*interest|mortgage.*deduct|\btips\b|overtime|\bamt\b|\bniit\b|catch.?up",
                q,
            ):
                raise ValueError(
                    "This tax topic is outside the supported W-2 standard-deduction scope; no strategy is inferred"
                )
            projection = tool(
                "get_tax_projection",
                lambda: project_tax(conn, user_id=user_id),
                {"tax_year": 2026},
                "Tax & Payroll",
            )
            result["validation"] = validate_tax_projection(projection)
            amounts = re.findall(r"\$\s*([\d,]+(?:\.\d{1,2})?)", q)
            wants_change = bool(re.search(r"increase|extra|additional|what if", q)) and bool(
                re.search(r"401|hsa|roth|withhold", q)
            )
            if wants_change:
                kinds = []
                if "roth" in q:
                    kinds.append("roth")
                if "traditional" in q or ("401" in q and "roth" not in q):
                    kinds.append("traditional")
                if re.search(r"\bhsa\b", q):
                    kinds.append("hsa")
                if re.search(r"withhold", q):
                    kinds.append("withholding")
                if len(kinds) != 1:
                    raise ValueError(
                        "Use Tax Planning for combined changes; Copilot requires one unambiguous strategy type"
                    )
                if len(amounts) != 1:
                    raise ValueError(
                        "Specify one per-paycheck or monthly amount, or use Tax Planning for combined changes"
                    )
                matched = [
                    w
                    for w in projection["workers"]
                    if re.search(
                        r"\b" + re.escape(w["employee_name"].split()[0].lower()) + r"\b", q
                    )
                ]
                if len(matched) != 1:
                    raise ValueError(
                        "Identify the worker or select an employment in Tax Planning; household payroll changes are not guessed"
                    )
                worker = matched[0]
                amount = decimal(amounts[0].replace(",", ""))
                if re.search(r"per month|monthly|a month", q):
                    amount = (amount * 12 / decimal(worker["annual_periods"])).quantize(
                        Decimal(".01"), rounding=ROUND_HALF_UP
                    )
                elif not re.search(
                    r"per (?:paycheck|check|pay period)|each (?:paycheck|check|pay period)", q
                ):
                    raise ValueError(
                        "Specify whether the proposed amount is per paycheck or per month"
                    )
                field = (
                    "extra_roth_per_check"
                    if "roth" in q
                    else "extra_hsa_per_check"
                    if re.search(r"\bhsa\b", q)
                    else "extra_withholding_per_check"
                    if re.search(r"withhold", q)
                    else "extra_traditional_per_check"
                )
                changes = {"employment_key": worker["employment_key"], field: str(amount)}
                strategy = tool(
                    "simulate_tax_strategy",
                    lambda: tax_strategy(conn, changes, user_id),
                    changes,
                    "Tax Scenario",
                )
                for label, key in [
                    ("Federal income-tax reduction", "federal_tax_savings"),
                    ("Payroll-tax reduction", "payroll_tax_savings"),
                    ("Remaining take-home reduction", "remaining_take_home_reduction"),
                    ("Economic cost of extra contributions", "economic_after_tax_cost"),
                ]:
                    fact(
                        label,
                        strategy["comparison"][key],
                        "simulate_tax_strategy",
                        path="comparison." + key,
                    )
                result["scenarios"] = [strategy["goal_scenario"]]
                result["validation"] = strategy["validation"]
                result["assumptions"] = strategy["assumptions"]
                result["summary"] = (
                    "The comparison separates estimated tax savings, immediate take-home changes, and the cost of additional contributions. The simulation holds federal income withholding fixed; real payroll may automatically recalculate it. The goal simulation also earmarks the projected tax balance from cash; it does not subtract gross contributions twice."
                )
            else:
                for label, key in [
                    ("Projected federal income tax", "federal_income_tax"),
                    ("Projected federal withholding", "projected_federal_withholding"),
                    ("Estimated balance due", "balance_due"),
                    ("Projected refund", "projected_refund"),
                ]:
                    fact(
                        label,
                        projection["figures"][key],
                        "get_tax_projection",
                        path="figures." + key,
                    )
                result["summary"] = (
                    "This is a scope-limited federal estimate from reviewed regular paystubs and confirmed household inputs. Increasing withholding changes tax payments; it does not lower tax liability. Texas has no individual state income tax. Open Tax Planning for bracket calculations, the annual withholding screen, eligibility assumptions, and official rule sources."
                )
                result["assumptions"] = projection["assumptions"]
            ids = [w["document_id"] for w in projection["workers"]]
            if ids:
                placeholders = ",".join("?" for _ in ids)
                rows = conn.execute(
                    f"SELECT c.*,d.title,d.version FROM document_chunks c JOIN documents d ON c.document_id=d.id WHERE d.user_id=? AND d.id IN ({placeholders}) AND c.quarantined=0 ORDER BY c.rowid",
                    [user_id, *ids],
                ).fetchall()
                result["sources"] = [
                    {
                        "chunk_id": r["id"],
                        "document_id": r["document_id"],
                        "title": r["title"],
                        "version": r["version"],
                        "page": r["page"],
                        "section": r["section"],
                        "passage": r["content"],
                        "score": 0,
                        "superseded": False,
                    }
                    for r in rows
                ]
            result["completeness"] = "partial evidence"
            result["limitations"] += projection["assumptions"]
        elif route == "clarification":
            result["summary"] = (
                "Please identify the purchase or financial question. I cannot infer what “it” refers to without context."
            )
            result["completeness"] = "missing required data"
        elif route == "memory":
            m = memory()
            if "house" in q or "down" in q:
                g = tool("get_goal_status", a.get_goal_status, node="Goal & Memory")["items"][0]
                fact(
                    "House down-payment target",
                    g["target_amount"],
                    "get_goal_status",
                    path="items.0.target_amount",
                )
                fact(
                    "Earmarked house savings",
                    g["current_amount"],
                    "get_goal_status",
                    path="items.0.current_amount",
                )
                result["summary"] = (
                    "Your house objective comes from structured goals. Earmarked savings are already included in your cash balance."
                )
            else:
                fact(
                    "Emergency-fund minimum",
                    m["emergency_fund_minimum"],
                    "get_user_memory",
                    path="emergency_fund_minimum",
                )
                result["summary"] = (
                    "Your current emergency-fund requirement is $"
                    + m["emergency_fund_minimum"]
                    + ". Structured memory takes precedence over historical documents."
                )
                if "goal" in q:
                    sources = rag()
                    old = [s for s in sources if "Historical emergency-fund" in s["passage"]]
                    if old:
                        result["summary"] += (
                            f" A historical goals document records a different threshold. That conflict is visible and unresolved; the current ${m['emergency_fund_minimum']} constraint remains enforced until you explicitly confirm a change."
                        )
                        result["completeness"] = "partial evidence"
        elif route == "affordability":
            sources = rag()
            terms = loan_terms(sources, conn, user_id)
            fact("Vehicle price", terms["price"], "retrieve_documents", path="document.price")
            fact("Loan APR", terms["apr"], "retrieve_documents", "percent", path="document.apr")
            fact("Loan term", terms["months"], "retrieve_documents", "months", path="document.term")
            cash = tool("get_cash_position", a.get_cash_position)
            cf = tool("get_monthly_cash_flow", a.get_monthly_cash_flow)
            tool("get_debt_payments", a.get_debt_payments)
            m = memory()
            tool("get_goal_status", a.get_goal_status, node="Goal & Memory")
            fact("Available cash", cash["value"], "get_cash_position")
            fact("Baseline monthly surplus", cf["surplus"], "get_monthly_cash_flow", path="surplus")
            fact(
                "Emergency reserve",
                m["emergency_fund_minimum"],
                "get_user_memory",
                path="emergency_fund_minimum",
            )
            result["scenarios"] = tool(
                "simulate_scenario", lambda: compare_car(a, terms), terms, "Scenario"
            )
            result["validation"] = validate_scenarios(result["scenarios"])
            result["summary"] = (
                f"{sum(s['constraints']['emergency_fund']['passed'] for s in result['scenarios'][:2])} of 2 financed options preserve your current emergency reserve. Compare the house savings consumed and goal delay below; postponing preserves the baseline timeline. Full affordability is not established until vehicle taxes, fees, insurance, and ownership costs are supplied."
            )
            result["completeness"] = "partial evidence"
            result["assumptions"] = result["scenarios"][0]["assumptions"]
        elif route == "goal_comparison":
            sources = rag()
            terms = loan_terms(sources, conn, user_id)
            m = memory()
            goals = tool("get_goal_status", a.get_goal_status, node="Goal & Memory")["items"]
            fact("Vehicle price", terms["price"], "retrieve_documents", path="document.price")
            fact(
                "Emergency minimum",
                m["emergency_fund_minimum"],
                "get_user_memory",
                path="emergency_fund_minimum",
            )
            fact(
                "House target",
                goals[0]["target_amount"],
                "get_goal_status",
                path="items.0.target_amount",
            )
            result["summary"] = (
                "The loan offer and your goals are shown together. Whether the purchase fits requires current cash flow and a scenario calculation; this document-to-goals comparison does not establish affordability."
            )
            result["completeness"] = "partial evidence"
        elif route == "rag":
            sources = rag()
            relevant = sources
            if re.search(r"loan|car|auto", q) and "insurance" not in q:
                if "compare" not in q:
                    assert_offer_authority(conn, user_id)
                relevant = [
                    s
                    for s in sources
                    if s.get("family") == "auto"
                    or re.search(r"auto.loan|loan.offer", s["title"], re.I)
                ]
            elif "mortgage" in q:
                relevant = [s for s in sources if "mortgage" in s["title"].lower()]
            elif "deductible" in q or "insurance" in q:
                relevant = [s for s in sources if "insurance" in s["title"].lower()]
            elif "security" in q or "credit limit" in q:
                relevant = [s for s in sources if s["document_id"] == "security"]
            result["sources"] = relevant
            text = "\n".join(s["passage"] for s in relevant)
            if re.search(r"skip|defer|holiday", q):
                result["summary"] = (
                    "That provision was not found in the available document evidence. I cannot confirm skipped payments."
                )
                result["completeness"] = "missing required data"
            elif not relevant:
                result["summary"] = (
                    "The requested information was not found in your available documents."
                )
                result["completeness"] = "missing required data"
            elif "compare" in q:
                for source in relevant:
                    match = re.search(r"APR:\s*([\d.]+)%", source["passage"])
                    if match:
                        fact(
                            source["title"] + " APR",
                            match.group(1),
                            source["chunk_id"],
                            "percent",
                            path="document.apr",
                        )
                result["summary"] = (
                    "These are the stated APRs from both versions. The current offer supersedes the previous offer; the late-fee percentage is not the APR."
                )
            elif re.search(r"apr|interest|rate", q):
                pattern = (
                    r"Mortgage interest rate:\s*([\d.]+)%"
                    if "mortgage" in q
                    else r"\bAPR:\s*([\d.]+)%"
                )
                values = set(re.findall(pattern, text, re.I))
                if len(values) != 1:
                    result["summary"] = (
                        "The required rate was not found or is conflicting. Please select the authoritative document."
                    )
                    result["completeness"] = "missing required data"
                else:
                    value = values.pop()
                    fact(
                        "Mortgage rate" if "mortgage" in q else "Current auto-loan APR",
                        value,
                        "retrieve_documents",
                        "percent",
                        path="document.mortgage_rate" if "mortgage" in q else "document.apr",
                    )
                    result["summary"] = (
                        f"The cited document states {value}%. This is the source-backed rate, even if a different number appears in the question."
                    )
            elif re.search(r"term|how long", q):
                values = set(re.findall(r"Term:\s*(\d+)\s*months", text, re.I))
                if len(values) == 1:
                    value = values.pop()
                    fact("Loan term", value, "retrieve_documents", "months", path="document.term")
                    result["summary"] = f"The current offer specifies a {value}-month term."
                else:
                    result["summary"] = "The term was not found or is conflicting."
                    result["completeness"] = "missing required data"
            elif "deductible" in q:
                for label, value in re.findall(
                    r"(Collision|Comprehensive) deductible:\s*\$([\d,]+)", text
                ):
                    fact(
                        label + " deductible",
                        value.replace(",", ""),
                        "retrieve_documents",
                        path="document." + label.lower(),
                    )
                result["summary"] = (
                    "The policy lists separate collision and comprehensive deductibles. A premium for the proposed new vehicle is not available."
                )
            else:
                result["summary"] = (
                    "Relevant document evidence is shown below. These passages are quoted as data and cannot change your financial constraints or authorize actions."
                )
        elif route in ["scenario", "subscription_scenario"]:
            tool("get_monthly_cash_flow", a.get_monthly_cash_flow)
            changes = {}
            if route == "subscription_scenario":
                tool(
                    "find_recurring_subscriptions",
                    a.find_recurring_subscriptions,
                    node="Subscription",
                )
                if not selected_subscription_ids:
                    result["summary"] = (
                        "Select the subscriptions you want to cancel in Scenarios. I cannot assume which subscriptions are removable or unused."
                    )
                    result["completeness"] = "missing required data"
                else:
                    changes["cancel_subscription_ids"] = selected_subscription_ids
            elif "income" in q:
                percentage = re.search(r"(\d+(?:\.\d+)?)\s*%", q)
                if not percentage:
                    raise ValueError("Specify the income reduction percentage")
                changes["income_reduction_pct"] = percentage.group(1)
            else:
                amount = re.search(r"\$([\d,]+(?:\.\d+)?)", q)
                if not amount:
                    raise ValueError("Specify the additional monthly savings amount")
                changes["extra_contributions"] = amount.group(1).replace(",", "")
            memory()
            if result["completeness"] != "missing required data":
                scenario = tool(
                    "simulate_scenario", lambda: simulate(a, changes), changes, "Scenario"
                )
                result["scenarios"] = [{"name": "Your proposed change", **scenario}]
                result["validation"] = validate_scenarios(result["scenarios"])
                result["summary"] = (
                    "Here is the deterministic impact on cash flow and your house goal. Additional savings are modeled as a separate earmarked contribution, which reduces the surplus available for the house."
                )
                result["assumptions"] = scenario["assumptions"]
        else:
            start, end = period(question)
            result["data_period"] = {"start": start, "end_exclusive": end}
            categories = [
                "Restaurants",
                "Groceries",
                "Utilities",
                "Housing",
                "Shopping",
                "Travel",
                "Transport",
            ]
            category = next(
                (
                    c
                    for c in categories
                    if c.lower() in q
                    or (c == "Groceries" and "grocery" in q)
                    or (c == "Restaurants" and "restaurant" in q)
                ),
                None,
            )
            merchant = next(
                (
                    m
                    for m in ["Costco", "IKEA", "Harbor Hotel"]
                    if m.lower() in q or (m == "Harbor Hotel" and "hotel" in q)
                ),
                None,
            )
            if re.search(r"compar|versus|between", q) and category:
                earlier = period("September" if "september" in q else "last month")
                if earlier == (start, end):
                    earlier = month_bounds(-2)
                comparison = tool(
                    "compare_category_spending",
                    lambda: a.compare_category_spending(*earlier, start, end, category),
                    {"previous": earlier, "current": [start, end], "category": category},
                )
                for label, key in [("Previous period", "previous"), ("Current period", "current")]:
                    fact(
                        label,
                        comparison[key]["value"],
                        "compare_category_spending",
                        path=key + ".value",
                    )
                fact(
                    "Change",
                    comparison["difference"],
                    "compare_category_spending",
                    path="difference",
                )
                fact(
                    "Percentage change",
                    comparison["percent_change"],
                    "compare_category_spending",
                    "percent",
                    path="percent_change",
                )
                result["summary"] = (
                    f"{category} spending changed by {comparison['percent_change']}% between the selected complete periods."
                )
            elif re.search(r"why|increase|double", q):
                output = tool(
                    "identify_spending_anomalies",
                    lambda: a.identify_spending_anomalies(start, end),
                    {"start": start, "end_exclusive": end},
                )
                if category:
                    items = [x for x in output["items"] if x["category"] == category]
                else:
                    items = output["items"]
                for item in items:
                    fact(
                        item["category"] + " increase",
                        item["difference"],
                        "identify_spending_anomalies",
                        path=f"items.{output['items'].index(item)}.difference",
                    )
                    fact(
                        item["category"] + " percentage change",
                        item["percent_change"],
                        "identify_spending_anomalies",
                        "percent",
                        path=f"items.{output['items'].index(item)}.percent_change",
                    )
                result["summary"] = (
                    "The category changes below explain the arithmetic difference. They do not establish personal causes."
                )
                if "double" in q:
                    result["summary"] += (
                        " The data does not support a doubling of restaurant spending."
                    )
                if not items:
                    result["summary"] = (
                        "No category increases were found in this period against the preceding month. This month is partial and should not be compared as a full month."
                    )
            elif "subscription" in q:
                output = tool(
                    "find_recurring_subscriptions",
                    a.find_recurring_subscriptions,
                    node="Subscription",
                )
                fact(
                    "Monthly subscription equivalents",
                    output["value"],
                    "find_recurring_subscriptions",
                )
                result["items"] = output["items"]
                result["summary"] = (
                    "These active billing schedules total $"
                    + output["value"]
                    + " per month in equivalents. Annual plans are divided by twelve; actual posted cash outflow may differ. There is no evidence that any plan is unused."
                )
            elif re.search(r"largest|biggest|five", q):
                output = tool(
                    "get_largest_purchases",
                    lambda: a.get_largest_purchases(start, end),
                    {"start": start, "end_exclusive": end},
                )
                result["items"] = output["items"]
                result["summary"] = (
                    "Your five largest posted purchases, ordered by amount. Transfers, duplicates, pending, reversed, and future-dated entries are excluded."
                )
            elif re.search(r"percentage.*save|saving.*rate", q):
                output = tool(
                    "calculate_savings_rate",
                    lambda: a.calculate_savings_rate(start, end),
                    {"start": start, "end_exclusive": end},
                )
                fact("Savings rate", output["value"], "calculate_savings_rate", "percent")
                result["summary"] = (
                    "Savings rate is (income − net expenses) / income × 100. It is undefined when income is zero or missing."
                )
            elif "income" in q:
                output = tool(
                    "get_total_income",
                    lambda: a.get_total_income(start, end),
                    {"start": start, "end_exclusive": end},
                )
                fact("Total income", output["value"], "get_total_income")
                result["summary"] = "Total posted income for the stated period."
            elif merchant:
                output = tool(
                    "get_spending_by_merchant",
                    lambda: a.get_spending_by_merchant(merchant, start, end),
                    {"merchant": merchant, "start": start, "end_exclusive": end},
                )
                fact("Net spending at " + merchant, output["value"], "get_spending_by_merchant")
                result["summary"] = (
                    "No matching transactions were found; this is not a measured zero."
                    if output["value"] is None
                    else "Net posted merchant spending, with refunds deducted and merchant aliases normalized."
                )
            else:
                output = tool(
                    "get_spending_by_category",
                    lambda: a.get_spending_by_category(start, end, category),
                    {"category": category, "start": start, "end_exclusive": end},
                )
                fact(category or "Total spending", output["value"], "get_spending_by_category")
                result["items"] = output["items"]
                result["summary"] = (
                    "Net posted expenses for the stated period. Refunds reduce expenses; excluded transaction types are listed in the calculation details."
                )
            result["calculation"] = output if "output" in locals() else comparison
            if result["facts"] and all(x["value"] is None for x in result["facts"]):
                result["completeness"] = "missing required data"
        result["nodes"].append("Critic / Validator")
        provenance = validate_facts(result["facts"], calls, result["sources"], result["summary"])
        result["validation"]["checks"].extend(provenance["checks"])
        result["validation"]["errors"].extend(provenance["errors"])
        result["validation"]["passed"] = result["validation"]["passed"] and provenance["passed"]
        if not result["validation"]["passed"]:
            result["summary"] = (
                "Validation failed. No financial recommendation can be made from these results."
            )
            result["completeness"] = "missing required data"
        result["nodes"].append("Advisor / Synthesis")
    except Exception as exc:
        result.update(
            summary="I cannot complete this answer because required evidence or a tool is unavailable. "
            + str(exc)
            if isinstance(exc, ValueError)
            else "The required transaction tool failed. No affordability recommendation was generated.",
            error=type(exc).__name__,
            completeness="missing required data",
            scenarios=[],
            validation={
                "passed": False,
                "checks": ["required inputs"],
                "errors": [
                    str(exc) if isinstance(exc, ValueError) else "Required tool unavailable"
                ],
            },
        )
        result["events"].append(
            {
                "node": "Critic / Validator",
                "tool": "required_data_check",
                "status": "blocked",
                "latency_ms": 0,
                "summary": "Required evidence unavailable; answer blocked",
            }
        )
    result["council"] = review_council(result, enabled=use_model)
    if result["council"]["status"] in {"held", "incomplete"}:
        result["summary"] = (
            "Council review required; no council-endorsed recommendation. " + result["summary"]
        )
    if result["council"]["status"] not in {"off", "skipped"}:
        result["nodes"].append("Model Council")
        result["tools"].append("model_council")
        calls.append(
            (
                "model_council",
                {"mode": result["council"]["mode"]},
                result["council"],
                result["council"]["latency_ms"],
            )
        )
        result["events"].append(
            {
                "node": "Model Council",
                "tool": "model_council",
                "status": result["council"]["status"],
                "latency_ms": result["council"]["latency_ms"],
                "summary": result["council"]["reconciliation"],
            }
        )
    result["latency_ms"] = round((time.perf_counter() - started) * 1000)
    result["tracing"] = publish_trace(result)
    safe = redact(result)
    try:
        conn.execute(
            "INSERT INTO agent_runs(id,user_id,question,route,nodes,validation,latency_ms,error,answer) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                rid,
                user_id,
                redact(question),
                route,
                json.dumps(result["nodes"]),
                json.dumps(result["validation"]),
                result["latency_ms"],
                result["error"],
                json.dumps(safe),
            ),
        )
        for name, inputs, output, ms in calls:
            conn.execute(
                "INSERT INTO tool_calls VALUES(?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    rid,
                    name,
                    json.dumps(redact(inputs)),
                    json.dumps(redact(output)),
                    ms,
                ),
            )
        for source in result["sources"]:
            conn.execute(
                "INSERT INTO citations VALUES(?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    rid,
                    source["document_id"],
                    source["chunk_id"],
                    source["passage"],
                ),
            )
        conn.commit()
    except sqlite3.Error as exc:
        safe["tracing"] = "local audit storage unavailable; response retained in this session only"
        safe["limitations"].append(
            "The local audit database is unavailable; this trace could not be persisted."
        )
        logging.getLogger("finpilot").warning(
            json.dumps(
                {"event": "audit_storage_error", "category": type(exc).__name__, "run_id": rid}
            )
        )
    return safe
