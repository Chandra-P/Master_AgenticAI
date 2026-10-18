"""Deterministic fictional banking corpus; no LLM or external data is used."""
import hashlib
import json
import random
from pathlib import Path

import yaml

TYPES = ["Checking Account Acquisition", "Deposit Growth", "High Yield Savings", "CD Promotions",
         "HELOC Campaigns", "Mortgage Campaigns", "Auto Loan Campaigns", "Credit Card Acquisition",
         "Branch Openings", "Direct Deposit Programs", "Digital Banking Adoption"]
REGIONS = ["TX", "CA", "IL", "FL", "NY"]


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_corpus(output: Path, seed: int = 42) -> dict:
    output = Path(output)
    rng = random.Random(seed)
    campaigns, documents, cases = [], [], []

    def write(meta, sections):
        text = "---\n" + yaml.safe_dump(meta, sort_keys=True) + "---\n\n"
        text += "# " + meta["campaign_name"] + " — " + meta["document_type"] + "\n\n"
        text += "SYNTHETIC COURSE DATA: all institutions, outcomes, and recommendations are fictional.\n\n"
        text += "\n\n".join(f"## {name}\n\n{body}" for name, body in sections.items()) + "\n"
        relative = f"corpus/{meta['document_type']}/{meta['document_id']}.md"
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        documents.append({**meta, "source_path": relative, "content_hash": digest(text)})

    for i in range(20):
        kind = TYPES[i % len(TYPES)]
        region = REGIONS[i % 5]
        cid = "TX-CHK-001" if i == 0 else f"{region}-CMP-{i+1:03}"
        target = 180 + i * 23
        actual = round(target * rng.choice([0.72, 0.86, 0.96, 1.08, 1.19, 1.28]))
        budget = 24000 + i * 1750
        spend = round(budget * rng.uniform(0.85, 1.04))
        record = dict(campaign_id=cid, campaign_name=f"{region} {kind} {2024+i%3}",
                      client_name=f"Fictional {region} Community Financial {i+1}", campaign_type=kind,
                      region=region, year=2024+i%3, period=f"{2024+i%3}-Q2", target=target,
                      actual=actual, budget=budget, spend=spend, audience="Digitally active local households",
                      offer=f"Campaign-specific eligibility incentive for {kind.lower()}")
        campaigns.append(record)
        meta = {k: record[k] for k in ["campaign_id", "campaign_name", "client_name", "campaign_type", "region", "year", "period"]}
        objective = f"Acquire {target} verified product activations during {record['period']} for {kind}."
        email = round(actual * 0.6)
        kpi = f"| Metric | Target | Actual | Unit | Direction | Period |\n|---|---:|---:|---|---|---|\n| Verified activations | {target} | {actual} | count | higher | {record['period']} |\n| Acquisition cost | {budget/target:.2f} | {spend/actual:.2f} | USD/activation | lower | {record['period']} |\n| Spend | {budget} | {spend} | USD | lower | {record['period']} |"
        for doc_type, sections in {
            "brief": {"Objectives": objective, "Audience": record['audience'] + "; includes existing and prospective members.",
                      "Offer": record['offer'] + ". Eligibility and product suitability must be verified.",
                      "Creative Theme": "Local confidence and clear product value.",
                      "Channels": "Email and paid search with CRM deduplication.", "Budget": f"Approved budget: USD {budget}."},
            "success_plan": {"Success Criteria": f"Success requires at least {target} verified activations within {record['period']} and spend no higher than USD {budget}.",
                             "KPI Definitions": "Verified activations are deduplicated completed product enrollments within 30 days of an eligible click. Acquisition cost equals attributed spend divided by verified activations.",
                             "Targets": f"Verified activations target: {target} count; acquisition cost ceiling: USD {budget/target:.2f}/activation; spend ceiling: USD {budget}.",
                             "Reporting Window": f"Only outcomes in {record['period']} are comparable; attribution uses a 30-day last eligible click window."},
            "performance_report": {"KPI Results": kpi,
                                   "Performance Drivers": f"Email accounted for {email} verified activations and paid search for {actual-email}. Channel composition is an observed association, not causal lift.",
                                   "Audience Insights": f"Existing members supplied {email} activations and prospective members {actual-email}; no age-level or income-level outcome breakdown was measured.",
                                   "Channel Insights": f"Email: {email} activations; paid search: {actual-email}. Total attributed spend: USD {spend}. Channel-specific spend is unavailable, so channel ROI cannot be calculated.",
                                   "Measurement Limitations": "Observational attribution; no randomized control group. Campaign-level acquisition cost is not incremental ROI."},
            "historical_deck": {"Executive Summary": f"{cid} delivered {actual} verified activations versus a target of {target}; spend was USD {spend}.",
                                "Findings": f"Activation goal was {'met' if actual >= target else 'not met'}. Compare only campaigns with compatible measurement windows and product definitions.",
                                "Recommendations": "Test clearer eligibility language and a segmented follow-up cadence before changing allocation; validate results in a controlled experiment.",
                                "Lessons Learned": "Deduplicated outcomes and documented attribution prevent inflated activation totals. Avoid assuming association proves causality.",
                                "Suggested Next Steps": "Audit enrollment tracking, design a holdout test, and review results after the next reporting cycle."},
        }.items():
            write({**meta, "document_type": doc_type, "document_id": f"{cid}-{doc_type}"}, sections)
        if i < 10:
            cases.append(dict(id=f"q{i+1:02}", question=f"What were the objectives of campaign {cid}?", campaign_id=cid,
                              expected_answer=objective, expected_facts=[str(target), "verified", record['period']],
                              expected_sources=[f"{cid}-brief"], ground_truth_citations=[f"{cid}-brief#objectives"], split="calibration" if i < 3 else "held_out", kind="question"))
            cases.append(dict(id=f"q{i+11:02}", question=f"What were the results and channel findings for {cid}?", campaign_id=cid,
                              expected_answer=f"{actual} activations; {email} from email and {actual-email} from paid search.",
                              expected_facts=[str(actual), str(email), str(actual-email)], expected_sources=[f"{cid}-performance_report"],
                              ground_truth_citations=[f"{cid}-performance_report#kpi-results", f"{cid}-performance_report#channel-insights"], split="held_out", kind="question"))

    guidance = {
        "strategy": (10, "Strategy", "Use product suitability, audience eligibility, and a documented objective before selecting an offer. Compare historical campaigns with matching product and attribution definitions."),
        "best_practice": (10, "Recommendations", "Validate tracking before scaling. Test segmented follow-up with a randomized holdout. Treat observed channel associations as hypotheses, not causal lift. Never claim unmeasured audience or channel ROI."),
        "kpi_dictionary": (5, "KPI Definitions", "Activation attainment = actual / target when target is nonzero. Acquisition cost = spend / verified activations. Lower cost is better; higher activation count is better. ROI needs measured financial return and cannot be inferred from activations alone."),
        "methodology": (5, "Reporting Methodology", "Use 30-day last eligible click attribution, deduplicate CRM enrollments, retain reporting periods, and distinguish targets from actuals. Do not compare mismatched windows or invent missing denominators."),
    }
    for kind, (count, heading, body) in guidance.items():
        for i in range(count):
            write(dict(campaign_id="GLOBAL", campaign_name=f"Banking {kind} {i+1}", client_name="Synthetic course library",
                       campaign_type=TYPES[i % 11], region="ALL", year=2026, period="ALL", document_type=kind,
                       document_id=f"GLOBAL-{kind}-{i+1:02}"), {heading: f"{body}\n\nApplication focus: {TYPES[i%11]}. Guide edition: {i+1}."})
    for i in range(5):
        c = campaigns[i]
        cases.append(dict(id=f"q{i+21:02}", question=f"Generate a complete campaign performance report for {c['campaign_id']}.", campaign_id=c['campaign_id'],
                          expected_answer="Eleven sections with campaign-specific KPI comparisons and citations.", expected_facts=[str(c['target']), str(c['actual'])],
                          expected_sources=[f"{c['campaign_id']}-{t}" for t in ['brief','success_plan','performance_report','historical_deck']],
                          ground_truth_citations=[f"{c['campaign_id']}-performance_report#kpi-results"], split="held_out", kind="report"))
    for i, question in enumerate(["What was the CEO's private salary?", "What is the campaign's randomized causal lift?", "What was the channel ROI without channel revenue?", "Generate a report for ZZ-UNKNOWN-999", "What are activation results by exact customer age?"]):
        cases.append(dict(id=f"q{i+26:02}", question=question, campaign_id="TX-CHK-001" if i != 3 else "ZZ-UNKNOWN-999",
                          expected_answer="I could not find sufficient evidence in the knowledge base.", expected_facts=[], expected_sources=[],
                          ground_truth_citations=[], split="held_out", kind="unsupported"))
    manifest = dict(schema_version=1, seed=seed, campaigns=campaigns, documents=documents)
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output / "evaluation").mkdir(exist_ok=True)
    (output / "evaluation/questions.json").write_text(json.dumps(sorted(cases, key=lambda c:c['id']), indent=2), encoding="utf-8")
    return manifest
