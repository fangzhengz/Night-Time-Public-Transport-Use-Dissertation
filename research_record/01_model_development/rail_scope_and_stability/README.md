# NUMBAT All-Area Test — Rail Scope Extension Check (now the primary RQ1 rail result)

The final Rail population grew out of a challenge to the original Underground-only scope: if NUMBAT contained a wider family of urban Rail services, could the narrower boundary still be justified? What began as a robustness check therefore became a scope decision. The successive refits in this folder show how geographical eligibility, station co-location, common night windows and K stability were reconciled before the 403-station K=5 solution was adopted.

**Status (2026-07-30): the K=5 clustering built here is now the primary RQ1
rail result**, replacing `cluster_clean_version_fullweek`'s 270-station
Underground-only K=5. It started as a scope-robustness check answering a
question raised in the 2026-07-17 supervisor meeting
(`FYP/meeting/_meeting4_extract.txt`). Howard asked:

> "why looking at just underground rather than all the rail stations
> within NUMBAT data?"

and Clara suggested treating it as a quick robustness check rather than a
full re-run:

> "maybe try what happens if you add all the rail as well... does that
> justify using just underground?"

After the 2026-07-24 NaPTAN scope correction, the missing Paddington NR/TfL
co-location was fixed and the full pipeline rerun on 2026-08-07. The current
result contains **403 stations** and one Paddington observation. The K-selection
panel and K=5-vs-K=7 stability battery were regenerated (see "NaPTAN-matched station
scope" below), K=5 here was adopted as primary -- for scope-defensibility
reasons (it directly answers Howard's question) rather than because it
out-performs canonical on the downstream LNWC/IMD story, which it does not
(see `rq2_new_clusters_analysis/README.md`'s headline result). Canonical
(`FYP/cluster_clean_version_fullweek/`) is kept, unmodified, as the retired
historical reference; this folder still does not modify its inputs, code,
or outputs. Everything here reads from the raw NUMBAT workbooks and writes
only beneath this folder's own `outputs/`.

## Background

The canonical rail typology (rail K=5, diagonal-covariance GMM) is built
from `FYP/analysis code/03_preprocess_numbat_lu_multiday.py`, which keeps
only stations where `has_lu == True` — 270 of 471 NLCs in the raw NUMBAT
workbooks. The other 201 stations (DLR-only, London Overground-only,
Elizabeth line-only, Tram-only, and a couple of non-LU mixed-mode stations)
are dropped before feature building ever runs.

This test builds a second, parallel pipeline that keeps every NUMBAT rail
NLC (see the tram limitation below), using the exact same 344-dimensional
full-week feature definition and GMM methodology as the canonical pipeline,
then compares the two results.

**A same-physical-site complication was found and fixed partway through**:
NUMBAT gives some locations (Heathrow's terminals, Canary Wharf, Euston,
Liverpool Street, etc.) separate NLCs per mode even though they are one
physical place, because those modes have historically separate fare
gatelines. `01b_merge_colocated_stations.py` consolidates these 14 sites
into single stations; see "Co-located station merge" below for why this
mattered.

## Scope

**2026-07-24: preprocessing moved out.** Steps 1-2 below (raw extraction,
co-located merge) plus NaPTAN coordinate matching now live in
`FYP/data_processing/rail_allmodes/` as `01`-`01d` (mirroring
`data_processing/bus_stoparea/`'s separation from
`rq1_bus_stoparea_clustering/`), with their own README and
station-count-chain report. This folder now starts at feature-building
(`02`) and reads that folder's final output directly.

1. *(moved to `data_processing/rail_allmodes/src/01_preprocess_rail_allmodes.py`)*
   — same NUMBAT parsing as the canonical LU-only script, minus the
   `has_lu` filter. Outputs a 471-station long table + a `mode_lookup`
   describing which NUMBAT mode(s) serve each station.
2. *(moved to `data_processing/rail_allmodes/src/01b_merge_colocated_stations.py`)*
   — merges the 14 co-located, cross-mode NLC groups (29 NLCs → 14 units)
   into single physical stations, summing counts per day/direction/bin →
   456 stations. Followed there by `01c_match_naptan_coords.py`
   (NaPTAN/Underground_Stations.csv coordinate match, 440/456 matched) and
   `01d_filter_naptan_matched.py` (drops the 16 unmatched, genuinely
   outside Greater London — see that folder's
   `outputs/report/RAIL_ALLMODES_PREPROCESSING.md` for the full chain).
3. `src/02_build_features_allmodes.py` — reuses the canonical
   `assemble()`/`pivot_day()` feature-building logic unchanged, now reading
   `data_processing/rail_allmodes/`'s final 440-station NaPTAN-matched
   table. 37 stations are dropped for zero night-window activity (see tram
   note below), leaving **403 stations**.
4. `src/03_cluster_allmodes.py` — reuses the canonical GMM search
   methodology (`diag` covariance, `n_init=20`, `random_state=42`,
   `reg_covar=1e-6`, K=2..12), restricted to `{diag, full}` covariance
   families for the BIC cross-check (diag is what the canonical rail
   result actually uses; full is a cross-check, not a replacement).
5. `src/03b_full_covariance_grid_check.py` — the complete
   `{spherical, diag, tied, full}` covariance grid on the same feature
   matrix, confirming diag dominates by a large margin (current best BIC:
   diag -1,899,404 at K=5; spherical -1,841,307 at K=11; tied -1,458,298
   at K=2; full -886,004 at K=2 —
   the same catastrophic overfitting pattern full shows in every other
   check on this kind of high-dimensional share data). Must be rerun
   whenever `X_rail_allmodes.parquet` changes upstream, since it reads
   that file directly rather than taking a station count as a parameter.
   See `outputs/data/rail_allmodes_bic_grid_full4family.csv` and
   `outputs/figures/rail_allmodes_bic_grid_full4family.png`.
6. `src/04_compare_lu_vs_allmodes.py` — the core comparison: does the
   BIC-preferred K change, how stable are the original 270 canonical
   stations' cluster memberships (ARI, Hungarian matching), and where do
   the added non-LU stations land by mode. The report text adapts
   automatically depending on whether the BIC-optimal K matches canonical's
   or not (see Key Finding below — it currently does match).
7. `src/05_build_allmodes_coords_and_map.py` — the canonical-vs-all-modes
   side-by-side cluster map. Coordinate matching itself moved to
   `data_processing/rail_allmodes/src/01c_match_naptan_coords.py`
   (2026-07-24); this script just reads that folder's
   `rail_allmodes_coords.csv` directly.
8. `src/06_profiles_and_maps_allmodes.py` — reuses
   `cluster_clean_version_fullweek/src/05_figures.py`'s exact plotting
   logic (BIC grid, K-diagnostics panel, per-cluster temporal
   usage-profile charts, station map on an LSOA basemap) for the all-modes
   result at K=5/6/7, with added non-LU stations marked as triangles on
   the map.
9. `src/07_stability_allmodes.py` — a parameterised adaptation of
   `FYP/rail_k_selection_validation/src/run_rail_k_validation.py`'s full
   bootstrap/seed-stability battery (200 paired bootstrap replicates, 20
   random-seed refits, cluster silhouette, K-transition structure),
   applied to K=5 vs K=6 -- this data's own closest BIC pair (K=5 is now
   this dataset's own outright BIC winner post-NaPTAN-filter, not just the
   canonical-comparability choice; see "NaPTAN-matched station scope"
   below -- the K=6-BIC-optimum claim originally written here was true of
   the pre-filter 420-station data, not the current 403-station one).
   **This is a secondary validation check, not the official K-selection
   source** -- its `seed_ARI_mean`/`bootstrap_ARI_mean_200`/
   `weakest_cluster_jaccard` measure agreement WITH the saved/adopted
   labels (20 refits / 200 bootstraps against the fixed adopted partition),
   whereas step 10 below measures agreement AMONG same-budget seeds/
   resamples with no privileged reference. Do not cite this step's numbers
   as if they were step 10's; see "Interpretation boundary" below.
10. `src/08_k_selection_panel.py` — the **official** K-selection evidence
    panel (`rail_allmodes_k_selection_panel.csv` / `.png`), K=2..12 at an
    equalised 5-seed x n_init=200 budget. Any random-seed ARI, bootstrap
    ARI or weakest-cluster Jaccard number cited in the dissertation must
    come from this CSV, at the adopted K row.

Steps 7-10 go beyond the original "quick check" scope at the user's later
request, to give the same class of figures/evidence that exists for the
canonical Underground-only result.

## Co-located station merge

NUMBAT records 14 physical sites under separate NLCs per mode because
those modes have historically separate fare gatelines even at the same
location: each of Heathrow's 3 terminals (Underground side + Elizabeth
line/Heathrow Express side), Canary Wharf (LU + DLR + Elizabeth line, 3
NLCs), Custom House, Euston, Liverpool Street, Bethnal Green, Shadwell,
Shepherd's Bush, West Croydon, West Hampstead, Wimbledon, and Paddington
(NR NLC 3087 + TfL NLC 670). Left
unmerged, these showed up as two (or three) overlapping points on the
station map and as separate rows feeding the clustering — most visibly at
Heathrow, where all three terminals doubled up.

**This complication was not cosmetic.** Before merging, the unmerged
432-station all-modes run's own BIC-optimal K was **7** (not matching
canonical's K=6). After merging via `01b_merge_colocated_stations.py`, the
BIC-optimal K on the resulting 420-station data is **6** — the same as
canonical. The pre-merge K=7 finding is archived in
`outputs/pre_merge_archive/` (see its own README) as a record that the
earlier scope-sensitivity finding was partly an artefact of station
accounting granularity, not a genuine consequence of widening station
scope.

## An important data limitation: trams

All 37 stations dropped for zero activity after merging are Tram-only (or
Tram-paired-with-nothing-else-live) stops, and no other mode is affected.
London Trams have no gateline, so NUMBAT's `Station_Entries`/
`Station_Exits` sheets structurally cannot record tram patronage (tram
counts only exist in `Station_Boarders`, a differently collected series).
"All NUMBAT rail stations" in this test therefore means LU + DLR +
Overground + Elizabeth line, not literally every rail-family mode — trams
cannot be included through this feature.

## NaPTAN-matched station scope (updated 2026-08-07)

The all-modes pipeline's input is filtered to 440 stations with a
NaPTAN Greater-London (area 490) coordinate match, before any feature
building or clustering; the night-window activity filter then removes 37
tram-only units, leaving the current **403-station** clustering population.
Sixteen of the 456 post-merge all-modes stations have no
NaPTAN Greater-London match at all (Reading, Slough, Maidenhead, Twyford,
Watford Junction, Bushey, Carpenders Park, Cheshunt, Theobalds Grove, etc.)
and are confirmed genuinely outside Greater London (checked the local
NaPTAN extract directly -- a structural/geographic fact, not a
name-matching bug). Checking their cluster membership in the original
420-station fit found they were not evenly spread: 12 of them (17.6%)
concentrated in one K=5 cluster (n=68), alongside several large National
Rail interchanges (Watford Junction, Maidenhead, Slough, Shenfield) with
activity comparable to the two largest clusters -- real signal, not noise.

**Only the no-NaPTAN-match stations are excluded.** A same-day earlier
attempt also excluded a further 16 stations that DO have a NaPTAN match but
whose point falls just outside the strict Greater London boundary
(Amersham, Chesham, Epping, Watford, Chorleywood, Rickmansworth, Moor
Park, Croxley, Buckhurst Hill, Chigwell, Debden, Grange Hill, Loughton,
Roding Valley, Theydon Bois, Chalfont & Latimer); that was reverted because
it was inconsistent with how canonical itself is scoped -- canonical's own
270-station Underground clustering already includes those same border
stations and only excludes them *downstream* from LNWC/IMD, never from the
clustering itself (see `outputs/archive_strict_extent_v1/README.md`).

The filter itself now lives in `data_processing/rail_allmodes/` (moved
there the same day, see that folder's own README and
`outputs/report/RAIL_ALLMODES_PREPROCESSING.md` for the full audit trail
and station-count chain) -- `02` through `07` in *this* folder run
**completely unmodified** on that folder's filtered 440-station final
output (`02`'s own zero-activity filter then drops the 37 tram-only
stations, arriving at 403), so every output here keeps its original
filename (`rail_allmodes_bic_grid.csv`, `rail_allmodes_k5_labels.csv`,
`VALIDATION_REPORT.md`, etc.) and full rigor (including the full
4-covariance-family check and the 200-bootstrap/20-seed stability battery)
is preserved exactly as before, just applied to the corrected station
population.

**The pre-filter 420-station results are archived, not discarded**, at
`outputs/archive_420station_allmodes/` (own README explains the change).
An even earlier, stricter (388-station) filter attempt is separately
archived at `outputs/archive_strict_extent_v1/`.

**Result**: unlike the (superseded) stricter 388-station exclusion, this
smaller, more targeted NaPTAN-matched population **does** shift the BIC-preferred K,
from 6 (diag) to 5 (diag) -- confirmed by both the standard `diag`+`full`
grid in `03` and the full `{spherical, diag, tied, full}` grid in `03b`.
K=5 is now both this dataset's own BIC winner and the number needed for
comparability with canonical's adopted K=5. The current equal-budget
K-selection panel (five seeds, n_init=200 per K) also selects K=5: BIC
-1,900,159.5 versus -1,900,063.5 at K=6 and -1,898,546.3 at K=7. Mean
pairwise seed ARI is 0.964 / 0.486 / 0.469 and night-group survival Jaccard
is 0.988 / 0.789 / 0.469 for K=5/6/7. `rq2_new_clusters_analysis` points at
these current standard-named files.

## Run

First, from `data_processing/rail_allmodes/` (see that folder's own
README): `01` → `01b` → `01c` → `01d`, producing the final 440-station
NaPTAN-matched long table.

Then, from this directory, in order:

```powershell
python src/02_build_features_allmodes.py
python src/03_cluster_allmodes.py
python src/03b_full_covariance_grid_check.py
python src/04_compare_lu_vs_allmodes.py
python src/05_build_allmodes_coords_and_map.py
python src/06_profiles_and_maps_allmodes.py
python src/07_stability_allmodes.py
```

## Main outputs

- `outputs/report/VALIDATION_REPORT_ZH.md` / `VALIDATION_REPORT.md` —
  evidence and a bounded verdict, in the same style as
  `FYP/rail_k_selection_validation/`. Now reports ARI=0.630 (canonical K=5
  vs this 403-station refit's K=5, restricted to the 270 canonical
  stations) and BIC-best K=5 for both canonical and this refit (previously
  K=6 for the pre-filter 420-station version).
- `outputs/data/k_selection_comparison_canonical_vs_allmodes.csv` —
  BIC/silhouette, K=2..12, canonical vs this refit side by side.
- `outputs/data/rail_allmodes_bic_grid_full4family.csv` +
  `outputs/figures/rail_allmodes_bic_grid_full4family.png` — the full
  `{spherical, diag, tied, full}` covariance grid on the 403-station data:
  diag best BIC -1,899,404 at K=5, vs spherical -1,841,307 (K=11), tied
  -1,458,298 (K=2), full -886,004 (K=2) -- diag wins decisively.
- `outputs/data/k5_canonical_vs_allmodes_mapping.csv` /
  `..._contingency.csv` — Hungarian-matched cluster correspondence and the
  full transition table, restricted to the 270 canonical stations.
- `outputs/data/mode_group_by_allmodes_k5_cluster_{counts,share}.csv` —
  where the added non-LU stations land, by mode.
- `outputs/data/colocated_station_merge_crosswalk.csv` — the 14-group,
  29-NLC merge mapping used by `01b`.
- `outputs/data/rail_allmodes_coords.csv` — coordinates for the 403 kept
  stations (all NaPTAN-matched by construction: 403/403, 0 unmatched).
- `outputs/data/rail_allmodes_naptan_{eligible,excluded}_nlcs.csv` — the
  audit trail for the current 403-station clustered population and the
  16-station NaPTAN exclusion decision.
- `outputs/figures/canonical_vs_allmodes_k5_map.png` — side-by-side map.
- `outputs/figures/rail_allmodes_bic_grid.png`, `rail_allmodes_kdiag.png` —
  BIC-by-covariance and the 5-panel K-diagnostics, in the canonical style.
- `outputs/figures/rail_allmodes_k{5,6,7}_profiles.png` — per-cluster
  temporal entry/exit usage-share profiles (median + 10-90% band),
  day-by-day across the full week.
- `outputs/figures/rail_allmodes_k{5,6,7}_map.png` — standalone station
  cluster maps on an LSOA basemap, added non-LU stations shown as
  triangles.
- `outputs/report/STABILITY_K5_K6_ALLMODES.md` — **validation report, not
  official** (see item 9 above and "Interpretation boundary" below). The
  bootstrap/seed-stability battery for K=5 vs K=6, rerun 2026-08-07 on all
  403 stations. K=5 has higher seed stability (0.859 vs 0.672), slightly
  higher paired bootstrap ARI (0.480 vs 0.454), and fewer weak bootstrap
  components (3 vs 5) -- **these three numbers are agreement-with-adopted-
  labels statistics from this validation battery, not the official
  `rail_allmodes_k_selection_panel.csv` figures** (which read 0.964 / 0.510
  respectively for K=5's mean pairwise seed ARI / bootstrap ARI). Do not
  quote this bullet's numbers next to the official K-selection figure.
- `outputs/figures/rail_allmodes_k5_k6_{transition_heatmap,
  cluster_silhouette_comparison, bootstrap_cluster_stability,
  bootstrap_global_stability, bootstrap_paired_ari_difference}.png` — the
  same five diagnostic figures `rail_k_selection_validation` produces for
  canonical's K=5 vs K=6, reproduced here.
- `outputs/report/STABILITY_K5_K7_ALLMODES.md` (rerun 2026-08-07) — **also a
  validation report, not official**, same caveat as the K5-vs-K6 bullet
  above. The same battery for K=5 vs K=7. K=5 has much higher seed stability
  (0.859 vs 0.559); paired bootstrap ARI is effectively tied (0.480 vs
  0.481), so it does not discriminate. Any pre-existing `allmodes_k6_k7_*` files/figures
  at the top level of `outputs/data`/`outputs/figures` predate the old 404-station NaPTAN
  filter (dated 2026-07-22, before the 2026-07-24 01:33 finalisation) and
  must not be cited — they are stale duplicates of what is properly
  archived under `outputs/pre_merge_archive/`. In the corrected result,
  K=5-to-K=7 ARI is 0.723 and 76.7% of stations are covered by the best
  one-to-one matches. **Conclusion: K=5 remains the best-supported choice
  against both adjacent candidates.**
- `outputs/figures/rail_allmodes_k5_k7_{transition_heatmap,
  cluster_silhouette_comparison, bootstrap_cluster_stability,
  bootstrap_global_stability, bootstrap_paired_ari_difference}.png` — same
  five diagnostics, for the K=5 vs K=7 pair.
- `outputs/pre_merge_archive/`, `outputs/archive_strict_extent_v1/`,
  `outputs/archive_420station_allmodes/` — superseded intermediate
  results, kept for provenance only (each has its own README explaining
  why it was superseded).

## Interpretation boundary

Finding 1 (BIC-optimal K) and the K=5/K=6 and K=5/K=7 stability batteries
are all single- or bounded-replicate comparisons on a station population
that has had less manual review than canonical's 270. K=5 is now the
best-supported choice against both of its closest BIC rivals (K=6 and
K=7) on this dataset, conditional on the current 344-dim feature
definition, the diag-GMM family, and the 14-site merge rule; this is not,
by itself, a claim that K=5 is the "true" number of rail night-activity
types. See each report's own fallacy and limitations sections before
citing a specific number in the dissertation.

**Which K-selection source is official (resolved 2026-08-17).** A
write-up draft cited `07_stability_allmodes.py`'s K5-vs-K6/K7 numbers
(seed ARI 0.859, bootstrap ARI 0.480, weakest-cluster Jaccard 0.399) next
to the official K-selection figure, whose K=5 axis values are actually
0.964 / 0.510 / 0.301. Both sets of numbers are correct for what they each
measure, but they measure different things:

| | `08_k_selection_panel.py` (**official**) | `07_stability_allmodes.py` (validation) |
|---|---|---|
| Reference partition | none privileged -- pairwise among 5 same-budget refits | the saved/adopted K=5 labels |
| Seed budget | 5 seeds x n_init=200 | 20 seeds x n_init=100 |
| Bootstrap replicates | 50 | 200 |
| Weakest-cluster Jaccard | mean of each replicate's own minimum (mean-of-mins) | minimum of each cluster's own mean (min-of-means) |
| K=5 seed ARI / bootstrap ARI / weakest Jaccard | 0.964 / 0.510 / 0.301 | 0.859 / 0.480 / 0.399 |

**Rule: any number cited in the dissertation for random-seed ARI,
bootstrap ARI, or weakest-cluster Jaccard at the adopted K must come from
`rail_allmodes_k_selection_panel.csv` (item 10).** `07_stability_allmodes.py`'s
STABILITY_K5_K6/K7_ALLMODES reports remain valid as a separate, clearly
-labelled robustness check (structural comparison against an adjacent K),
but are not a substitute source for those three figures.

---

## Method tests against this result (added 2026-08-01)

**Provenance note:** the numerical results in this method-test section were
generated before the Paddington correction and have not been promoted into
the 2026-08-07 result. They remain useful historical sensitivities, but must
be rerun against the 403-station matrix before being cited as current.

The interpretation boundary above states that K=5 is conditional on "the
current 344-dim feature definition". Two of the three conditionals in that
sentence have since been tested. The tests are **not** in this folder — this
folder stays read-only and canonical — they live in
**`FYP/rq1_rail_method_tests/`**, which is anchored to this result so that the
two cannot drift apart.

**Anchoring.** `rq1_rail_method_tests/src/01_prepare_features.py` rebuilds this
folder's feature matrix from the same preprocessed input and asserts it against
`outputs/data/X_rail_allmodes.parquet` (max absolute difference must be 0). The
adopted K=5 labels are reproduced there at ARI = 1.000 and the K=5/K=6/K=7 seed
stability numbers (0.894 / 0.624 / 0.703) are reproduced independently. Any
future change to this folder that the tests do not track will make `01` fail.

| conditional | test | verdict |
|---|---|---|
| normalisation denominator (full-week vs per-day-type closure) | 2x2 in `rq1_rail_method_tests`, both windows | full-week retained; day-type closure raises zero-cell domination (eta² 0.13→0.43) and moves the BIC optimum from K=5 to a K=7-11 plateau |
| day-type window length (native 344 vs padded to a common 18:00-05:00, 440) | same 2x2, plus `06_robustness_padded.py` at the converged optimum | padding is inert: ARI 0.885 against this result, the smallest cluster is the identical 12 stations, 16 of 404 stations (4.0%) change |
| diag-GMM family, pre-correction 13-site merge rule | not tested in this historical method-test run | must be rerun before current citation |

**One numerical caveat this folder should adopt.** The padded matrix does not
converge at `N_INIT = 20`; it needs >= 50. This folder's own native matrix does
converge at 20 (verified identical at n_init = 20/50/100/200; a marginally
better optimum at n_init = 300 differs by one station), so no change is
required here — but any NEW feature space should have its n_init convergence
checked before its cluster structure is interpreted, because the under-converged
padded fit produced a *more* attractive-looking typology than the correct one.

**Second-stage structure.** `rq1_rail_method_tests/src/08_substructure_screen.py`
screens every cluster of this result for reproducible substructure under one
uniform protocol. All four clusters with n >= 25 carry some; the splits are
reported there, not adopted here.

---

## K = 5: current selection evidence (rerun 2026-08-07)

The Paddington-corrected 403-station matrix was evaluated with the same
equal-budget panel (five seeds, `n_init=200` per K). K=5 is selected on the
joint reading of BIC, stability and interpretability set out here.

### BIC and stability both support K=5 on the corrected data

The equal-budget panel gives:

| K | best BIC (5 seeds x n_init=200) |
|---|---|
| 5 | **-1,900,159.5** |
| 6 | -1,900,063.5 |
| 7 | -1,898,546.3 |

| K | seed ARI (mean pairwise) | seeds reaching the best basin | bootstrap ARI | weakest cluster Jaccard |
|---|---|---|---|---|
| 5 | **0.964** | 1/5 | **0.510** | **0.301** |
| 6 | 0.486 | 1/5 | 0.449 | 0.135 |
| 7 | 0.469 | 1/5 | 0.442 | 0.116 |

The BIC gap between K=5 and K=6 is small relative to the overall criterion,
but K=5 is far more reproducible across seeds and has the strongest weakest-
cluster bootstrap recovery.

### Interpretability, including a criterion specific to this study

The 31-station night-persistent cluster is the study's headline structure, so
whether a K preserves it is a selection criterion. Jaccard against its best host
cluster, averaged over seeds:

| K | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|
| night-persistent group survival | — | — | — | **0.988** | 0.789 | 0.469 | — | — |

K=5 preserves this group most consistently; K=7 fragments it materially.

### What K = 5 does not fix

The adopted K=5 partition still has uneven separation. The 26-station central
departure cluster has the lowest mean silhouette (-0.063), whereas the
167-station inner/mid arrival cluster is much more compact (0.230). Cluster
names are descriptive summaries, not claims that every member is strongly
separated from all alternatives.

Evidence: `outputs/figures/rail_allmodes_k_selection_panel.png` and
`outputs/data/rail_allmodes_k_selection_panel.csv` (K = 2..9, all indices).
