# Retrieval ablation: group-aware option comparison

Date: 2026-11-06  
Scope: deterministic backend contract test; synthetic content only.

## Question

Does plan evidence change the option assessment, or is retrieval only stored and queried without affecting generation?

## Setup

`backend/tests/test_research.py::test_saved_plan_evidence_changes_option_assessment` uses a synthetic restaurant result, a synthetic saved preference note, and a deterministic assessment adapter. It makes two otherwise equivalent requests:

1. With the group's saved vegetarian preference available, the adapter returns a `fits` assessment citing that saved source; the evidence validator accepts the citation and the result is ordered accordingly.
2. After removing the unique saved preference source, the response cannot claim the same group-supported match and instead returns `needs_info`.

The test also verifies the retrieval query includes the requested option category, destination, plan dates, and confirmed preferences, while excluding unconfirmed preferences. Provider outages preserve public results and disclose that comparison was unavailable. Invalid source IDs cannot be cited as evidence.

## Result and interpretation

The ablation passes and demonstrates that the saved plan evidence changes the assessment in this controlled scenario. This is meaningful RAG behavior for “Does this option fit our group?” because evidence is retrieved before comparison, source IDs are validated, and the cited evidence can change the answer.

This is not a quality benchmark. The model response is deterministic in this test, and it does not measure retrieval precision/recall or prove that Pinecone uniquely contributed: current Notes are also supplied directly for indexing freshness, and the same context may exist in PostgreSQL. Pinecone is intended to semantically find relevant unstructured plan history. PostgreSQL remains authoritative for votes, confirmed preferences, budget and decision state.

## Reproduction

From `tagalong/backend` in the repository environment:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/test_research.py -q
```

This test uses no live OpenAI or Pinecone requests, production plan data, external API, or writes to a deployed service. See [Group fit RAG](../GROUP_FIT_RAG.md) for the product flow and limitations.
