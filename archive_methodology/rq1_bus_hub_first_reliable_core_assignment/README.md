> **Superseded for active analysis (2026-07-22).** This directory documents the
> historical self-built hub-first experiment. Its `min(boardings,
> alightings)>=36` branch has been replaced by the canonical StopArea raw-share
> pipeline in `FYP/rq1_bus_stoparea_clustering`. Do not use the results below as
> the current RQ1 bus classification.

# Hub-first reliable-core clustering and posterior assignment

This is a thin, side-by-side experiment. It does not overwrite the existing
hub-first reclustering, alpha sensitivity, alpha-grid, or older activity-tiered
workspaces.

## Current stage

Stage 1 screens a weaker-direction activity-evidence threshold on the fixed
hub-first `alpha=0` 72-feature sample. For each threshold it fits the same
full-covariance Gaussian mixture at `K=2..5` and asks whether cluster membership
is more strongly associated with late-night timing metrics than with total
activity.

The screening variable is:

```text
min_direction_activity = min(total_boardings, total_alightings)
```

This is preferable to a total-activity cutoff because boarding and alighting
are normalized separately and each contributes 36 equally weighted features.

Stage 1 does **not** select the final K and does **not** yet perform posterior
assignment. Those steps only follow if a threshold passes the pre-specified
gate while retaining acceptable coverage.

## Fixed inputs

- Hub-first sample: 3,593 LSOAs after the existing `min_total=50` and exact
  one-direction-zero exclusions.
- Features: saved hub-first `alpha=0` direction-normalized 72-vector.
- Covariance: `full`.
- Random seed: 42.
- Threshold-screen K values: 2, 3, 4, 5.

Inputs are read in place from the upstream workspaces. They are not copied.
Every run writes an input manifest with SHA-256 hashes.

## First-pass command

```powershell
py -3 src\01_threshold_screen.py `
  --thresholds 0 50 70 90 100 110 125 150 `
  --k-scan-min 2 --k-scan-max 10 `
  --scan-n-init 5 --deepdive-n-init 20 `
  --seed 42 `
  --tag first_pass
