"""Deterministic fictional banking corpus; no LLM or external data is used."""
import hashlib
from itertools import chain
import json
import random
from datetime import date,timedelta
from pathlib import Path

import yaml
from campaign_hub.synthetic_data.attribution import CHANNEL_RULES,attributable,matured
from campaign_hub.synthetic_data.geography import campaign_geography
from campaign_hub.synthetic_data.learning_corpus import learning_sources
from campaign_hub.synthetic_data.requirements_corpus import requirements_sources,requirements_cross_cases

TYPES = ["Checking Account Acquisition", "Deposit Growth", "High Yield Savings", "CD Promotions",
         "HELOC Campaigns", "Mortgage Campaigns", "Auto Loan Campaigns", "Credit Card Acquisition",
         "Branch Openings", "Direct Deposit Programs", "Digital Banking Adoption"]
REGIONS = ["TX", "CA", "IL", "FL", "NY"]


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def benchmark_questions() -> list[dict]:
    """Gold questions authored from existing sources, without retrieval-score tuning."""
    return [{'id': 'rag-ambiguous-01',
      'question': 'Does a late observation mean it is outside the attribution window, or does late '
                  'arrival differ from late occurrence under the correction policy?',
      'campaign_id': None,
      'expected_answer': 'A late-arriving observation can still fall within a previously defined '
                         'attribution window; an observation occurring outside that window cannot be '
                         'pulled inside merely because its file arrived with eligible events.',
      'expected_facts': ['A late-arriving observation can still fall within a previously defined '
                         'attribution window; an observation occurring outside that window cannot be '
                         'pulled inside merely because its file arrived with eligible events.'],
      'expected_sources': ['GLOBAL-learning-04'],
      'ground_truth_citations': ['GLOBAL-learning-04#correction-custody'],
      'split': 'held_out',
      'kind': 'question',
      'category': 'ambiguous',
      'evidence_facts': [{'source_id': 'GLOBAL-learning-04',
                          'citation': 'GLOBAL-learning-04#correction-custody',
                          'fact': 'A late-arriving observation can still fall within a previously '
                                  'defined attribution window; an observation occurring outside that '
                                  'window cannot be pulled inside merely because its file arrived with '
                                  'eligible events.'}],
      'measurement_provenance': {'purpose': 'source-grounded benchmark expansion',
                                 'held_out': True,
                                 'origin': 'authored by inspecting existing immutable synthetic '
                                           'sources',
                                 'usage': 'evaluation cases; not evidence of general quality or '
                                          'independent external validation'}},
     {'id': 'rag-ambiguous-02',
      'question': 'For TX-CHK-001, does the reported balance mean current balances, net new deposits, '
                  'revenue, or balances at account opening?',
      'campaign_id': 'TX-CHK-001',
      'expected_answer': 'Sum of posted account balances at opening (USD); not current balances, net '
                         'new deposits, or revenue.',
      'expected_facts': ['Sum of posted account balances at opening (USD); not current balances, net '
                         'new deposits, or revenue.'],
      'expected_sources': ['TX-CHK-001-performance_report'],
      'ground_truth_citations': ['TX-CHK-001-performance_report#balance-definition'],
      'split': 'held_out',
      'kind': 'question',
      'category': 'ambiguous',
      'evidence_facts': [{'source_id': 'TX-CHK-001-performance_report',
                          'citation': 'TX-CHK-001-performance_report#balance-definition',
                          'fact': 'Sum of posted account balances at opening (USD); not current '
                                  'balances, net new deposits, or revenue.'}],
      'measurement_provenance': {'purpose': 'source-grounded benchmark expansion',
                                 'held_out': True,
                                 'origin': 'authored by inspecting existing immutable synthetic '
                                           'sources',
                                 'usage': 'evaluation cases; not evidence of general quality or '
                                          'independent external validation'}},
     {'id': 'rag-ambiguous-03',
      'question': 'In DR-905, does a receipt timeout mean we should resend an accepted batch, or first '
                  'recover its status?',
      'campaign_id': None,
      'expected_answer': 'For DR-905, query the partner using the original idempotency key before '
                         'retrying; an accepted batch must not be resent.',
      'expected_facts': ['For DR-905, query the partner using the original idempotency key before '
                         'retrying; an accepted batch must not be resent.'],
      'expected_sources': ['GLOBAL-learning-10'],
      'ground_truth_citations': ['GLOBAL-learning-10#dr-905-recovery'],
      'split': 'held_out',
      'kind': 'question',
      'category': 'ambiguous',
      'evidence_facts': [{'source_id': 'GLOBAL-learning-10',
                          'citation': 'GLOBAL-learning-10#dr-905-recovery',
                          'fact': 'For DR-905, query the partner using the original idempotency key '
                                  'before retrying; an accepted batch must not be resent.'}],
      'measurement_provenance': {'purpose': 'source-grounded benchmark expansion',
                                 'held_out': True,
                                 'origin': 'authored by inspecting existing immutable synthetic '
                                           'sources',
                                 'usage': 'evaluation cases; not evidence of general quality or '
                                          'independent external validation'}},
     {'id': 'rag-multi-01',
      'question': 'After an attribution correction changes the source checksum under the same document '
                  'ID, what must happen to the signed snapshot and to a cached answer presented as '
                  'current?',
      'campaign_id': None,
      'expected_answer': 'A late correction receives a new revision linked to the original snapshot; '
                         'it never overwrites the signed snapshot under policy AC-318. KS-663 rejects '
                         'a cached retrieval result when its source checksum differs from the current '
                         'manifest, even if the document identifier is unchanged.',
      'expected_facts': ['A late correction receives a new revision linked to the original snapshot; '
                         'it never overwrites the signed snapshot under policy AC-318.',
                         'KS-663 rejects a cached retrieval result when its source checksum differs '
                         'from the current manifest, even if the document identifier is unchanged.'],
      'expected_sources': ['GLOBAL-learning-04', 'GLOBAL-learning-12'],
      'ground_truth_citations': ['GLOBAL-learning-04#correction-custody',
                                 'GLOBAL-learning-12#ks-663-mismatch'],
      'split': 'held_out',
      'kind': 'question',
      'category': 'multi_document',
      'evidence_facts': [{'source_id': 'GLOBAL-learning-04',
                          'citation': 'GLOBAL-learning-04#correction-custody',
                          'fact': 'A late correction receives a new revision linked to the original '
                                  'snapshot; it never overwrites the signed snapshot under policy '
                                  'AC-318.'},
                         {'source_id': 'GLOBAL-learning-12',
                          'citation': 'GLOBAL-learning-12#ks-663-mismatch',
                          'fact': 'KS-663 rejects a cached retrieval result when its source checksum '
                                  'differs from the current manifest, even if the document identifier '
                                  'is unchanged.'}],
      'measurement_provenance': {'purpose': 'source-grounded benchmark expansion',
                                 'held_out': True,
                                 'origin': 'authored by inspecting existing immutable synthetic '
                                           'sources',
                                 'usage': 'evaluation cases; not evidence of general quality or '
                                          'independent external validation'}},
     {'id': 'rag-multi-02',
      'question': 'During consent recovery an emergency withdrawal is received. What is the '
                  'suppression acknowledgment and queued-reuse rule, and what review gate is required '
                  'to resume the quarantined file?',
      'campaign_id': None,
      'expected_answer': 'The suppression service must acknowledge emergency withdrawal SP-809 within '
                         'four business hours and block queued reuse until reconciliation. Resume only '
                         'after two independent reviewers reconcile every quarantined row and sign '
                         'gate CR-217.',
      'expected_facts': ['The suppression service must acknowledge emergency withdrawal SP-809 within '
                         'four business hours and block queued reuse until reconciliation.',
                         'Resume only after two independent reviewers reconcile every quarantined row '
                         'and sign gate CR-217.'],
      'expected_sources': ['GLOBAL-learning-06', 'GLOBAL-learning-01'],
      'ground_truth_citations': ['GLOBAL-learning-06#suppression-custody',
                                 'GLOBAL-learning-01#recovery-gate'],
      'split': 'held_out',
      'kind': 'question',
      'category': 'multi_document',
      'evidence_facts': [{'source_id': 'GLOBAL-learning-06',
                          'citation': 'GLOBAL-learning-06#suppression-custody',
                          'fact': 'The suppression service must acknowledge emergency withdrawal '
                                  'SP-809 within four business hours and block queued reuse until '
                                  'reconciliation.'},
                         {'source_id': 'GLOBAL-learning-01',
                          'citation': 'GLOBAL-learning-01#recovery-gate',
                          'fact': 'Resume only after two independent reviewers reconcile every '
                                  'quarantined row and sign gate CR-217.'}],
      'measurement_provenance': {'purpose': 'source-grounded benchmark expansion',
                                 'held_out': True,
                                 'origin': 'authored by inspecting existing immutable synthetic '
                                           'sources',
                                 'usage': 'evaluation cases; not evidence of general quality or '
                                          'independent external validation'}},
     {'id': 'rag-multi-03',
      'question': 'In a partner handoff, one new file has no checksum and a separate previously '
                  'transmitted batch has a receipt timeout. What do the north notebook and delivery '
                  'FAQ require for each?',
      'campaign_id': None,
      'expected_answer': 'A partner file without a checksum stays in intake hold NH-143 and cannot '
                         'become a delivery batch. For DR-905, query the partner using the original '
                         'idempotency key before retrying; an accepted batch must not be resent.',
      'expected_facts': ['A partner file without a checksum stays in intake hold NH-143 and cannot '
                         'become a delivery batch.',
                         'For DR-905, query the partner using the original idempotency key before '
                         'retrying; an accepted batch must not be resent.'],
      'expected_sources': ['GLOBAL-learning-07', 'GLOBAL-learning-10'],
      'ground_truth_citations': ['GLOBAL-learning-07#document', 'GLOBAL-learning-10#dr-905-recovery'],
      'split': 'held_out',
      'kind': 'question',
      'category': 'multi_document',
      'evidence_facts': [{'source_id': 'GLOBAL-learning-07',
                          'citation': 'GLOBAL-learning-07#document',
                          'fact': 'A partner file without a checksum stays in intake hold NH-143 and '
                                  'cannot become a delivery batch.'},
                         {'source_id': 'GLOBAL-learning-10',
                          'citation': 'GLOBAL-learning-10#dr-905-recovery',
                          'fact': 'For DR-905, query the partner using the original idempotency key '
                                  'before retrying; an accepted batch must not be resent.'}],
      'measurement_provenance': {'purpose': 'source-grounded benchmark expansion',
                                 'held_out': True,
                                 'origin': 'authored by inspecting existing immutable synthetic '
                                           'sources',
                                 'usage': 'evaluation cases; not evidence of general quality or '
                                          'independent external validation'}},
     {'id': 'rag-unsupported-01',
      'question': 'Which named employees signed CR-217 for the TX-CHK-001 consent recovery incident?',
      'campaign_id': None,
      'expected_answer': 'I could not find sufficient evidence in the knowledge base.',
      'expected_facts': [],
      'expected_sources': [],
      'ground_truth_citations': [],
      'split': 'held_out',
      'kind': 'unsupported',
      'category': 'unsupported'},
     {'id': 'rag-unsupported-02',
      'question': 'What real statutory retention period does fictional policy AC-318 require?',
      'campaign_id': None,
      'expected_answer': 'I could not find sufficient evidence in the knowledge base.',
      'expected_facts': [],
      'expected_sources': [],
      'ground_truth_citations': [],
      'split': 'held_out',
      'kind': 'unsupported',
      'category': 'unsupported'}]


