# Three chunking methods

The application supports three distinct methods through the same LangChain embedding interface, Chroma retrieval pipeline, report workflow, and evaluation cases. The default remains section-based because it preserves the existing campaign-document structure. There is no assumption that one method wins on every question.

| UI label | CLI value | Boundary rule | Embeddings used to choose boundaries |
|---|---|---|---|
| Fixed-size | `fixed` | 500 cl100k_base tokens, with 50-token overlap on overflow | No |
| Section-based | `section` | Markdown headings, with bounded windows for long sections | No |
| Embedding-based semantic | `semantic` | Sentence/unit cosine-distance changes above the document's 65th percentile | Yes |

All three methods subsequently embed their final chunks for Chroma search. Semantic chunking additionally embeds the sentence/unit text before deciding boundaries. It uses the configured embedding model; no generation API call is needed to split documents. Segmentation embeddings are batched across the corpus and use the provider's content-addressed cache.

## Semantic algorithm

1. Validate source metadata and remove YAML/title material through the existing Markdown ingestion contract.
2. Construct the same cleaned heading/body source text used for source reconciliation. Split paragraphs into sentence spans using punctuation boundaries; retain contiguous Markdown tables as units.
3. Embed the units using the configured LangChain-compatible embedding provider. Validate vector count, dimensions, finite values and nonzero norms.
4. Normalize vectors, calculate adjacent cosine distances, and split where distance is strictly greater than the document's 65th-percentile distance. Tied distances do not create arbitrary boundaries. Headings are source context and citation metadata; they do not force semantic boundaries.
5. Apply 500-token bounds to oversized groups, with 50-token overflow overlap. Every output is an exact character span of cleaned source text. Unicode characters are not decoded from incomplete byte fragments.
6. Store source/section anchors, character offsets, token counts, threshold, percentile, boundary reason and segmentation-model identity. A multi-section chunk retains all intersecting anchors. Tables within the token budget remain intact; oversized tables must still obey the bound and may split. Final reports expand validated parent documents to recover complete source tables.

The percentile is a recorded baseline, not a tuned optimum. Rule-based sentence boundaries are not a linguistic parser. The tokenizer used for the 500-token course comparison differs from model-specific tokenizers; the CPU embedding adapter separately windows and pools text within its model's actual limit.

## Index and measurement isolation

Collection names and manifests include the strategy, chunker version/parameters, tokenizer version, and embedding identity. Old heading-based `semantic` collections are not reused as embedding-based semantic indexes. The former method is now named `section`. Existing collections are retained; a new index is built rather than relabeling old vectors.

Experiment identities also include the actual per-strategy configuration. Earlier evaluation rows whose `semantic` key meant headings remain historical records and are rejected as current measurements by the dashboard. Current evaluation uses twelve configurations: three chunkers × dense/hybrid × reranking off/on. Faithfulness remains unavailable unless a support judge actually ran; document precision/recall are not RAGAS token-level or model-judged context metrics.

Multi-section chunks retain overlapping anchors for source inspection. Claim-level section scoring resolves the exact text span to one section; ambiguous, cross-section and unidentified leading partial spans remain unavailable. Document citation overlap and section-resolution coverage are reported separately. Exported whole-chunk references list actual section anchors rather than inventing a `#document` section. See [measured results](evaluation-results.md) for the current experiment and its limits.

## Reproduce

```powershell
python -m campaign_hub index --chunking all
python -m campaign_hub client-report --campaign TX-CHK-001 --chunking fixed
python -m campaign_hub client-report --campaign TX-CHK-001 --chunking section
python -m campaign_hub client-report --campaign TX-CHK-001 --chunking semantic
python -m campaign_hub evaluate --full --extractive
```

For the hosted CPU profile, set `CIH_EMBEDDING_PROVIDER=sentence_transformers` and `CIH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2` before those commands. Local defaults use Ollama. Hosted startup prepares all three compatible indexes automatically. Changing model or chunker configuration requires the corresponding isolated indexes; there is no silent structural fallback on semantic-model failure.

The implementation uses [LangChain's embedding contract](https://docs.langchain.com/oss/python/integrations/embeddings) and [cosine similarity between sentence embeddings](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html). It implements the application splitter directly and does not require the experimental LangChain package.
