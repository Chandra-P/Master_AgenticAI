# Credit Union Evidence Lab demo script

Target duration: four minutes thirty seconds. Record the real public application and narrate the steps below. Do not show configuration files, API keys, or hosting secrets.

## 0:00 to 0:35 — Purpose and corpus

“This is Credit Union Evidence Lab, a document-only RAG application for financial analysts. It explores assets, lending, and reported financial ratios from original NCUA documents. This snapshot contains 18 reports for nine credit unions, covering annual periods from 2021 through 2025. It does not claim nationwide rankings.”

## 0:35 to 1:35 — Live answer and evidence

Choose Navy Federal and 2025. Ask: “What were Navy Federal total assets in 2025?” Show the answer, expand its citation, then open the original source table. Point out the reporting period and USD amount. Explain that these are original online HTML reports, so citations use table/row references rather than invented PDF page numbers.

## 1:35 to 2:15 — Historical question and ratio meaning

Ask: “How did Alliant total loans change from 2023 to 2025?” Show the retrieved balances and the source's reported annual %Chg columns. Explain the difference between reported growth and a computed multi-year change. In the risk example, note that delinquent loans divided by assets is a different ratio from delinquent loans divided by total loans.

## 2:15 to 2:45 — Insufficient evidence

Ask for Navy Federal assets in 2030 and show the insufficient-evidence result. Then demonstrate that a broad comparison without all required institution/metric evidence produces a partial-evidence message instead of a definitive ranking.

## 2:45 to 3:45 — Experiments

Open Experiments. Explain the same 15 questions are used for fixed-size and semantic chunking, each with reranking off and on. Recall@5 improves from about 91.7% to 95.8% with reranking. Explain that the difficult cross-document question still misses evidence and that retrieval recall is not generated-answer faithfulness. Show the per-query question list and the downloadable comparison report.

## 3:45 to 4:15 — Implementation and AI coding tools

“I used Codex to help plan, implement, test, and review the application. LangChain provides Documents, text splitting, the Chroma integration, and ChatGroq. LangGraph coordinates retrieval, evidence checks, and generation. Local MiniLM models embed and rerank passages. ChromaDB persists vectors and citation metadata. Groq generates only after the evidence gate passes.”

## 4:15 to 4:30 — Learnings and limits

“The main learnings were preserving financial table headers, checking ratio denominators, and evaluating retrieval before trusting answers. The UI is public; this demonstration's live Python backend requires the local computer and tunnel to stay online. An always-on backend is a separate deployment step.”
