# Bus hub-first full-week reclustering

The hub-first reconstruction opened a plausible alternative to the original point-based allocation, but adopting it would have required more than a cleaner map. This experiment carried that alternative through a full-week GMM search and an explicit stability audit, allowing its behavioural coherence and small-cluster fragility to be judged before any downstream context analysis was changed.

This is an independent RQ1 bus clustering experiment. It does not overwrite
either the accepted historical clustering folders or the upstream hub-first
preprocessing workspace.

## Purpose

The experiment keeps the original full-week clustering design while changing
only the bus input treatment that has now been audited:

- analysis unit: hub-first LSOA output;
- one model for the full week (not separate weekday/weekend models);
- feature order follows `cluster_clean_version_fullweek`: direction first, then
  `Weekday`, `Saturday`, `Sunday` and the 12 hourly bins;
- each direction is one 36-bin full-week vector and is normalised separately,
  hence 72 features and a full-row sum of two;
- boardings and alightings never share a denominator; no `StandardScaler`;
- exclude the union of the documented group-level exact one-direction-zero
  exception LSOAs;
- retain LSOAs with full-week night activity >= 50;
- apply empirical prior shrinkage with alpha=5 independently to the 36-bin
  full-week boardings and alightings vectors;
- fit one GMM and compare K=2..12 and the four sklearn covariance families by
  BIC, using the historical settings (`n_init=20`, seed 42).

The BIC minimum is a diagnostic candidate, not an automatic final K. The run
also records cluster sizes, internal indices, posterior uncertainty, adjacent-K
nesting, bootstrap ARI, and per-cluster Jaccard recovery. The last measure is
included specifically to detect a high global ARI that conceals an unstable
small cluster.

After the main run, the candidate K=3 interpretation audit can be regenerated
without refitting any model:

```powershell
python -u src\summarise_k3_candidate.py
```

## Inputs (read only)

- `../rq1_bus_hub_first_reorganisation/outputs/preprocessed/bus_lsoa_night_long.parquet`
- `../rq1_bus_hub_first_reorganisation/outputs/data/one_direction_exception_areas.csv`
- `../map/London_LSOA_2021_Boundaries.geojson`
- historical full-week outputs under `../cluster_clean_version_fullweek/outputs/` are
  read only for like-K comparison.

## Run

From this folder:

```powershell
python -u src\run_fullweek_first_pass.py --alpha 5 --min-total 50 --bootstrap 20
```

All generated artifacts are written below `outputs/`. The main narrative output
is `outputs/report/FIRST_PASS_RESULTS.md`.

The K=3 audit is `outputs/report/K3_CANDIDATE_AUDIT.md`.
