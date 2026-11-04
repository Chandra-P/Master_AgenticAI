# Retrieval design

Uploads accept UTF-8 TXT/Markdown and text PDFs, at most 2 MB, at most 50 PDF pages and 300,000 extracted characters. The filename is reduced to a sanitized basename; files are processed as bytes and never executed. SHA-256 checksum gives per-user idempotence. No OCR, archive extraction, remote URLs, or office macros are supported.

PDF text preserves page numbers. Blank-line sections become chunks, split at 1,200 characters when needed. Page and section metadata survive normalization. Injection-pattern lines are stored as quarantined chunks and excluded from retrieval and the source viewer. Legitimate neighboring facts remain available.

Default embeddings are deterministic 256-dimensional hashing vectors. Ranking combines cosine similarity (25%), token overlap (55%), and title overlap (20%). Tokens normalize common car/auto/interest terms. OpenAI embedding mode is configurable for uploads; seed vectors always remain local. Query embeddings are generated using the stored provider. This is a compact local retrieval system, not pgvector or a claim of general semantic-search quality.

Current retrieval filters by user, effective date, and explicit supersession. Comparison requests can include superseded offers. Results contain document/version/page/section/passage and a similarity score; this score is not financial confidence. The independent offer-authority check consults the complete eligible document registry, so top-K truncation cannot hide a conflicting current offer.

Loan projections require a unique current offer with evidenced vehicle price, APR, and term. The extractor uses labeled fields and distinguishes APR from late fees. Missing or conflicting fields cause abstention. Arbitrarily worded or scanned real offers may need manual normalization; the application does not guess terms.

## Injection model

Retrieved content is untrusted data. The OpenAI planner receives the question and a bounded route schema, not document passages as instructions. Synthesis is deterministic and displays quoted evidence with output escaping. No document can update memory, issue SQL, invoke a financial action, or access secrets. Pattern detection improves presentation but is not the primary authority boundary and is not a complete injection classifier.

## Version and conflict rules

Uploading a replacement requires selecting the accessible current document to supersede; versions increment and the previous record is retained. Matching filenames alone do not determine authority. Independent current offers block loan simulation until the user explicitly resolves supersession. Future-effective documents are not eligible under the fixed demo clock. Structured confirmed preferences override older narrative goals, with the discrepancy disclosed.
