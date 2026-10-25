# Campaign metadata classification and analyst view

## Intent

Add the three Week 2 capabilities requested by the user to the existing Campaign
Intelligence Hub: automatic metadata classification with local Ollama, combined
metadata filters, and an analyst view showing applied filters and retrieved
evidence. Keep existing report and history workflows available. No OpenAI API
keys are committed. The user approved implementation with OpenAI as an optional
alternative; Ollama remains the default.

## Approach

The user's request selects the extension proposed in the preceding review:
reuse Streamlit, the CampaignService, local structured Ollama generation, and
the Chroma/dense/BM25 pipeline. A separate application or a vector-store migration
would add no necessary capability and is outside this request.

## Filter contract

- Supported fields: campaign ID, client name, campaign type, region, year,
  reporting period, and document type. Values come from the actual corpus
  manifest, including shared guidance where its metadata supports the selection.
- Multiple selected values in one field mean OR; different fields mean AND.
- Validate fields and values before querying. Neither model output nor users
  can supply arbitrary Chroma operators.
- Manually selected constraints are binding. Intersect inferred constraints
  with them. Conflicts produce an explicit empty/conflict result, never an
  unfiltered retry. Unknown classifier values produce a visible validation error.
- Do not invent quarter/date conversions, channel metadata, or filters absent
  from the corpus. Existing campaign selection remains binding in Ask Questions.
- Apply the identical effective predicate to dense and BM25 candidate sets.

## Local automatic classification

Use a structured schema and a dedicated local Ollama classifier, defaulting to
llama3.2:3b at the configured local Ollama URL. Pass the available field values
and instruct it to include only constraints supported by the question. Empty
classification is valid for a general question. Treat the question as data,
not instructions to change the schema or scope.

Each inferred constraint includes exact supporting words from the question;
reject constraints whose supporting words are absent. This checks provenance,
not complete semantic entailment. Model output still needs analyst inspection.
Constrain candidate values to explicit labels or supported aliases mentioned in
the question; do not derive campaign IDs or quarters from region/year. General
questions with no recognized metadata terms skip classification. Manual controls
support remaining paraphrases and explicit shared ALL/GLOBAL values.

Classification defaults to local Ollama regardless of the answer provider.
Allow explicit OpenAI classification and optional OpenAI answer generation,
using a server-owned OPENAI_API_KEY from the environment or ignored Streamlit
secrets. Never accept a key through a widget or silently change providers.
Show an actionable local-model error if Ollama is
unavailable. Permit a deliberate manual-only mode; never silently substitute a
cloud model or ignore a classifier failure.

## User interface

Add an Analyst View navigation entry. Provide a question, combined metadata
controls, automatic-classification control, and the existing chunking,
dense/hybrid, and reranking settings. Run inference and retrieval only on explicit
submission. Cheap input reruns hide stale results immediately without inference;
no expensive work runs on edits.

Display manual filters, inferred filters, and effective filters separately.
Show retrieved evidence with rank, document identity, metadata, chunk text, and
available dense/BM25/reranking scores. Label scores according to their method;
do not present them as confidence or probabilities. Explain empty results and
conflicts. Invalidate displayed results when the query, filters, retrieval
settings, or corpus change.

Extend Ask Questions with the same filter/classification path and applied-filter
disclosure, retaining its selected campaign scope and existing source validation.
Do not change client report calculations or historical comparison eligibility.

## Verification

Write regression tests before implementation for value validation, AND/OR
semantics, manual/inferred intersections, conflicting scopes, and local-only
classification. Verify real Chroma filtering and BM25 scoping on the same test
corpus, including empty results. Test the Streamlit analyst submission and stale
result handling without a live model. Run the existing Campaign regression suite.
Finally smoke-test actual local classification and retrieval against Ollama and
the existing corpus, with OpenAI credentials removed. Scan changed files for
credentials before completion.

## Boundaries

No new real-data ingestion, authentication, production tenancy, benchmark quality
claims, calibrated confidence, graph restructuring, or unrelated model migration.
Do not commit or push this feature unless requested. The user approved
implementation, including the optional OpenAI alternative.
