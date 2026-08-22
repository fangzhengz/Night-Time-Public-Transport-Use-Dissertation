# RQ1 context-metrics analysis

This is a non-destructive interpretation layer for the provisional
`cluster_clean_version_fullweek` RQ1 result. It does **not** refit or modify the
GMM clusters.

The analysis adds three dimensions that were deliberately excluded from the
shape-normalised clustering:

- activity volume;
- entry/exit or boarding/alighting balance;
- interpretable timing ratios, including common-window and Night Tube extension
  measures for rail.

Rail and bus are analysed separately. Volume bands are therefore mode-specific
tertiles and must not be compared across modes.

## Run

```powershell
py -3 src/run_rq1_context_analysis.py
node src/build_workbook.mjs
py -3 src/run_cluster_metric_significance.py
```

`run_cluster_metric_significance.py` must run after
`run_rq1_context_analysis.py` (it reads `*_unit_metrics.csv`). It tests
whether the cluster label explains variance in its own continuous profile
metrics (metric ~ cluster, Kruskal-Wallis + epsilon^2) -- the piece needed
to tell whether a weak cluster x LNWC/IMD association (see
`../rq2test analysis/`) reflects a genuine shape-vs-intensity distinction or
an internally incoherent partition. See
`outputs/report/CLUSTER_METRIC_SIGNIFICANCE.md` for the answer. Related: the
bus-specific geography/aggregation validity checks live in the sibling
folder `../rq1_bus_geography_diagnostic/`.

## Main outputs

- `outputs/data/*_unit_metrics.csv`: one row per station/LSOA.
- `outputs/data/*_cluster_metric_summary.csv`: cluster medians and IQRs.
- `outputs/data/*_cluster_signature_z.csv`: robust standardised signatures.
- `outputs/data/*_cluster_metric_significance.csv`: metric ~ cluster
  Kruskal-Wallis + epsilon^2.
- `outputs/figures/*_context_dashboard.png`: interpretation dashboards.
- `outputs/report/RESULTS_SUMMARY.md`: provisional result interpretation.
- `outputs/report/CLUSTER_METRIC_SIGNIFICANCE.md`: is the cluster partition
  internally coherent for its own continuous metrics?
- `outputs/workbook/rq1_context_metrics_results.xlsx`: review workbook.

## Interpretation boundary

These metrics describe observed night-time transport activity. They do not
identify passenger occupations, trip purposes, latent demand, or unmet demand.
For bus, the analytical unit remains an LSOA rather than a stop or route.