```

## Decision gate (v2)

The v1 gate (below) required K=2 through K=5 to simultaneously clear the
activity-versus-timing test at the same threshold. That was dropped: the
historical K=3 result was produced by a pipeline this project has since shown
to be activity-noise-contaminated (hub splitting, no reliable-core exclusion),
so K=3 repeatedly "winning" in earlier work is not independent evidence that
K=3 is still correct once the contamination is actually removed -- assuming
K=3 (or requiring an arbitrary fixed K list to agree) would presuppose the
answer. Forcing simultaneous agreement across K=2..5 also silently assumed
every one of those K values *should* be a good fit if the threshold were
clean, which is a different and unjustified claim from "the threshold is
clean."

v2 instead lets BIC pick each threshold's own preferred K from an exploratory
scan (K=2..10, full covariance, low n_init), confirms the winning K at full
n_init, and gates only on that threshold's own natural K. K=3 is still
refit and shown as a labelled reference point for comparability, never as a
requirement.

A threshold is a strict candidate only if, at its own BIC-best K:

1. `activity_eta2 < timing_mean_eta2`;
2. the same condition holds at its own BIC-best K for an adjacent screened
   threshold (the two thresholds may prefer different K);
3. core coverage is at least 75%; and
4. the confirmatory fit converges.

Coverage from 70% to below 75% is reported as fallback-only. Below 70% is a
stress test, not an eligible main result. BIC/AIC are only valid for
comparing K values within the same threshold.

## Executed runs (v1, superseded)

- `benchmark`: threshold 100, K=3, n_init=1; input and runtime check.
- `first_pass`: thresholds 0, 50, 70, 90, 100, 110, 125, 150;
  fixed K=2..5 required simultaneously; n_init=5.
- `stress`: thresholds 175, 200, 250, 300; fixed K=2..5; n_init=5.
- `reproducibility`: threshold 100, K=3, n_init=5; exact numeric
  reproduction of the corresponding first-pass row, excluding runtime.

The v1 strict gate found no eligible threshold -- see
`outputs/report/SCREENING_SYNTHESIS.md`. v2 output (per-threshold BIC-chosen
K) supersedes this; see `outputs/report/THRESHOLD_SCREEN_FIRST_PASS.md` and
`THRESHOLD_SCREEN_STRESS.md` for the current tag's results after a v2 rerun.

## Later stages (not reflected above): bottom-20% vs literature threshold=36

Two side-by-side low-flow rules were carried through to full K=3/K=4
inspection: `bottom20` (Pareto-style, excludes the bottom 20% of LSOAs by raw
total activity -- kept only as a sensitivity comparator, not literature-
derived) and `literature_mean1ph` (`min(boardings,alightings)>=36`, the
Mariñas-Collado et al. 2022 mean->=1-passenger-per-observed-hour analogue --
see `outputs/report/LITERATURE_LOW_FLOW_THRESHOLD_DECISION.md`). This is the
same threshold and the same 3,365-LSOA sample later adopted as the primary
rule in `../巴士聚类错误修改`.

```powershell
python src\02_bottom20_excluded_bic.py
python src\02b_bottom20_full_covariance_kdiag.py
python src\03_bottom20_k3_k4_profiles_and_maps.py
python src\04_literature_mean1ph_k3_k4_maps.py
python src\05_bottom20_cluster_homogeneity.py
python src\06_literature_mean1ph_k_diagnostics_figure.py
python src\07_literature_mean1ph_cluster_homogeneity.py
python src\08_literature_mean1ph_full_kdiag_figure.py
python src\09_bottom20_full_kdiag_figure.py
```

`04` only ever fit K=3/K=4 directly and produced profiles/maps -- it never
plotted the K=2..12 scan `01_threshold_screen.py` already saved for this
threshold, and never had a cluster-homogeneity check, so `literature_mean1ph`
had strictly fewer diagnostic figures than its `bottom20` comparator despite
being the more important of the two. `06` and `07` close that gap, read-only
against already-saved scan/label/metrics data (no refitting):

- `06_literature_mean1ph_k_diagnostics_figure.py` -- `outputs/figures/literature_mean1ph_k_diagnostics.png`:
  BIC / activity-vs-timing eta2 / smallest-cluster-% vs K=2..12, from
  `outputs/data/threshold_k_scan_literature_mean1ph.csv` and
  `threshold_k_deepdive_literature_mean1ph.csv`. No bootstrap panel here --
  `01_threshold_screen.py` never ran a bootstrap for this threshold, unlike
  `bottom20_excluded_k_diagnostics.png`'s second panel.
- `07_literature_mean1ph_cluster_homogeneity.py` -- same diagnostic as
  `05_bottom20_cluster_homogeneity.py` and
  `巴士聚类错误修改/src/03_cluster_homogeneity.py`, on the
  `literature_mean1ph_full_k{3,4}_labels.csv` labels:
  `outputs/diagnostics/literature_mean1ph_cluster_homogeneity{,_raw_values}.csv`,
  `outputs/figures/literature_mean1ph_homogeneity_boxplots_k{3,4}.png`,
  `outputs/report/CLUSTER_HOMOGENEITY_LITERATURE_MEAN1PH.md`.
- `08_literature_mean1ph_full_kdiag_figure.py` -- the full 5-panel house-style
  K-diagnostics panel (silhouette, Calinski-Harabasz, Davies-Bouldin, BIC,
  bootstrap ARI), matching `巴士聚类错误修改/outputs/figures/bus_fullweek_kdiag_full.png`
  exactly. Verifies byte-identity against `巴士聚类错误修改`'s feature matrix first
  (same 3,365-LSOA hub-first sample, same GMM settings), then reuses its
  `bus_fullweek_kdiag.csv` rather than refitting a numerically identical
  model a second time: `outputs/figures/literature_mean1ph_kdiag_full.png`,
  `outputs/diagnostics/literature_mean1ph_kdiag_full.csv`.
- `09_bottom20_full_kdiag_figure.py` -- the same 5-panel house-style figure
  for the `bottom20` comparator. This sample is NOT the same as the official
  rewrite's (different exclusion rule, different retained LSOAs), so it
  can't be borrowed; also note `02_bottom20_excluded_bic.py`'s own kdiag used
  whichever covariance family had the global BIC minimum, which turned out to
  be `tied` at a degenerate K=12 (min_cluster_n=1) -- this script instead
  builds on `02b_bottom20_full_covariance_kdiag.py`'s full-covariance-only
  line, refitting K=2..12 once more only to add Calinski-Harabasz (the one
  metric neither `02` nor `02b` computed):
  `outputs/figures/bottom20_excluded_kdiag_full.png`,
  `outputs/diagnostics/bottom20_excluded_kdiag_full.csv`.
