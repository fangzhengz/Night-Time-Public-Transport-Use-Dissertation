# Rail ILR compositional sensitivity

The Rail profiles were fitted as direction-wise temporal shares, raising the same compositional-geometry question that had become important for Bus. This audit deliberately changed only the coordinate representation. Its strong disagreement with the historical raw-share partition initially challenged K=5, but the follow-up diagnostic showed that the ILR solution was dominated by temporal zero patterns. The branch is therefore preserved as a caution about transformation choice, not as a replacement Rail typology.

This side-by-side audit tests whether the accepted full-week Underground
typology is sensitive to treating each direction-wise temporal profile as a
composition. It does not modify the accepted raw-share feature matrix, labels,
or the existing K=5/K=6 validation.

## Fixed inputs

- 270 Underground stations from `cluster_clean_version_fullweek`;
- five native day types and the existing 18:00-night windows;
- 172 entry shares and 172 exit shares per station;
- direction totals from `rail_meta.csv`;
- current raw-share K=5 and K=6 labels as external comparators only.

## Single intended change

For entry and exit separately, raw shares are converted back to counts using
the saved direction totals. Zeros are handled with the same empirical-prior
posterior used in the accepted Bus compositional analysis (`alpha=1`). Each
172-part composition is then represented by 171 standard Helmert ILR
coordinates, giving 342 fitted features.

The primary GMM family remains diagonal covariance so the sensitivity changes
the feature geometry while holding the current Rail covariance assumption
fixed. A four-family BIC grid is retained as a secondary diagnostic.

## Run

From this directory:

```powershell
python src/run_rail_ilr_sensitivity.py --bootstrap 200 --seed-runs 20
```

Use a different `--output-root` for any parameter variant. Do not overwrite a
completed canonical run.

## Main outputs

- `outputs/report/VALIDATION_REPORT_ZH.md`
- `outputs/report/VALIDATION_REPORT.md`
- `outputs/report/RUN_METADATA.json`
- `outputs/features/X_rail_fullweek_ilr342.parquet`
- `outputs/diagnostics/ilr_bic_grid.csv`
- `outputs/diagnostics/ilr_kdiag.csv`
- `outputs/diagnostics/raw_reference_comparison.csv`
- `outputs/diagnostics/bootstrap_global_summary.csv`
- `outputs/diagnostics/bootstrap_cluster_summary.csv`
- `outputs/labels/ilr_k2_labels.csv` through `ilr_k12_labels.csv`
- `outputs/figures/`

## Completed result

The canonical alpha=1 / diagonal-GMM run is complete and independently
reproduced in `outputs_repro`.

- Raw K=5 versus ILR K=5: ARI 0.216, NMI 0.351, best-match share 0.511.
- ILR K=5 bootstrap mean ARI: 0.559; weakest cluster mean Jaccard: 0.091.
- The current raw K=5 therefore fails this exact ILR robustness check.
- A post-hoc mechanism audit shows that ILR memberships are dominated by
  temporal zero-pattern structure (K=5 zero-count eta-squared 0.942), so this
  run does not justify adopting ILR K=4 as a replacement typology.

Use `outputs/report/VALIDATION_REPORT_ZH.md` for the bounded conclusion,
`outputs/report/TRANSFORM_DIAGNOSTIC.md` for the zero-pattern audit, and
`outputs/report/REPRODUCIBILITY_CHECK.md` for the exact re-run comparison.

## Interpretation boundary

This is a feature-geometry sensitivity test. It does not add passenger volume,
LNWC, IMD, land use, service supply, or causal evidence. Absolute BIC values
from raw-share and ILR fits are not compared because their fitted dimensions
and likelihood scales differ.
