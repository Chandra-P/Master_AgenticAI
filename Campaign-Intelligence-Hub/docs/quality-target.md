# Working toward 90 percent quality

The target is **0.90 or higher for each measured dimension**, with complete assessment coverage. It is not a single blended accuracy score and has not yet been achieved.

## What is measured

| Measure | Meaning |
|---|---|
| Passage relevance precision | Fraction of retrieved passages the judge labels useful for the reference answer. Every passage must receive a valid judgment. |
| RAGAS context precision | RAGAS rank-aware average precision; reported separately because it is not the fraction of relevant passages. |
| RAGAS context recall | Reference claims supported by the retrieved context. |
| RAGAS faithfulness | Generated-answer claims supported by the retrieved evidence. Abstention does not earn a perfect score. |
| RAGAS factual correctness | Actual RAGAS reference-based claim precision/recall F1. |
| Answer coverage | Fraction of supported questions receiving a non-abstained answer without an execution error. |
| Unsupported abstention | Fraction of unsupported questions that correctly decline to answer. |

The old 34.6% figure remains the saved expected-document-overlap precision from a different retrieval experiment. It must not be relabeled as passage relevance or answer correctness.

## The gate

The current question set has **17 supported held-out questions and five unsupported cases**. A smoke run cannot pass the complete-set gate. All supported cases require valid passage relevance, context recall, faithfulness and factual-correctness scores; all four means, answer coverage and unsupported abstention must reach 0.90. Missing scores, execution failures, missing cases or a failed judge calibration make the result incomplete. Low scores and abstentions remain visible rather than being removed from the sample.

Before quality assessment, the judge receives one known-relevant passage and three known-irrelevant calibration passages. The reference answer is identical across them. A judge that simply copies the reference into every relevance verdict fails this check. Passing four controls is a necessary check, not proof of general judge reliability. An independent reviewer and broader questions are still required.

These existing questions are narrow and have been inspected during development: seven ask for campaign objectives and ten ask for results and channel findings. Any eventual pass describes this development set; it is not untouched independent certification, production readiness, or proof of 90% real-world answer accuracy. The separate five report cases and final client-report validation are not covered by the question-quality gate.

## Opt-in improvement

`--focus-context` selects existing retrieved sections based on the question: Objectives for original intent, Targets for metric goals, and KPI Results plus Channel Insights for combined result/channel questions. It reads no gold answers or evaluation labels. Comparisons and historical questions retain broader context. If a requested section is absent, it retains the original candidates rather than silently dropping needed evidence. Source spans, chunk IDs and citation provenance remain traceable.

This option is **off by default**, pending adequate quality evidence. It does not modify client-report source selection or the public navigation. The old baseline experiment artifacts are unchanged.

## Run with free local models

Install the optional RAGAS dependencies, keep Ollama running, and use compatible embeddings/indexes. For the existing CPU indexes in PowerShell:

```powershell
$env:CIH_EMBEDDING_PROVIDER="sentence_transformers"
$env:CIH_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
$env:CIH_GENERATION_PROVIDER="ollama"
$env:CIH_GENERATION_MODEL="llama3.2:3b"
python -m campaign_hub evaluate --ragas --quality --focus-context --ragas-limit 22 --metric-timeout 180
```

Omit `--focus-context` for the baseline. Avoid `--full` until a single configuration has reliable assessments; it multiplies expensive model calls. A one-case `--ragas-limit 1` run is useful for debugging and always remains incomplete against the complete question set.

Outputs: `data/runs/quality/latest/results.json`, individual execution records, CSV and `quality-summary.json`. Each record preserves exact answers, ranked passages, references, per-passage verdicts/reasons and model identities. `--judge-provider` and `--judge-model` allow a separately configured judge; a free hosted judge requires an owner-supplied environment key, never a visitor key or a key pasted into chat.

For a hosted Groq assessment, the CLI loads only `GROQ_API_KEY` from the ignored project `.streamlit/secrets.toml` when it is not already in the environment. Keep the tracked `secrets.example.toml` as a placeholder. Streamlit Cloud secrets are separate from this local file. Failed calibration stops subsequent generation calls and records an incomplete result rather than spending calls on an unreliable judge.

## Actual development findings

Hosted development command (use compatible existing indexes):

