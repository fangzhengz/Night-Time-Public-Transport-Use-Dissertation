# Bus activity-tiered reclustering

Formalises the fix for the problem Codex's 2026-07-19 pipeline audit found
in the adopted bus K=3 solution (`cluster_clean_version_fullweek`,
MIN_TOTAL=1): the clusters were ~49% explained by activity volume
(log_total_activity), not primarily by night-time rhythm shape, because
low-activity LSOAs have systematically noisier per-direction share vectors
(small-count compositional noise). Neither raising the activity threshold
alone nor switching to diag covariance alone resolved this (see
`../rq1_bus_geography_diagnostic/`) -- but restricting the shape-clustering
to a "reliable core" of higher-activity LSOAs did.

## The finding this formalises

1. Shape-vector variance/spikiness is strongly anti-correlated with
   total_activity (Spearman r=-0.72 / -0.64) -- confirms the noise
   mechanism directly (`01_threshold_selection.py` output
   `shape_noise_vs_activity_diagnostic.csv`).
2. At threshold=450 (n=2,452, 59.8% of the original 4,100 units),
   activity-domination collapses from 49% to 9.8% eta2, while late-night
   timing metrics (post_midnight_share, deep_night_share,
   post_midnight_persistence) all improve, and bootstrap stability at K=3
   is 0.727 (SD 0.025) -- the most stable of K=2/3/4 tested. See
   `outputs/data/comparison_adopted_vs_reliable_core_k3.csv`.

## Design: two tiers, not a blanket threshold

Per Clara's 2026-06-26 guidance (kept, not reversed -- see
`../cluster_clean_version_15min/src/config.py`'s `MIN_TOTAL = 1 # keep
low-activity units (Clara)`), low-activity LSOAs are **not dropped from the
study**. They are reported descriptively (coverage tier + volume context),
just not forced into the same shape-only GMM as higher-activity units.

## Run order

```powershell
py -3 src/01_threshold_selection.py      # evidence-based threshold choice
py -3 src/02_coverage_tiers.py           # classify all 4,994 London LSOAs
py -3 src/03_recluster_reliable_core.py --threshold 450
py -3 src/04_validate_reliable_core.py --k 3
```

Each script also accepts `--threshold` / `--k` explicitly if you want to
try a different cut than the one recommended by `01`'s output.

## Known scope reductions (disclosed, not silent)

Full-covariance GMM on this near-singular, compositional feature space
converges very slowly (multiple background runs at n_init=20 exceeded
10-20 minutes and were killed). To get a complete result within the
available time:

- `01_threshold_selection.py`'s BIC-best-K sanity check uses a coarser K
  grid and n_init=3-5 (informational only -- not the adopted K).
- `03_recluster_reliable_core.py` uses n_init=8 (not the adopted
  pipeline's n_init=20) and only tests K in {2,3,4} with full covariance
  only (spherical/diag/tied are not re-swept here; diag was already shown
  to still hit the K=12 ceiling on a similar clean subsample in
  `../rq1_bus_geography_diagnostic/outputs/report/COVARIANCE_SENSITIVITY_CHECK.md`).

**If this reliable-core design is adopted for the dissertation, re-run
`03_recluster_reliable_core.py` with `RECLUSTER_N_INIT` restored to 20
(matching the adopted pipeline's own settings) for the final reported
numbers, time permitting.** The K=3 choice itself is unlikely to change
(bootstrap ARI margin over K=2/K=4 is large), but exact BIC/silhouette
values should be refreshed at full precision before citing them.

## Relationship to sibling folders

- `../rq1_bus_geography_diagnostic/`: diagnoses *why* the adopted solution
  is fragile (K-choice, classification noise, LSOA aggregation, covariance
  type, threshold sensitivity). Keep -- this is the evidence trail that
  motivated the tiered design here, not redundant with it.
- `../rq1_context_metrics_analysis/`: source of `bus_unit_metrics.csv`,
  reused directly here rather than recomputed.
- `../rq2test analysis/`: bus cluster x LNWC/IMD linkage. **Not yet re-run
  against this reliable-core typology** -- do that only after the K=3
  reliable-core solution is confirmed (full n_init) and the cluster
  identities are named/interpreted, per Codex's original recommendation not
  to re-run downstream tests before the upstream typology stabilises.
