# RQ1 context metrics reproducibility check

- Verification status: VERIFIED
- Command: `py -3 src/run_rq1_context_analysis.py`
- Re-run date: 2026-07-02
- Deterministic inputs: fixed RQ1 K=6 rail and K=4 bus labels

The analysis was run twice after correcting structural zero handling. SHA-256
hashes matched exactly for:

- `rail_cluster_metric_summary.csv`
- `bus_cluster_metric_summary.csv`

The data audit also passed:

- Rail rows: 270; missing primary metrics: 0.
- Bus rows: 4,100; missing primary metrics: 0.
- Maximum relative disagreement between recomputed activity and RQ1 metadata:
  below `9e-16` for both modes.

Timestamped reports and workbook files were excluded from the hash comparison.