```powershell
$env:CIH_EMBEDDING_PROVIDER="sentence_transformers"
$env:CIH_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
$env:CIH_GENERATION_PROVIDER="groq"
$env:CIH_GENERATION_MODEL="qwen/qwen3.8-27b"
python -m campaign_hub evaluate --ragas --quality --focus-context --ragas-limit 22 --judge-provider groq --judge-model openai/gpt-oss-120b --metric-timeout 240
```

The Groq judge uses up to five SDK retries, which honor provider rate-limit responses; the public generator retains its default of one retry. Retry settings and metric timeout are recorded with the run. Exhausted quotas, invalid judgments and timeouts remain missing metrics and block a pass. No paid-plan change is part of this workflow. See [Groq rate-limit documentation](https://console.groq.com/docs/rate-limits).

The first q04 baseline/focused local Llama smoke executions both abstained. Their faithfulness and factual correctness remained unavailable. The local judge nevertheless labeled all baseline passages relevant, including eligibility, budget and audience passages. Its subsequent control test passed the relevant objective but falsely accepted all three irrelevant controls. Therefore its high raw relevance scores are not credible evidence of a 90% result. The quality gate blocks them.

Raw development evidence is retained in `docs/evaluation/quality-development-results.json` and `quality-judge-controls.json`. The next requirement is a judge that passes negative controls and independent review, plus generated answers that survive source validation. Increasing a raw judge score without fixing those problems would be misleading.

Primary metric definitions: [RAGAS metrics](https://docs.ragas.io/en/v0.3.1/concepts/metrics/available_metrics/). The installed project version is 0.3.9; the runtime uses its actual metric classes rather than substituting document-overlap formulas.

## Hosted development assessment: October 19, 2026

The owner-configured key was moved to the ignored local secrets file and its API connection verified. No credential is included in these artifacts.

- The separate GPT-OSS 120B passage judge passed the four relevance controls. This does not calibrate faithfulness or correctness.
- Seven objective questions scored 1.0 on all four quality dimensions with Qwen generation and focused context. These are repeated question templates, not seven independent task types.
- The first results/channel case had full context recall and faithfulness but failed the precision API's JSON validation. Increasing the hosted precision allowance from 256 to 1024 fixed that failure in a separate diagnostic. The earlier failure remains recorded.
- That same richer answer received 0.0 reference-based factual correctness. Claim-level diagnostics show why: the reference contains only activation counts, while the answer also includes source-backed attribution windows, spend, targets and balances. The strict reference comparison rejects the extra detail. All three reference claims were supported by the answer in the diagnostic. This does not establish that the richer answer is wrong, and does not justify replacing the recorded F1 with a higher score.
- Five separate unsupported-question executions produced three exact fallback responses and two cited explanations of unavailable measurements. The current exact-fallback metric counts only three of five (60%). One explanation says ROI cannot be calculated without financial return; the other states that age-level outcomes were not measured but also includes unnecessary campaign details. These observations need a prespecified semantic-refusal rubric rather than post-hoc relabeling.

The broader run was paused after eight supported cases. Its gate is **incomplete**, not a 90% pass. The five separate unsupported executions are not silently merged into it. Current-run output files now checkpoint each completed case so an interrupted run cannot leave an earlier summary in place. The final regression suite passed **113 tests**, with three framework deprecation warnings.

Evidence: [partial results](evaluation/quality-groq-development-results.json), [partial gate summary](evaluation/quality-groq-development-quality-summary.json), [initial smoke](evaluation/quality-groq-initial-smoke.json), [earlier executions](evaluation/quality-groq-pre-retry-executions.json), [channel diagnostic](evaluation/quality-groq-channel-diagnostic.json), [correctness reasons](evaluation/quality-groq-correctness-diagnostic.json), [faithfulness repeat](evaluation/quality-groq-faithfulness-diagnostic.json), [unsupported executions](evaluation/quality-groq-unsupported-cases.json). Diagnostics are separate executions and do not replace original scores.

### Remaining work before a defensible 90% claim

Independently author complete references and a semantic-refusal rubric before testing new questions, calibrate claim judges with both supported and unsupported claims, and run the complete set under one recorded configuration. Keep the existing references and results unchanged as a historical baseline. Evaluate recommendations, comparisons and final reports separately. The public defaults remain unchanged pending this evidence.
