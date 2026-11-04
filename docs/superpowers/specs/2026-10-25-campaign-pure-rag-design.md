# Campaign Intelligence Hub: pure RAG workspace

## Intent

The user wants report generation removed from the RAG solution and a corpus that
demonstrates different chunking techniques. The active application should answer
questions from retrieved source evidence and explain retrieval behavior.

## Proposed approach

Refactor the existing application into a RAG workspace rather than building a
second app. Preserve existing corpus attribution and source reports as input
documents; remove generated campaign reports, KPI dashboards and historical
comparison workflows from active app navigation and CLI commands. Historical
export artifacts remain archival examples, clearly identified as outside the
current application. Do not delete unrelated source material or private settings.

An alternative is only hiding the report tab. That leaves report generation
coupled to the active service and evaluation and does not meet the requested
separation. The proposed refactor instead gives retrieval and grounded answers
their own service boundary, with no report-rendering dependency in the live path.

## Active application

1. **Ask Questions:** question -> validated metadata constraints -> dense/hybrid
   retrieval -> optional reranking -> context -> generated answer with citations.
   Keep current source validation and explicit insufficient-evidence responses.
   Allow corpus-wide questions and optional campaign scope instead of requiring
   one campaign for every question.
2. **Analyst View:** retain manual/inferred/effective filters, ranked chunks,
   metadata, source text and method-labeled scores. Manual scope stays binding.
3. **Chunking Lab:** inspect the same source document under fixed-size,
   section-based and embedding-based semantic chunking side by side. Show chunk
   text, count, token lengths, boundaries, overlap and relevant source spans.
   Compare retrieved evidence for the same query and filters across all three
   chunking indexes. Semantic boundaries must use real embeddings.
4. **Evaluation:** question-answer/retrieval cases only; report-generation cases
   must not enter current RAG scores. Show configuration and corpus identity,
   measured coverage, precision, recall and unavailable faithfulness explicitly.
   Do not carry historical scores forward as results for the expanded corpus.

Ollama remains the default for embeddings, classification and generation.
Keep explicitly selected OpenAI classification/answers optional, using private
server configuration. No committed keys and no automatic cloud fallback.

## Corpus expansion

Add approximately twelve original, clearly labeled synthetic campaign knowledge
documents, using compatible manifest metadata and deterministic generation.
Use genuinely different document structures rather than padding existing text:

- Long playbooks with meaningful headings and several related sections.
- Cohesive long policies that cross the fixed token-window boundary.
- Mixed-topic operational notes with weak or missing headings, useful for
  observing semantic segmentation independently of heading boundaries.
- Troubleshooting/FAQ material with identifiers, exceptions, tables and facts
  near section/window boundaries to exercise lexical and semantic retrieval.

Aim for roughly 1,200–2,500 tokens per added document, adjusting actual lengths
after inspecting the produced chunks. Do not claim semantic chunking wins every
case. Preserve existing sources and hashes; add explicit new IDs and a versioned
manifest. Add curated questions with expected source evidence and distinguish
development examples from held-out measurement cases.

## Verification and operation

- Regression tests prove active UI/CLI no longer expose report generation and
  the RAG path does not depend on report rendering/calculation workflows.
- Tests cover grounded answers, combined-filter consistency, conflicting scopes,
  corpus-wide versus selected-campaign retrieval, citations and abstention.
- Chunking tests cover real source-span alignment, token limits and overlap,
  long sections, heading-free topic changes and preserved source metadata.
- Rebuild compatible indexes for the expanded corpus; stale indexes and cached
  scores must be rejected. Retain old collections/artifacts for recovery.
- Perform local Ollama question/retrieval checks and actual chunk comparisons;
  record measured counts/results without substituting fabricated quality scores.
- Update README and run instructions around the active RAG workflows, run the
  relevant full regression suite and scan publishable changes for credentials.
- Leave changes uncommitted/unpushed unless the user requests publication.

## Approval

Approved by the user on October25,2026 and implemented under the linked
implementation plan. Verification and local runtime results are recorded there.
