# Ragas Group Fit Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional Ragas scoring to the existing live synthetic Group Fit RAG evaluation.

**Architecture:** The existing evaluator remains responsible for creating synthetic plans, Pinecone retrieval, Group Fit calls, and cleanup. A small isolated adapter captures actual prompt evidence, constructs Ragas samples with synthetic references, invokes Ragas only when the opt-in flag is set, and adds per-case/aggregate scores to timestamped reports. Ragas is an evaluation-only dependency and never loads in API runtime or ordinary CI.

**Tech Stack:** Python 3.12, uv dependency groups, Ragas metrics, existing OpenAI/Pinecone providers, pytest.

**Spec:** `docs/superpowers/specs/2026-11-10-ragas-evaluation-design.md`

## Global Constraints

- Synthetic content and temporary `eval-` source IDs only.
- Do not read production `DATABASE_URL`, Supabase service credentials, or production plan namespaces.
- Ragas model calls are opt-in and excluded from ordinary CI.
- Never treat a Ragas score as proof; report scores and deterministic checks separately.
- Cleanup only synthetic vectors created by this run and report any cleanup failures.

## Review Focus

- No Pinecone hit: score an empty retrieved-context set without inventing evidence.
- API/model/Ragas failure: preserve deterministic results, record a scoped metric error, and still run synthetic cleanup.
- Mixed evidence origins: score grounding against exact prompt evidence while scoring retrieval only against Pinecone contexts.
- Sensitive data: ensure evaluator inputs and artifacts contain only synthetic case content.
- Metric/version drift: pin the Ragas release and test the adapter's sample-to-metric mapping.

---

### Task 1: Add tested Ragas input and result adapter

**Files:**
- Create: `backend/tagalong/ragas_eval.py`
- Test: `backend/tests/test_ragas_eval.py`

**Interfaces:**
- Produces `build_ragas_sample(case, evidence, output)` returning the single-turn fields `user_input`, `retrieved_contexts`, `response`, and `reference`.
- Produces `serialize_ragas_scores(metric_results)` returning JSON-safe per-metric scores and errors.

- [ ] **Step 1: Write failing tests** for correct prompt-vs-Pinecone context separation, empty retrieval handling, response normalization, and serialization of success/error results.
- [ ] **Step 2: Run the tests** and confirm they fail because the adapter is absent.
- [ ] **Step 3: Implement the two adapter functions** with no import-time Ragas dependency.
- [ ] **Step 4: Re-run adapter tests** and confirm they pass without credentials or Ragas calls.

### Task 2: Integrate opt-in Ragas scores and synthetic references

**Files:**
- Modify: `backend/scripts/evaluate_group_fit.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Test: `backend/tests/test_rag_evaluation_support.py`

**Interfaces:**
- The existing evaluator accepts an explicit `--ragas` flag; default behavior stays Ragas-free.
- Ragas results add `ragas_evaluation` with `status`, `judge_model`, `metrics`, per-case details, means, and errors to both report formats.

- [ ] **Step 1: Write failing tests** proving the flag defaults off and the live Ragas adapter receives actual captured evidence, generated output, and synthetic reference facts.
- [ ] **Step 2: Run tests** and confirm the missing opt-in behavior fails.
- [ ] **Step 3: Add a pinned evaluation dependency group** and lock it without adding Ragas to runtime or default CI dependencies.
- [ ] **Step 4: Capture exact prompt evidence and run opt-in Faithfulness, Answer Relevancy, Context Precision, and Context Recall scoring** for eligible synthetic cases.
- [ ] **Step 5: Preserve deterministic results and cleanup on Ragas failures**; record per-metric errors instead of losing the whole evaluation artifact.
- [ ] **Step 6: Run focused tests** and confirm the default evaluator does not import/call Ragas.

### Task 3: Document use and limitations

**Files:**
- Modify: `docs/GROUP_FIT_RAG.md`

- [ ] **Step 1: Document the opt-in command, evaluator credential names, synthetic-only scope, expected extra model calls, report fields, and metric limitations.**
- [ ] **Step 2: Verify documented commands against the evaluator CLI and ensure no credential values are written.**

### Task 4: Verify the full evaluation change

**Files:** all files above

- [ ] Run backend pytest and the isolated Ragas adapter tests.
- [ ] Run the live Ragas evaluator only with explicit synthetic-only scope and configured evaluator credentials.
- [ ] Verify generated report content and synthetic Pinecone cleanup results.
- [ ] Run lint/type checks required by project CI and confirm no runtime dependency or regular CI path calls Ragas.
