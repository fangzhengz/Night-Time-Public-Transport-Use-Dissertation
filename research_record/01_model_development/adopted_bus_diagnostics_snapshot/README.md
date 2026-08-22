# RQ1 bus clustering on the canonical StopArea allocation

The Bus analysis reached this form only after the project separated two problems that had initially been entangled: how stops should be assembled into meaningful spatial units, and how sparse temporal compositions should be represented for clustering. Once the official StopArea hierarchy replaced direct stop-to-LSOA assignment, this workspace rebuilt the downstream analysis on a more defensible geographical foundation and carried the model through the final threshold, CLR and K-selection decisions.

This is the fuller historical snapshot of the downstream analysis for the canonical bus
StopArea preprocessing output. It replaces the analytical dependency on the
old hub-first folders without modifying archived code.

Migration mapping:

| Previous active analysis | Canonical replacement |
|---|---|
| `rq1_bus_hub_first_reliable_core_assignment` literature `min(boardings, alightings)>=36` branch | `outputs/raw_share/` |
| `rq1_bus_clr_transform` filtered CLR branch | `outputs/clr/` |

The replacement is implemented from the canonical long table rather than by
changing one path in the old scripts, because those scripts also imported
hub-specific feature matrices, metrics, exception lists and helper modules.

The clustering unit remains **LSOA**. The change is upstream: bus-stop demand
is first grouped using official NaPTAN child StopAreas and then allocated to
LSOAs by `FYP/data_processing/bus_stoparea`.

## Night window and retention threshold (updated 2026-08-08)

**Current: 18:00-05:00, min-direction=33.** The window was truncated from
18:00-06:00 (12 hourly bins) by one hour after a controlled sensitivity test
(`FYP/rq1_bus_05cutoff_sensitivity/`, see its `SUMMARY.md`) found the headline
night-persistent cluster >=98% stable under truncation, and timing-metric eta2
*improved* rather than degraded. This also aligns the bus window's upper
boundary with rail's (`numbat_all_area_test`, 18:00-05:00), which previously
differed by one hour for unrelated historical reasons.

The min-direction retention threshold is derived from Marinas-Collado et al.
(2022), "average >=1 passenger per hourly interval": threshold = n_hours x
n_day_types = 11 x 3 = **33** (was 36 = 12 x 3 under the old window; reusing
36 as an absolute count would silently tighten the reliability floor to
~1.09/interval).

**The superseded 18:00-06:00/min-direction=36 pipeline is archived, not
deleted**, at `outputs_archive_1806_min36_2026-08-08/` (this folder) and
`FYP/data_processing/bus_stoparea/outputs_archive_1806_min36_2026-08-08/` --
nothing there was moved or modified when the new pipeline was built. The two
smaller clusters' boundary (moderate/destination-leaning vs. peripheral
low-flow) redraws under the new window -- see
`rq1_bus_05cutoff_sensitivity/SUMMARY.md` for the two-way crossover detail --
so cluster narrative text and specific per-cluster numbers were re-derived,
not just re-run; see `outputs_1805_min33/data/bus_cluster_names.csv`.

## Fixed sample rule

- Input: `FYP/data_processing/bus_stoparea/outputs_1805_min33/preprocessed/bus_lsoa_night_long.parquet`
- Day types: Weekday, Saturday, Sunday
- Window: 18:00–05:00, hourly (11 bins per day)
- Directions: boardings, alightings
- Retain only LSOAs with total activity at least 50 and both direction totals
  at least 33. Because both directions must be at least 33, the total-50 rule
  is retained for methodological continuity but is non-binding.

## Parallel feature variants

1. `raw_share`: boardings and alightings are normalized separately over their
   own 33-bin full-week blocks.
2. `clr`: the same sample and raw counts are used; an empirical-prior
   pseudo-count with `alpha=1` is applied before a separate CLR transform of
   each direction block.

No ParentStopArea grouping or Bayesian temporal smoothing is used.

## Run order

From `D:\SDS2025_workspace\CASA_FYP`:

