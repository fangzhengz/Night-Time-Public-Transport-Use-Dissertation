# Rail K Selection Validation

Before the study expanded to the final 403-station all-modes Rail scope, the Underground-only model faced a close K=5 versus K=6 decision. This validation records how that earlier choice was defended using paired bootstrap recurrence, seed stability and transition structure rather than BIC alone. Because the sample and feature definition later changed, it remains historical evidence and cannot substitute for the final Rail model-selection table.

This workspace validates the choice between `K=5` and `K=6` for the current
full-week Underground clustering. It is deliberately separate from the
runnable clustering pipeline and does not modify its features, labels, or
diagnostics.

## Scope

The validation uses only evidence internal to the clustering problem:

1. deterministic refit against the saved labels;
2. K=5/K=6 transition and overlap structure;
3. global and cluster-level silhouette diagnostics;
4. paired bootstrap resampling stability;
5. full-data random-seed stability.

LNWC, IMD, station catchments, land use, and other downstream interpretation
variables are not loaded and cannot affect the K assessment. Station names are
joined only to make membership changes auditable.

## Inputs

The defaults point to the accepted full-week workspace:

- `../cluster_clean_version_fullweek/outputs/features/X_rail.parquet`
- `../cluster_clean_version_fullweek/outputs/labels/rail_k5_labels.csv`
- `../cluster_clean_version_fullweek/outputs/labels/rail_k6_labels.csv`
- `../cluster_clean_version_fullweek/outputs/diagnostics/rail_kdiag.csv`
- `../cluster_clean_version_grouped/outputs/preprocessed/rail_coords.csv`

All input paths and SHA-256 hashes are recorded in
`outputs/report/RUN_METADATA.json`.

## Run

From this directory:

```powershell
python src/run_rail_k_validation.py
```

or:

```powershell
.\run_validation.ps1
```

Default settings reproduce the current diagonal-covariance GMM configuration:

- random state: 42
- reference/full-data `n_init`: 20
- bootstrap `n_init`: 3
- covariance: diagonal
- bootstrap replicates: 200
- random-seed refits: 20
- `reg_covar`: 1e-6
- `max_iter`: 300

Use `python src/run_rail_k_validation.py --help` for overrides. A parameter
variant should use a different `--output-root` so the canonical run is not
overwritten.

## Main outputs

- `outputs/report/VALIDATION_REPORT.md`: evidence and bounded verdict
- `outputs/report/VALIDATION_REPORT_ZH.md`: Chinese evidence report
- `outputs/report/REPRODUCIBILITY_CHECK.md`: saved-label and diagnostic refit
- `outputs/report/RUN_METADATA.json`: parameters, versions, hashes, duration
- `outputs/data/bootstrap_cluster_stability_summary.csv`
- `outputs/data/bootstrap_global_stability_summary.csv`
- `outputs/data/bootstrap_paired_ari_comparison.csv`
- `outputs/data/bootstrap_paired_ari_summary.csv`
- `outputs/data/seed_cluster_stability_summary.csv`
- `outputs/data/cluster_silhouette_summary.csv`
- `outputs/data/k5_k6_contingency.csv`
- `outputs/data/station_transition_detail.csv`
- `outputs/figures/`: transition, silhouette, and stability figures

## Interpretation boundary

Bootstrap stability measures whether memberships recur after resampling. It
does not estimate the probability that a particular K is the true number of
clusters. K is reported as a multi-criterion, parsimonious analytical choice,
not a discovered natural constant.
