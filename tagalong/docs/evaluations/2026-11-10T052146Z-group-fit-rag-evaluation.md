# Group Fit live synthetic Pinecone retrieval evaluation

Run started (UTC): 2026-11-10T05:21:46.569455+00:00
Model: `gpt-4.1-mini`

Synthetic MemoryRepository plans only. Positive cases upsert synthetic message evidence into random plan namespaces, verify it appears in Pinecone semantic top-k, then call the real Group Fit endpoint and OpenAI model. Synthetic vectors are deleted after each case. No production database, real plan, account, or index namespace is used.

## Reproduce

From `tagalong/backend`:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.\.venv\Scripts\python.exe scripts\evaluate_group_fit.py
```

The runner uses existing OpenAI and Pinecone credentials only for synthetic provider calls. It creates random in-memory plans and `eval-` source IDs, checks actual Pinecone top-k retrieval, and deletes only vectors it created. It does not write to the production database or production plan namespaces. Each run creates new timestamped artifacts.

## Deterministic rule and security scenarios

30/30 tests passed; exit code 0; 8.648 seconds.

| Check | Passing scenarios |
|---|---|
| citation validation | 4/4 |
| budget conflict rule | 1/1 |
| missing evidence rule | 1/1 |
| cross plan access | 2/2 |
| freshness | 7/7 |

## Live cases

| Case | Expected | Observed | Pinecone evidence in prompt | Valid citation IDs | Seconds |
|---|---|---|---|---|---|
| over_budget | conflicts | conflicts | yes | yes | 3.488 |
| missing_evidence | needs_info | needs_info | no / N/A | N/A (no findings) | 1.798 |
| dietary_conflict | conflicts | conflicts | yes | yes | 1.933 |
| supported_home_option_safety_unknown | needs_info | needs_info | yes | yes | 2.832 |

Indexed source checks: 3/3 found in Pinecone top-k; 3/3 reached the model prompt.

## Same-option live ablation

Pinecone evidence cited: True.
Verdict changed after source removal: False; substantive response content changed: True.
Evidence materially changed the response: True (the Pinecone-sourced group match is cited only when evidence is present).
With evidence: `needs_info`; after removal: `needs_info`.
Ablation error type: `none`. Cleanup failures: `none`.

## Limits

- This is a small synthetic demonstration, not a representative quality benchmark.
- The live ablation tests whether a uniquely indexed synthetic group message is retrieved, cited, and changes the assessment findings when removed. Safety uncertainty can correctly keep the verdict at needs_info in both runs; one pair does not establish broad retrieval precision or recall.
- Citation ID validity and model citations do not prove semantic entailment, truth, or safety; human citation entailment remains unscored.
- Budget and missing-evidence rules are deterministic, so those outcomes are not model-only reasoning tests.
- The sequential run is not a load test or latency percentile study.
- No real menu, allergy safety, current prices, availability, booking or calendar action is verified.

See the adjacent JSON for per-case query hits, evidence origins, source IDs, responses, timings, and code hashes.
