# Requirements corpus expansion plan

User instruction: Generate new corpus data to satisfy the requirements. Keep Ollama default; no authorization inferred for OpenAI answer generation.

Design: Add eight original fictional source documents with explicit scope, stable IDs, headings/tables or coherent mixed-topic prose. Cover measurement ambiguity, attribution timing, source/version precedence and cross-document release/receipt handling. Preserve all122 existing sources and all existing benchmark questions byte-for-byte as source records. Add development exercises with exact supporting facts, document citations and transparent authored provenance. Do not inject answers for old benchmark questions or relabel development examples as unseen evaluation.

Alternatives: Repeating campaign templates would inflate size without adding useful chunking structure. Generating with a hosted model is unnecessary and was not requested. Author deterministic source content locally and integrate it with the existing generator.

Tasks:
1. Add failing contracts for new source coverage, metadata/hash validity, deterministic regeneration, preservation of old documents/cases and genuinely distinct multi-document development facts.
2. Implement a focused requirements_corpus module and integrate generation without modifying the old source module. Use eight new development single-source cases plus multi-document and unsupported development cases.
3. Generate the new corpus, validate, inspect actual token lengths/chunk spans and run tests. Rebuild indexes if available; never present old benchmark measurements as current for the changed corpus.
4. Update requirements and corpus documentation with actual counts and limitations. Review source consistency and clean artifacts for secrets. No commit or push requested.

## Results
- Generated eight source documents and13 development cases; corpus130, development25, legacyheldout30, calibration3. Archived prior manifest/questions privately before generation.
- All122 prior source metadata/content hashes and45 prior question records verified unchanged against the pre-change backup. No held-out gold edits.
- Full non-live suite passed138 tests, with three existing RAGAS deprecation warnings. Source-consistency review and revised cross-document review found no material issues.
- Local indexes rebuilt: fixed180, section580, semantic788. All eight new documents have exact canonical chunk spans and <=500 tokens per chunk. The39 retrieval diagnostics found all gold documents on all11 supported development exercises per chunker; unsupported retrieval is not refusal accuracy.
- Current corpus docs updated; historical122-source metrics retained and labeled historical. Submission DOCX/video/sourceZIP remain earlier-corpus assets and are explicitly marked for refresh before resubmission.
- API-key scan of new source/data/validation files passed. No OpenAI calls, provider change, commit or push. No new generated-answer F1/faithfulness claim.
