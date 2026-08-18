# Bus hub-first isolation test

Single-variable test: does changing ONLY the stop-to-LSOA aggregation method
(hub-first vs the original point-in-polygon assignment) change the bus
clustering result, holding every other setting -- filtering, shrinkage,
feature construction, GMM search -- exactly as in
`../cluster_clean_version_fullweek`?

This did not previously exist as an isolated artifact. The closest existing
experiment, `../rq1_bus_hub_first_reclustering`, changes hub-first aggregation
*together with* three other things at once (one-direction-exception exclusion,
`MIN_TOTAL` raised from 1 to 50, and alpha=5 empirical-prior shrinkage), so it
cannot say which of the four changes is responsible for any given difference
from the original result.

## What is held fixed vs the true original (`cluster_clean_version_fullweek`)

Copied verbatim from `cluster_clean_version_fullweek/src/config.py` and
`03_build_features.py`/`04_cluster.py`'s bus branch:

- `MIN_TOTAL = 1` (Clara's "drop only empty units" rule -- not the official
  rewrite's 50)
- No one-direction-exception exclusion
- No weaker-direction floor
- No empirical-prior shrinkage (alpha=0, i.e. plain `count / direction_total`
  shares, `fillna(0.0)` for any zero-total direction rather than excluding it)
- Same 72-feature construction: two independently-normalised 36-bin full-week
  direction vectors, bus native day-types (Weekday/Saturday/Sunday), hourly,
  18:00-06:00
- Same GMM search: `K=2..12`, 4 covariance families, `n_init=20`,
  `reg_covar=1e-6`, `max_iter=300`, `seed=42`
- Same diagnostics: BIC grid, subsampled silhouette
  (`sample_size=min(2000,n)`, `random_state=42`), Calinski-Harabasz,
  Davies-Bouldin, 20-resample bootstrap ARI (`n_init=3` for the resample
  refits), candidate `K=3..8` labels

## What changed

Only `BUS_LONG`: from `cluster_clean_version_grouped`'s point-in-polygon
LSOA long table to `rq1_bus_hub_first_reorganisation`'s hub-first long table
(`bus_lsoa_night_long.parquet`, schema `day_type, direction, lsoa, hour_bin,
count` -- unchanged). Any difference between this run's results and
`cluster_clean_version_fullweek`'s bus result is attributable to hub-first
aggregation alone.

## Run

```powershell
python src\01_build_features.py
python src\02_cluster.py
```

## Outputs

- `outputs/features/X_bus.parquet`, `bus_meta.csv`
- `outputs/diagnostics/bus_bic_grid.csv`, `bus_kdiag.csv`, `bus_bic_best.txt`
- `outputs/labels/bus_k{3..8}_labels.csv`
- `outputs/report/HUB_FIRST_ISOLATED_COMPARISON.md` -- side-by-side against
  `cluster_clean_version_fullweek`'s original bus result (built by
  `src/03_compare_to_original.py`, read-only against both runs' outputs)
