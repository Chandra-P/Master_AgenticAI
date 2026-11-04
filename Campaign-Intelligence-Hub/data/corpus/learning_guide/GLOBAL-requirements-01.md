---
campaign_id: GLOBAL
campaign_name: Canary campaign measurement dictionary
campaign_type: Shared campaign operations
client_name: Synthetic course library
description: 'Fictional CL-640 evidence: canary campaign measurement dictionary; scope
  and source precedence are explicit.'
document_id: GLOBAL-requirements-01
document_shape: playbook
document_type: learning_guide
effective_date: '2026-10-01'
evidence_pack: requirements-v1
period: ALL
region: ALL
source_status: active
source_version: '1'
year: 2026
---

# Canary campaign measurement dictionary

SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.

## Scope and custody
This dictionary applies only to the fictional canary campaign CL-640. It defines fields before any campaign results exist. The exercise contains invented aggregate examples, not a customer extract. The measurement owner approves definitions, while the source custodian records which export implements them. A field name in a dashboard is not the authority for its meaning. When an export changes a definition, retain the old definition and create a versioned mapping rather than silently changing historical values.

## Balance meaning
For CL-640, opening balance is the posted balance at account opening; it is not current balance, net new deposits, or revenue.
A later withdrawal changes current balance but does not rewrite the opening observation. An internal transfer can contribute to opening balance without representing new money entering the institution. A campaign analyst cannot infer transfer treatment from a positive aggregate. If an analysis requires net new deposits, the owner must specify eligible flows and supply transfer evidence separately. This dictionary does not supply that evidence.

## Aggregate rehearsal
| Field | Invented value | Unit | Interpretation |
|---|---:|---|---|
| Verified activations | 80 | distinct enrolled accounts | Completed verification, not clicks |
| Direct mail activations | 48 | distinct enrolled accounts | Observational attribution |
| Display activations | 32 | distinct enrolled accounts | Observational attribution |
| Opening balance | 160000 | USD | Posted at opening |
| Net new deposits | unavailable | USD | Transfer evidence absent |
The channel counts reconcile to the total in this rehearsal. They do not establish that either channel caused an activation. Exposures use different units across channels, so a raw response-rate comparison also requires compatible denominators. Preserve the unit and maturity state next to any exported count.

## Missing values and zero
An unavailable measurement must remain unavailable, rather than becoming zero during export. Zero means the owner measured the defined quantity and observed none. An empty cell can instead indicate missing evidence, a pending refresh, or a field outside the source scope. The analyst records the reason with the value. A formatting rule that replaces blanks with zeros would erase that distinction and can turn an honest limitation into an apparently precise result.

## Change control
The rehearsal numbers are immutable teaching inputs. Correct a transcription error through a new revision linked to the original dictionary, with the changed field and reason stated. Do not change the rehearsal to make a model answer look better. A future measurement design may use different units, but it needs a new identifier and its own examples. The dictionary is one source of evidence; the separate timing policy determines whether an event is mature enough to enter a campaign snapshot.
