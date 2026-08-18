# Bus cluster geography diagnostic

Answers a single question raised by Howard Wong at the 17 July 2026
supervisor meeting: the bus K=3 LSOA cluster map places central London
(Westminster, Camden) and outer suburbs (Kingston, Richmond Park) in the
same cluster -- is that a real feature of bus night-time usage rhythm, or
an artifact of K choice, uncertain classification, or LSOA-level
aggregation? Does **not** refit or modify the GMM clusters.

Three independent candidate explanations are tested, each against the fixed
`cluster_clean_version_fullweek` bus labels:

1. **K choice** (`run_geography_diagnostic.py`, section 1): does raising K
   from 3 to 6 improve how much distance-to-Charing-Cross explains cluster
   membership?
2. **Classification noise** (`run_geography_diagnostic.py`, section 2): does
   GMM assignment confidence (`max_posterior`) drop for units far from the
   centre or in low/high volume tiers?
3. **LSOA aggregation** (`run_lsoa_aggregation_check.py`): using
   pre-aggregation stop-level BUSTO data, how much stop-to-stop variance in
   proxy metrics sits between LSOAs vs within them?

A fourth, related question -- whether the K=3 partition is even internally
coherent for the continuous metrics it is conceptually closest to -- is
answered by a sibling script in `../rq1_context_metrics_analysis/src/
run_cluster_metric_significance.py` rather than duplicated here, since it
reuses that folder's already-built `bus_unit_metrics.csv`.

## Run

```powershell
py -3 src/run_geography_diagnostic.py
py -3 src/run_lsoa_aggregation_check.py
```

## Main outputs

- `outputs/data/bus_distance_eta2_by_k.csv`: eta^2 and Kruskal-Wallis
  epsilon^2 of distance-to-centre ~ cluster, for K = 3, 4, 5, 6.
- `outputs/data/bus_confidence_correlations.csv`,
  `bus_confidence_by_volume_tertile.csv`: assignment-confidence checks.
- `outputs/data/bus_stop_lsoa_variance_decomposition.csv`,
  `bus_stop_lsoa_audit.csv`: stop-level aggregation check.
- `outputs/report/RESULTS_SUMMARY.md`, `LSOA_AGGREGATION_CHECK.md`.

## Centrality reference

Charing Cross, British National Grid (530134, 180379) -- the same point
used by the RQ2 centrality-adjusted LNWC/IMD tests in
`../rq2test analysis/src/run_direct_metrics_analysis.py`, so this
diagnostic's distance measure is directly comparable to that analysis.

## Interpretation boundary

These are validity/robustness checks on the RQ1 bus clustering solution
itself. They do not test or replace the RQ2 cluster x LNWC/IMD linkage
analyses, which live in `../rq2test analysis/`.
