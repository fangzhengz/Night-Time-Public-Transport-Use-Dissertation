# 巴士15分钟与1小时稳定性验证

Finer temporal bins can reveal short-lived peaks, but they also multiply sparse cells and may make a convincing profile less reproducible. This experiment rebuilt both resolutions from the same validated source table so that temporal detail—not sample composition or preprocessing—was the only intended difference. The comparison helped justify treating stability and interpretability as separate criteria rather than assuming that more detailed data must produce the better typology.

This folder is an independent, non-destructive comparison of the Bus RQ1
typology at 15-minute and 1-hour temporal resolution.

## Fair-comparison design

Both feature matrices are rebuilt from the same validated 15-minute LSOA long
table. The 1-hour table is created by summing four adjacent 15-minute bins.
Everything else is held constant:

- same 4,100 non-empty LSOAs;
- same day types (`Weekday`, `Saturday`, `Sunday`);
- same 18:00–06:00 window;
- same whole-week, per-direction normalisation;
- same K values (`3`, `4`, `5`);
- same covariance families (`diag`, `tied`);
- same seeds and bootstrap samples;
- same GMM regularisation and convergence settings.

Because silhouette values in 288- and 72-dimensional spaces are not directly
comparable, every label solution is also evaluated on the same 1-hour feature
space (`silhouette_common_1h`).

## Validation dimensions

1. Internal separation on native and common feature spaces.
2. Across-seed label stability.
3. Bootstrap label stability.
4. Cross-resolution ARI/NMI and Hungarian-matched agreement.
5. Cluster-size balance and singleton detection.
6. Post-hoc separation on volume, late-night timing, direction and weekend use.
7. Association with the seven supplied LNWC categories.

## Run

```powershell
py -3 src/run_validation.py
node src/build_workbook.mjs
```

## Outputs

- `outputs/data/model_comparison.csv`
- `outputs/data/cross_resolution_agreement.csv`
- `outputs/data/interpretability_metrics.csv`
- `outputs/data/cluster_signatures.csv`
- `outputs/figures/stability_dashboard.png`
- `outputs/figures/interpretability_dashboard.png`
- `outputs/figures/k4_diag_profiles.png`
- `outputs/report/RESULTS_SUMMARY.md`
- `outputs/workbook/bus_resolution_stability_validation.xlsx`

## Interpretation boundary

This experiment evaluates robustness and interpretability of the two
resolutions. It does not establish that a visually richer solution is the true
latent typology, and BIC values are not compared across matrices of different
dimensionality.