```powershell
py -3 FYP\rq1_bus_stoparea_clustering\src\01_prepare_features.py
py -3 FYP\rq1_bus_stoparea_clustering\src\02_run_clustering.py --variant raw_share --bootstrap 20
py -3 FYP\rq1_bus_stoparea_clustering\src\02_run_clustering.py --variant clr --bootstrap 20
py -3 FYP\rq1_bus_stoparea_clustering\src\03_compare_variants.py
py -3 FYP\rq1_bus_stoparea_clustering\src\04_supplementary_figures.py
py -3 FYP\rq1_bus_stoparea_clustering\src\05_strict_min72_raw_share.py --min-direction 72
py -3 FYP\rq1_bus_stoparea_clustering\src\05_strict_min72_raw_share.py --min-direction 180
py -3 FYP\rq1_bus_stoparea_clustering\src\06_cluster_names.py
py -3 FYP\rq1_bus_stoparea_clustering\src\07_posterior_membership.py
py -3 FYP\rq1_bus_stoparea_clustering\src\08_seed_agreement.py
```

`07_posterior_membership.py` and `08_seed_agreement.py` (added 2026-08-17) both
refit the exact reported CLR solution rather than reading a saved model (none
is pickled) -- `07` verifies its refit reproduces the saved K=4 labels
(ARI==1.0) before extracting `predict_proba`; `08` independently refits every
K in `BOOTSTRAP_KS` at the same `FINAL_SEEDS`/`N_INIT_FINAL`/covariance budget
as the official refit, keeps each seed's own labels (discarded by
`02_run_clustering.py`), and reports the mean *pairwise* ARI among the 5
seeds as `seed_ari_mean` -- merged into `outputs_1805_min33/clr/diagnostics/kdiag.csv`
so it appears in `build_ch4_final_figures.py`'s K-selection panel, which was
previously blank for this metric (rail's equivalent panel is
`numbat_all_area_test/src/08_k_selection_panel.py`'s `seed_ari_mean`, same
statistic and method).

Each clustering run evaluates `K=2..12` across spherical, diagonal, tied and
full covariance GMMs with `n_init=20`, seed 42. Candidate outputs for K=3 and
K=4 include profiles, maps and within-cluster homogeneity diagnostics.

## Output structure

All current outputs live under `outputs_1805_min33/` (not `outputs/`, which is
the archived 18:00-06:00/min36 pipeline -- see above).

- `outputs_1805_min33/features/`: common sample, raw counts, raw-share and CLR matrices
- `outputs_1805_min33/raw_share/`: raw-share clustering outputs
- `outputs_1805_min33/clr/`: CLR clustering outputs
- `outputs_1805_min33/comparison/`: raw-share/CLR comparison on the common StopArea sample
- `outputs_1805_min33/figures/`: cross-variant supplementary figures in PNG and PDF
- `outputs_1805_min33/report/`: feature preparation and cross-variant reports
- `outputs_1805_min33/strict_min*_raw_share/`: independent raw-share strict low-activity
  sensitivities, retaining only LSOAs with both directions above the stated
  threshold; these write PNG figures only and do not alter the baseline outputs.
  **Not yet re-run under the new window as of 2026-08-08** -- their thresholds
  (72, 180) were absolute counts derived from the old min36 baseline (2x, 5x);
  whether to rescale them to 66/165 to preserve the same multiplier, or keep
  72/180 as fixed absolute floors, is an open call flagged for the user.

For a threshold `T`, its standard figures are
`strict_minT_raw_share_full_map_k{3,4}`,
`strict_minT_raw_share_full_profiles_k{3,4}`,
`strict_minT_raw_share_kdiag_full`,
`strict_minT_raw_share_model_selection_bic_grid`, and
`strict_minT_raw_share_vs_min36_candidate_comparison`.

To inspect every fitted K without rerunning the models, use:

```powershell
py -3 FYP\rq1_bus_stoparea_clustering\src\05_strict_min72_raw_share.py --min-direction T --figures-only --all-k-figures
```

This writes individual maps and temporal profiles for `K=2..12`, plus
`strict_minT_raw_share_all_k_map_atlas`.  The atlas uses a separate categorical
colour assignment in each panel, so its colours must not be interpreted as
matched clusters across different K values.

The five original-style core figures are available for each variant as both
PNG and PDF. Raw-share uses
`literature_mean1ph_full_map_k{3,4}`,
`literature_mean1ph_full_profiles_k{3,4}` and
`literature_mean1ph_kdiag_full`; CLR uses `clr_map_k{3,4}`,
`clr_profiles_k{3,4}` and `clr_kdiag_full`.

The old hub-first outputs are not read by this pipeline and are not used as a
scientific comparator. They remain historical material in the archive only.
