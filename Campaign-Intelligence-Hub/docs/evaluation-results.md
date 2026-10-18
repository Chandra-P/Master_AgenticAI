# Evaluation status

The application writes real run outputs to `data/runs/latest/results.json` and `results.csv`. The dashboard remains empty until those files exist.

The experiment matrix has eight combinations: fixed/semantic chunking, dense/hybrid retrieval, and reranking disabled/enabled. Held-out cases exclude calibration items. `--smoke` uses one held-out question across the matrix; `--full` uses all held-out cases, including report and unsupported requests.

Faithfulness is currently unavailable as an independently judged metric. Do not interpret retrieval relevance, valid citation IDs, or string-matched completeness as a faithfulness score. Generated errors are retained in each result row; failed runs are not silently excluded.

Actual local verification results will be recorded after the first integrated run.
