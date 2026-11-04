# Week 2 requirements mapping

The handout permits a bring-your-own corpus. This project chooses campaign knowledge RAG. Capability, achieved quality and external submission are distinct.

| Requirement | Status and evidence |
|---|---|
| One-line use case and percentages | course-project.md defines 90% faithfulness and 80% passage relevance targets; not claimed achieved. |
| Corpus, ownership, ingestion, freshness | 130 English synthetic Markdown sources, including eight CL-640 requirements-pack documents; manifest hashing, validation and manual one-working-day refresh policy. |
| Chunk, embed, store, retrieve, cite | Active Ollama/Chroma RAG service with exact citation validation. |
| LangChain and LangGraph | Actual question graph in rag/workflow.py with explicit refusal branch and timing. |
| Chunking comparison and reranking impact | Historical 122-source corpus: completed 360-row retrieval/reranking matrix and 90-row generated-answer comparison across fixed, section and semantic chunking. See evaluation-results.md and chunking-answer-quality-comparison.md. |
| Ambiguous, multi-document, unsupported cases | Benchmark includes three new ambiguous and three multi-document cases with source gold, plus unsupported controls. |
| Faithfulness, precision, recall | Historical 122-source corpus: completed 30 questions for each of three chunkers with Ollama answers and calibrated OpenAI judgments. Conditional faithfulness and scoring coverage are explicit. Semantic leads observed overall reference correctness; quality targets remain unmet. |
| Latency ceiling | Warm p95 target 60 seconds. Observed 30-case answer p95 was 62.79 seconds; this run exceeds the target and does not certify a warm-load SLA. |
| Comparison and failure analysis | Separate submission documentation, outside runtime RAG features. |
| Google Doc | Three-page docs/submission/Campaign_Knowledge_RAG.docx prepared and visually checked. The owner chose local delivery; no native Google Doc was created. Native conversion remains an external course-submission step. |
| Video at most five minutes | Local docs/submission/Campaign_RAG_Walkthrough.mp4 is 2:06, with actual UI captures and AI-tool explanation. Explicitly edited text-narrated footage, not a continuous personal live recording; owner can use it to prepare the requested live presentation. |
| GitHub or assets | Repository: https://github.com/Chandra-P/Master_AgenticAI. Latest changes remain local; a credential-checked source bundle accompanies the local deliverables. |
| No API keys committed | Private environment or ignored Streamlit secrets only; source and artifact credential scan required. |

SEC ingestion, Pinecone, Jev, knowledge graphs and customer-support escalation belong to other example choices and are outside this project's scope.

Current corpus expansion: see [requirements evidence pack](requirements-corpus.md). It adds 13 development exercises, including three cross-document and two unsupported cases. New answer-quality and latency acceptance results remain unmeasured; historical scores must not be applied to the 130-source corpus. Local submission document/video and source bundle need refreshing before a new course submission.

Current 130-source answer evaluation: [expanded results](expanded-quality-results.md) reached 87.3% reference F1 across all 23 supported cases (22 answered), with 7/7 unsupported controls refused. Conditional faithfulness 100%; passage precision 34.2% remains below its separate 80% target. One multi-document question remains refused. This development result does not establish unseen accuracy or a latency SLA.
