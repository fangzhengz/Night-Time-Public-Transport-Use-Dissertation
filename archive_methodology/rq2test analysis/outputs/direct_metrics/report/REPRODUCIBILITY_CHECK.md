# RQ2 direct metrics reproducibility check

- Verification status: VERIFIED
- Command: `py -3 src/run_direct_metrics_analysis.py`
- Re-run date: 2026-07-02
- Permutations: 999
- Random seed: 42

The analysis was run twice. SHA-256 hashes matched exactly for:

- `bus_kruskal_wallis.csv`
- `centrality_adjusted_tests_all.csv`
- `rail_metrics_by_lnwc_fractional.csv`

The data audit also passed:

- Bus: 4,100 LSOAs, seven LNWC groups, no missing primary metrics.
- Rail: 254 eligible stations, no missing primary metrics.
- Maximum rail seven-share sum error: below `5e-16`.

Timestamped reports and workbook files were excluded from the hash comparison.

