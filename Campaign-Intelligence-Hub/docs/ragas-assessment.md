# RAGAS answer and passage assessment

For passage-fraction precision, reference-based factual correctness and the complete-set 90% gate, see [quality-target.md](quality-target.md). New negative controls showed that the local Llama judge falsely accepted irrelevant offer, budget and audience passages. Earlier smoke scores remain recorded observations, not validated evidence of 90% quality. Quality assessment now stops before answer generation if the judge fails these controls.

The optional evaluator uses **actual RAGAS 0.3.9**, through its LangChain model wrapper. It is separate from the document-ID overlap metrics in the retrieval experiment. A RAGAS score is a model judgment, not proof that an answer is correct.

Context precision uses a compact application prompt and schema-constrained binary verdicts. The output allowance is 256 tokens for Ollama and 1024 for Groq; the smaller hosted allowance produced invalid JSON on a richer passage. Every ranked passage is still judged individually, and RAGAS computes the unchanged average-precision formula. The prompt version/hash and output budget are recorded. This customized judge prompt is not the same prompt used by the peer financial-document kits.

| Metric | What is assessed |
|---|---|
| `ragas_faithfulness` | Fraction of answer claims judged supported by the retrieved passages |
| `ragas_context_precision` | Rank-sensitive precision from passage relevance judgments against the question/reference answer (`LLMContextPrecisionWithReference`) |
| `ragas_context_recall` | Fraction of reference-answer claims attributable to retrieved passages (`LLMContextRecall`) |

These follow the [official RAGAS metric definitions](https://docs.ragas.io/en/v0.3.9/references/metrics/) and [LangChain integration](https://docs.ragas.io/en/v0.3.9/howtos/integrations/langchain/). This implementation does not use RAGAS answer relevancy, internal embedding-based answer similarity or OpenAI inference. Some OpenAI integration packages are transitive evaluator dependencies; no OpenAI key or paid API is required for the local profile.

## Run a small assessment

```powershell
cd Campaign-Intelligence-Hub
.venv/Scripts/python.exe -m pip install -r requirements-ragas.txt
$env:CIH_EMBEDDING_PROVIDER='sentence_transformers'
$env:CIH_EMBEDDING_MODEL='sentence-transformers/all-MiniLM-L6-v2'
$env:CIH_GENERATION_PROVIDER='ollama'
$env:CIH_GENERATION_MODEL='llama3.2:3b'
.venv/Scripts/python.exe -m campaign_hub index --chunking all
.venv/Scripts/python.exe -m campaign_hub evaluate --ragas --chunking section --ragas-limit 1
```

Ollama must be running with the selected generation model. CPU embeddings download once; if compatible indexes already exist, rebuilding is unnecessary. The optional requirements pin the evaluator and compatible adapter dependencies; they are deliberately separate from normal hosting requirements. RAGAS 0.3.9 requires the legacy adapter retained in `langchain-community==0.4.1`; 0.4.2 removes it. The LangChain RAGAS wrapper is deprecated upstream but works with this pinned/tested stack. Upgrading the evaluator or adapters requires rerunning framework and live tests.

The default assesses **one held-out question and the selected configuration**. `--ragas-limit 10` selects up to ten held-out question cases. Add `--full` to assess all twelve chunking/retrieval/reranking configurations. Each answer and metric can require multiple inference calls; start small. No full benchmark runs on app startup or visitor navigation. Calibration, analytical-report and unsupported-question cases are excluded from this question-answer benchmark. Full report quality and abstention accuracy require separate evaluations.

Use `--judge-model MODEL --judge-provider ollama` to select another locally installed judge. A Groq generator/judge is supported via the existing owner-supplied server key and `--judge-provider groq`; its model availability, structured response quality and free-tier quotas affect success. Provider errors remain visible as missing judgments. A different model can reduce shared-model bias but still does not constitute independent human validation.

## Artifacts and interpretation

Results are saved under `data/runs/ragas/latest/`: JSON rows, CSV scores and one preserved JSON artifact per execution. Each row records:

- The actual generated answer, exact ranked retrieved passages, question and reference answer.
- Chunk/document IDs, corpus version, chunker and embedder configuration, generation/judge provider and model, RAGAS version and metric timeouts.
- Available scores, per-metric failures, generation/total latency, abstention status and whether generator/judge models match.

Assessment failures and NaN/out-of-range scores remain null. Faithfulness is unavailable for empty/abstention answers; missing contexts make all three metrics unavailable. Passage precision/recall may still be assessed for an abstention with retrieved evidence. Error summaries exclude provider request bodies and credentials. RAGAS usage tracking is disabled by the adapter.

The retained development Evaluation Dashboard (outside public app navigation) shows these saved results separately, with measured-case counts and the actual generation/judge profiles. It can display a bundled local smoke artifact without installing RAGAS on the web host. A saved local Llama assessment is not a measurement of the live Groq deployment. Results from a different corpus or assessment schema are rejected. Raw answers/passages/reference answers can be inspected.

Our source-derived synthetic gold and conservative verbatim answer validation make this a constrained demonstration. A small run, perfect score on one easy example, or a same-model judge does not establish broad factual accuracy. Peer financial-document scores are not directly comparable: their corpus, questions, reference answers, models and retrieval configurations differ.

## Verification on 2026-10-18

The precision fix passed the full **101-test** regression suite, including strict binary verdict validation and real RAGAS ranked-scoring behavior.

- **100 tests passed**, including actual RAGAS calculations from known judge verdicts, exact sample capture, score/error handling, repeated-event-loop use, JSON-mode configuration and dashboard rendering. The installed optional stack passed `pip check`.
- Two real local Llama 3.2 CPU cases completed before the JSON-mode fix. For q04, context recall was **1.0**, faithfulness was unavailable because the application abstained, and context precision failed parsing. For q05, faithfulness was **0.75**, context recall **1.0**, and context precision timed out. Total per-case times were 197.0 and 424.4 seconds. The [raw smoke artifact](evaluation/ragas-smoke-results.json) preserves all scores, unavailable judgments and the original JSON-mode setting.
- Precision prompt v2 was then verified on the exact saved q05 answer and all five original ranked passages, with no answer regeneration. Context precision completed at approximately **1.0** in **55.9 seconds** of verification wall time, under a 90-second metric timeout. This row reassesses precision only; faithfulness and recall are deliberately unavailable for that execution. The original failures remain in the artifact. Prompt versions and JSON settings are distinct chart groups.
- A complete independently judged benchmark remains pending. These small smoke/fix checks are not a full model-quality benchmark; neither the original pre-fix results nor one successful precision result establish the current app's overall accuracy.
- The generator and judge used the same local model. These results are neither independent validation nor a measurement of the hosted Groq model. The original 324-row retrieval experiment remains separate and has no generated-answer faithfulness scores.