def generate_corpus(output: Path, seed: int = 42) -> dict:
    output = Path(output)
    rng = random.Random(seed)
    campaigns, documents, cases, geography = [], [], [], []

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
        type_index=i if i<11 else 0 if i<15 else 1 if i<19 else 2
        kind = TYPES[type_index]
        region = REGIONS[i % 5]
        cid = "TX-CHK-001" if i == 0 else f"{region}-CMP-{i+1:03}"
        target = 180 + i * 23
        actual = round(target * rng.choice([0.72, 0.86, 0.96, 1.08, 1.19, 1.28]))
        budget = 24000 + i * 1750
        spend = round(budget * rng.uniform(0.85, 1.04))
        year=2026 if i<9 else 2024+i%2
        direct_mail=round(actual * 0.6)
        channel_results={}
        for channel,count,exposures,channel_spend in [
            ('direct_mail',direct_mail,5000+i*200,round(spend*.65)),
            ('display',actual-direct_mail,10000+i*400,spend-round(spend*.65))]:
            rule=CHANNEL_RULES[channel]
            anchor_date=date(year,4,1 if channel=='direct_mail' else 15)
            as_of=date(year,6,30)
            conversions=[anchor_date+timedelta(days=1+j%rule['window_days']) for j in range(count)]
            conversions += [anchor_date-timedelta(days=1),anchor_date+timedelta(days=rule['window_days']+1)]
            attributed=sum(attributable(channel,anchor_date,d) for d in conversions)
            channel_results[channel]={**rule,'anchor_date':anchor_date.isoformat(),'as_of':as_of.isoformat(),
                'exposures':exposures,'activations':attributed,'spend':channel_spend,
                'mature':matured(channel,anchor_date,as_of),'excluded_conversions':len(conversions)-attributed}
        client_index=type_index%5 if i<11 else 0 if i<13 else 3 if i<15 else 1 if i<17 else 4 if i<19 else 2
        clients=['Fictional Meridian Credit Union','Fictional Harbor Community Bank','Fictional Summit Credit Union','Fictional Prairie Bank','Fictional Orchard Financial']
        record = dict(campaign_id=cid, campaign_name=f"{region} {kind} {year}",
                      client_name=clients[client_index], campaign_type=kind,
                      region=region, year=year, period=f"{year}-Q2", target=target,channel_results=channel_results,
                      actual=actual, budget=budget, spend=spend, audience="Digitally active local households",
                      offer=f"Campaign-specific eligibility incentive for {kind.lower()}")
        geo_rows=campaign_geography(record,i)
        geography.extend(geo_rows)
        record['balance_cents']=sum(r['balance_cents'] for r in geo_rows)
        record['balance_target_cents']=target*300000
        record['balance_definition']='Sum of posted account balances at opening (USD); not current balances, net new deposits, or revenue.'
        campaigns.append(record)
        meta = {k: record[k] for k in ["campaign_id", "campaign_name", "client_name", "campaign_type", "region", "year", "period"]}
        objective = f"Acquire {target} verified product activations during {record['period']} for {kind}."
        direct_mail = channel_results['direct_mail']['activations']
        channel_table='| Channel | Activations | Exposures | Spend USD | Window days | Anchor | Anchor date | As of | Exposure unit | Mature |\n|---|---:|---:|---:|---:|---|---|---|---|---|\n'
        for channel,stats in channel_results.items():
            channel_table+=f"| {channel} | {stats['activations']} | {stats['exposures']} | {stats['spend']} | {stats['window_days']} | {stats['anchor']} | {stats['anchor_date']} | {stats['as_of']} | {stats['exposure_unit']} | {str(stats['mature']).lower()} |\n"
        kpi = f"| Metric | Target | Actual | Unit | Direction | Period |\n|---|---:|---:|---|---|---|\n| Verified activations | {target} | {actual} | count | higher | {record['period']} |\n| Acquisition cost | {budget/target:.2f} | {spend/actual:.2f} | USD/activation | lower | {record['period']} |\n| Spend | {budget} | {spend} | USD | lower | {record['period']} |"
        kpi+=f"\n| Opening account balance | {record['balance_target_cents']/100:.2f} | {record['balance_cents']/100:.2f} | USD | higher | {record['period']} |"
        geo_table='| Location | Channel | Accounts | Opening balance cents | Exposures | Latitude | Longitude | As of |\n|---|---|---:|---:|---:|---:|---:|---|\n'
        geo_table+='\n'.join(f"| {r['location']} | {r['channel']} | {r['accounts']} | {r['balance_cents']} | {r['exposures']} | {r['latitude']} | {r['longitude']} | {r['as_of']} |" for r in geo_rows)
        for doc_type, sections in {
            "brief": {"Objectives": objective, "Audience": record['audience'] + "; includes existing and prospective members.",
                      "Offer": record['offer'] + ". Eligibility and product suitability must be verified.",
                      "Creative Theme": "Local confidence and clear product value.",
                      "Channels": "Direct mail and display only, with deduplicated CRM activations. Direct mail attribution: 60 days from mail/drop date. Display attribution: 30 days from exposure date.", "Budget": f"Approved budget: USD {budget}."},
            "success_plan": {"Success Criteria": f"Success requires at least {target} verified activations within {record['period']} and spend no higher than USD {budget}.",
                             "KPI Definitions": "Verified activations are deduplicated completed product enrollments within 60 days of the direct mail/drop date or 30 days of display exposure. Acquisition cost equals attributed spend divided by verified activations. Direct mail rate uses mailed households; display rate uses unique exposed users. Compare rates within the same channel and denominator definition.",
                             "Targets": f"Verified activations target: {target} count; acquisition cost ceiling: USD {budget/target:.2f}/activation; spend ceiling: USD {budget}; opening account balance target: USD {record['balance_target_cents']/100:.2f}.",
                             "Reporting Window": f"Reporting cohort: {record['period']}. Direct mail: 60 days from mail/drop date; display: 30 days from exposure. Include only conversions on/after the anchor and no later than the channel window boundary. Both windows are fully observed as of {year}-06-30. De-duplicate activations across channels; outcomes are pre-assigned to one eligible channel in this synthetic corpus."},
            "performance_report": {"KPI Results": kpi,
                                   "Performance Drivers": f"Direct mail accounted for {direct_mail} verified activations and display for {actual-direct_mail}. Channel composition is an observed association, not causal lift.",
                                   "Audience Insights": f"Existing members supplied {direct_mail} activations and prospective members {actual-direct_mail}; no age-level or income-level outcome breakdown was measured.",
                                   "Channel Insights": f"Direct mail: {direct_mail} activations within 60 days of mail/drop date; display: {actual-direct_mail} within 30 days of exposure. Total attributed spend: USD {spend}. Channel-specific spend and exposure counts are in Channel Results. Financial return is unavailable, so channel ROI cannot be calculated.",
                                   "Channel Results":channel_table,
                                   "Geographic Results":geo_table,
                                   "Balance Definition":record['balance_definition'],
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
                              expected_answer=f"{actual} activations; {direct_mail} from direct mail and {actual-direct_mail} from display.",
                              expected_facts=[str(actual), str(direct_mail), str(actual-direct_mail)], expected_sources=[f"{cid}-performance_report"],
                              ground_truth_citations=[f"{cid}-performance_report#kpi-results", f"{cid}-performance_report#channel-insights"], split="held_out", kind="question"))

    guidance = {
        "strategy": (10, "Strategy", "Use product suitability, audience eligibility, and a documented objective before selecting an offer. Compare historical campaigns with matching product and attribution definitions."),
        "best_practice": (10, "Recommendations", "Validate tracking before scaling. Test segmented follow-up with a randomized holdout. Treat observed channel associations as hypotheses, not causal lift. Never claim unmeasured audience or channel ROI."),
        "kpi_dictionary": (5, "KPI Definitions", "Activation attainment = actual / target when target is nonzero. Acquisition cost = spend / verified activations. Lower cost is better; higher activation count is better. ROI needs measured financial return and cannot be inferred from activations alone."),
        "methodology": (5, "Reporting Methodology", "Use direct mail and display only. Direct mail attribution is 60 days from mail/drop date; display attribution is 30 days from exposure date. Exclude conversions before the anchor or after its channel window. Compare fully matured earlier campaigns within the same product/channel, attribution window, and exposure denominator. Deduplicate CRM enrollments and distinguish targets from actuals. Do not compare mismatched windows or invent missing denominators."),
    }
    for kind, (count, heading, body) in guidance.items():
        for i in range(count):
            write(dict(campaign_id="GLOBAL", campaign_name=f"Banking {kind} {i+1}", client_name="Synthetic course library",
                       campaign_type=TYPES[i % 11], region="ALL", year=2026, period="ALL", document_type=kind,
                       document_id=f"GLOBAL-{kind}-{i+1:02}"), {heading: f"{body}\n\nApplication focus: {TYPES[i%11]}. Guide edition: {i+1}."})
    for i, question in enumerate(["What was the CEO's private salary?", "What is the campaign's randomized causal lift?", "What was the channel ROI without channel revenue?", "Generate a report for ZZ-UNKNOWN-999", "What are activation results by exact customer age?"]):
        cases.append(dict(id=f"q{i+26:02}", question=question, campaign_id="TX-CHK-001" if i != 3 else "ZZ-UNKNOWN-999",
                          expected_answer="I could not find sufficient evidence in the knowledge base.", expected_facts=[], expected_sources=[],
                          ground_truth_citations=[], split="held_out", kind="unsupported"))
    cases.extend(benchmark_questions())
    for meta, body, case in chain(learning_sources(),requirements_sources()):
        text = "---\n" + yaml.safe_dump(meta, sort_keys=True) + "---\n\n"
        text += f"# {meta['campaign_name']}\n\n"
        text += "SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.\n\n"
        text += body + '\n'
        relative = f"corpus/learning_guide/{meta['document_id']}.md"
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        documents.append({**meta, 'source_path': relative, 'content_hash': digest(text)})
        cases.append(case)
    cases.extend(requirements_cross_cases())
    geography_text=json.dumps(geography,indent=2,sort_keys=True)
    (output/'geography.json').write_text(geography_text,encoding='utf-8')
    manifest = dict(schema_version=4, seed=seed, campaigns=campaigns, documents=documents,geography_hash=digest(geography_text))
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output / "evaluation").mkdir(exist_ok=True)
    (output / "evaluation/questions.json").write_text(json.dumps(sorted(cases, key=lambda c:c['id']), indent=2), encoding="utf-8")
    return manifest
