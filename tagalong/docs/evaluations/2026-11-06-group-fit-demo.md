# Group-fit synthetic demonstration evaluation

Run started (UTC): 2026-11-06T22:20:31.789571+00:00
Model: `gpt-4.1-mini`

Synthetic MemoryRepository plans only; real OpenAI generation and real Pinecone queries in fresh random namespaces. No index writes, production plans, production database, or real auth accounts.

## Reproduce

From `tagalong/backend`:

```sh
uv run --env-file /secure/path/backend.env python scripts/evaluate_group_fit.py
```

The script removes database/auth environment values, disables indexing, runs fake-provider rule tests without provider keys, then runs four live synthetic requests. It uses existing OpenAI/Pinecone credentials only for provider calls. It never upserts vectors. Re-running overwrites these dated demo artifacts.

## Deterministic rule and security scenarios

27/27 tests passed; exit code 0; 20.314 seconds.

| Check | Passing scenarios |
|---|---|
| citation validation | 4/4 |
| budget conflict rule | 1/1 |
| missing evidence rule | 1/1 |
| cross plan access | 2/2 |
| freshness | 7/7 |

## Live provider outcomes

| Synthetic case | Expected | Observed | Valid citation IDs | End-to-end seconds |
|---|---|---|---|---|
| over_budget | conflicts | conflicts | yes | 6.081 |
| missing_evidence | needs_info | needs_info | N/A (no findings) | 2.655 |
| dietary_conflict | conflicts | conflicts | yes | 2.016 |
| supported_home_option | fits | fits | yes | 3.245 |

Validated responses: 4/4. Expected-verdict agreement: 4/4. Unchanged in-memory state: 4/4.
Median latency: 2.95 seconds; maximum observed: 6.081 seconds.

Citation references: 12/12 findings cite supplied source IDs across 3 cases with findings. This is reference validity, not semantic accuracy.

## Limits and honest interpretation

- Four synthetic cases are a demonstration, not a statistically representative benchmark.
- Citation-ID validity establishes supplied-source references, not semantic entailment, truth, or safety. Human citation entailment was not scored. Cases with no findings are N/A for citation validity.
- Fresh namespaces intentionally have no indexed records. Live Pinecone checks validate routing/availability, not retrieval relevance or ranking quality. Saved synthetic Notes provide immediate evidence.
- Budget and missing-evidence outcomes include deterministic server rules; they do not measure model-only reasoning accuracy.
- Latency includes authentication adapter, repository, real embedding/query and model generation. One sequential run, no load test or percentile claims.
- No real menu, allergy safety, prices, availability, booking or calendar action was verified.

See the adjacent JSON for exact synthetic inputs, returned evidence/findings, per-stage timings and source-file hashes.
