# New bus CLR K=4 × LNWC / IMD test

The first externally interpreted CLR K=4 Bus solution contained 3,365 LSOAs. Linking it to LNWC and IMD showed how the fourth component could be described and also exposed a useful restraint: K=4 did not automatically strengthen every external association relative to K=3. The later corrected Bus refit superseded these numbers, but this branch preserves the analytical step that connected compositional clustering to the dissertation's contextual argument.

This is a thin, side-by-side RQ2 context-analysis branch. It does not copy or
modify the upstream bus clustering data and it does not overwrite the existing
`rq2test analysis` outputs.

## Fixed inputs

- Bus labels: `rq1_bus_clr_transform/outputs/labels/clr_k4_labels.csv`
- K=3 sensitivity labels: `rq1_bus_clr_transform/outputs/labels/clr_k3_labels.csv`
- Bus metrics: `rq1_bus_clr_transform/outputs/features/raw_metrics.csv`
- LNWC: `night_time_work_data/london_night_workers_classification_data.csv`
- IMD: `IMDdata_2025/imd2025_lsoa21_london.csv`
- Boundaries: `map/London_LSOA_2021_Boundaries.geojson`

## Analysis

- K=4 cluster × seven-category LNWC: chi-square, Cramer's V, expected counts,
  row composition, enrichment ratios and Pearson residuals.
- K=4 cluster × IMD score: Kruskal-Wallis, epsilon-squared, cluster summaries
  and BH-adjusted pairwise Dunn tests.
- Minimal K=3 sensitivity comparison on the exact same 3,365-LSOA sample.
- K=3 × K=4 crosswalk to identify how the fourth component refines K=3.

The analyses externally characterise the RQ1 bus typology. They do not identify
passengers, establish causality, or make LNWC/IMD part of the clustering model.

## Run

```powershell
python src\01_run_bus_context_analysis.py
python src\02_verify_reproducibility.py
```

Primary reports are written to `outputs/report/`.
