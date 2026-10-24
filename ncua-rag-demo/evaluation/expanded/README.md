# Expanded retrieval experiment

Read comparison-report.md for measured results, results.json for all passages and metrics, and questions.json for the frozen labels. Original evaluation/questions.json and results.json are unchanged.

To repeat from the project root with the installed dependencies and cached models:

```powershell
python scripts/evaluate_expanded.py
```

The two pre-existing Chroma indexes are read without rebuilding or tuning. No Groq generation calls occur. This study has 38 questions, including 32 evidence questions and 6 negatives. The original benchmark UI remains labeled as the earlier 18-report snapshot. The expanded report is separately available at /expanded-comparison-report.txt on the running demo.

## PDF membership-table repair and frozen evaluation

Five Navy Federal Financial Summary rows now have validated table passages preserving institution, both consecutive year columns, exact integer membership counts, units, and physical PDF page. These supplement existing text without replacing it. Ambiguous headers, malformed counts, equity labels, and unsupported layouts are rejected; no OCR or count inference is performed. The audit is data/supplemental/membership-table-audit.json. Index counts are 2,156 fixed and 1,896 semantic chunks. Incremental indexing embeds added/changed passages only.

All 45 regression tests pass. The identical 38-question set (SHA-256 b7cd2413d36e7477f29dd6a3722abdde5c771df69a7f0736c3cd5e7e5a109ff9) was rerun after indexing. Exact membership evidence improved from 0/5 to 5/5 for every configuration. With reranking, combined Recall@5 rose from 0.828 to 0.984 for fixed and 0.818 to 0.974 for semantic; MRR rose from 0.844 to 1.000 and 0.812 to 0.969 respectively. Negative-case empty-retrieval accuracy remains 5/6. This does not establish a semantic advantage. The repair was motivated by known test failures, so this is a regression evaluation rather than independent held-out evidence. Generation is not measured by this retrieval benchmark.

Original results are preserved in evaluation/expanded/pre-table-fix/; new results, frozen labels and before-after report are in evaluation/expanded/post-table-fix/. Repeat with python scripts/evaluate_after_table_fix.py after building indexes. Public report path: /pdf-table-fix-comparison.txt.
