# Expanded-corpus answer quality results

**Reference F1 reached 87.3% on the fixed 30-case benchmark against the 130-source corpus.** The expanded-corpus baseline was 36.9%. Ollama remains the default answer provider; the approved OpenAI gpt-4.1-mini judge assessed actual answers. No OpenAI answer generation was used.

| Profile | Reference F1, all 23 supported | Supported answered | Unsupported refused | Faithfulness, answered only | Useful-passage precision |
|---|---:|---:|---:|---:|---:|
| baseline | 36.9% | 21/23 | 7/7 | 100.0% | 42.4% |
| factual-v1 | 79.8% | 22/23 | 7/7 | 99.2% | 42.4% |
| factual-k8 | 87.3% | 22/23 | 7/7 | 100.0% | 34.2% |

## What changed

1. Narrow objective questions extract a complete source section already present in retrieved evidence. The section must match its hashed parent source; fragments and conflicting objectives fall back to the model.
2. Narrow activation-results questions project actual totals and channel counts from retrieved Markdown tables. Source rows and headers are retained as proof. Counts must be nonnegative integers, scope must agree, values must be unique and channel counts must reconcile to the actual total. These are source-derived rendered facts rather than verbatim model quotations.
3. The complete query must match a narrow intent. Extra facets, unsupported year suffixes or an explicit mismatched campaign return to Ollama. Broader policies and explanations still use cited Ollama generation with exact-quote validation.
4. Returning eight of the same twenty retrieval candidates supplied channel tables missing at five. Semantic/hybrid/k8 is now the Python, CLI and app default; reranking and context focusing remain off.

## Measurement contract

All three profiles executed all 30 cases once, with zero execution errors: 23 supported questions and 7 unsupported controls. The primary score averages raw RAGAS factual-correctness F1 across all 23 supported questions; genuine supported refusals count as zero. Missing answered-case judgments would make the result incomplete. References and original case records were not changed. No newly authored development examples were added to the denominator to raise the score.

The two experimental profiles use the same grounding contract, model, references, scorer and corpus; only returned context count changes from 5 to 8. The baseline uses the preceding quote-generation contract. Protocol, exact samples, table proofs and model identities are saved in [protocol](evaluation/expanded-quality-protocol.json), [summary](evaluation/expanded-quality-summary.json) and [all 90 records](evaluation/expanded-quality-results.json). The current app loads only the winning 30 records from its version-checked local quality run. A separate reviewer checked all 90 records, denominator arithmetic and source proofs against current references/corpus.

## Remaining limitations

- This is a development benchmark whose cases have been inspected during improvement, not independent unseen validation or production certification. It is one run per profile; no confidence interval or reproducibility claim is made.
- The seventeen objective/count questions scored 1.0 each. The six complex questions averaged 51.5% F1. The consent/emergency-withdrawal multi-document question was still refused; other complex answers remained incomplete. Overall F1 benefits from the benchmark having more factual than complex questions.
- Useful-passage precision is 34.2%, below the separate 80% passage-relevance target. Meeting the reference-F1 goal does not satisfy every quality requirement. Faithfulness 100% applies only to the 22 answered supported questions.
- Judge claim matching is strict for terse references, as documented in the earlier q11 audit. Original references and scorer were preserved here rather than adjusted to inflate results.
- Trials overlapped; raw timings are retained but this was not a controlled latency comparison and does not certify the 60-second p95 target.
- The 13 newly authored requirements-pack exercises remain development-only. Their retrieval checks are separate from this fixed 30-case answer benchmark.

## Reproduce locally

With the project virtual environment and local Ollama models available:
```powershell
.venv\Scripts\python.exe -m campaign_hub ask --campaign TX-CHK-001 --question "What were the results and channel findings for TX-CHK-001?"
```
The default profile is semantic/hybrid/k8. To repeat optional judged evaluation with the owner key kept in ignored settings:
```powershell
.venv\Scripts\python.exe -m campaign_hub evaluate --ragas --quality --ragas-limit 30 --judge-provider openai --judge-model gpt-4.1-mini
```
Repeating a run may produce different model judgments. The legacy all-metric 90% quality gate remains distinct from the 80% reference-F1 goal and must not be reported as passed.

## Verification

145 non-live tests passed, with three existing RAGAS deprecation warnings. Streamlit AppTest confirmed the semantic default and the displayed 87.3% caption with the complete 23-question denominator. No commit or push was requested.
