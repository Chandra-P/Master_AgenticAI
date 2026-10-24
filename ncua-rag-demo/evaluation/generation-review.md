# Live generation review

The same 15 questions were sent to the local Python API using fixed chunks, reranking, and Groq's openai/gpt-oss-20b. Requests were spaced by 12 seconds; all returned HTTP 200, with no application rate-limit responses.

Eight answers were displayed (Q01, Q03, Q04, Q05, Q07, Q08, Q09, Q11). Three drafts failed validation even after one repair attempt and were withheld (Q02, Q06, Q10). Q12 returned partial evidence, and all three negative questions abstained (Q13–Q15). Thus 8 of 12 evidence questions produced a generated answer; this coverage must accompany any quality statement.

Manual inspection compared each displayed answer with its cited source row, including institution, period, amounts and reported annual changes. The figures in all eight displayed answers match those rows. Q03 and Q11 preserve the delinquent-loans/assets denominator but omit an explicit ratio unit; the original table remains necessary. This is a small, developer-reviewed source-support check, not an independent semantic faithfulness benchmark. The 0.90 faithfulness target is not established by this check, and machine-readable faithfulness remains null.

Q02's inspected failed draft calculated a new multi-year growth amount and percentage, despite the prompt asking for reported annual changes. The numeric validator rejected it. Mechanical numeric and citation validation cannot detect every misleading interpretation; withholding output also reduces usefulness.

The reported API processing p95 across these 15 requests was 5.888 seconds (nearest-rank calculation). This includes local retrieval and generation, but excludes UI and external network latency. The collection code originally overwrote client timing with the API's seconds field; it now records client_seconds separately for future runs. These saved results cannot establish public end-to-end latency or load performance.

Retrieval results remain in comparison-report.md. They are separate from answer-generation results. The first collection attempt is retained as generation-first-run.json for comparison; it included rate-limit errors and used a shorter request interval.
