# RQ2 continuous variables + LNWC + IMD (official RQ1/RQ2 result)

This workspace records the point where the clustering work and the contextual work finally met. Earlier LNWC trials had used provisional labels and a 1,200 m Rail catchment; later model corrections changed both modes, while the spatial interpretation narrowed to an 800 m walking-scale context. The folder therefore contains more than one historical layer. Read chronologically, it shows how the final association analysis was rebuilt rather than simply renamed after the upstream typologies changed.

**Status (rerun 2026-08-07): this folder is the primary RQ1/RQ2 result**, not a
sensitivity check. It was originally built 2026-07-23/24 as a non-canonical
sensitivity analysis comparing two alternative clusterings against
`cluster_clean_version_fullweek/` / `rq1_context_metrics_analysis/` /
`rq2test analysis/` ("canonical": rail 270-station Underground-only K=5, bus
K=3 raw_share, pre-StopArea). Both clusterings it uses have since been
promoted:
- **Bus** StopArea CLR K=4 was adopted 2026-07-29 (see
  `project_bus_clr_k4_final_adoption_2026-07-29.md`) because internal
  coherence *and* external LNWC/IMD association both improved over
  canonical K=3.
- **Rail** all-modes K=5 was adopted 2026-07-30 (see
  `project_rail_allmodes_k5_vs_k7_decision_2026-07-30.md`) after a full
  K=5-vs-K=6 and K=5-vs-K=7 bootstrap/seed stability battery confirmed K=5
  as the best-supported K within that scope. **Unlike bus, rail's adoption
  is a scope decision, not an association-strength one** -- see "Headline
  result" below, this is important and should not be glossed over in the
  write-up.

  On 2026-08-07 the adopted rail result was fully regenerated after adding
  the missing Paddington NR/TfL co-location rule. Paddington is now one
  observation; the current rail population is 403 stations. All current
  context, LNWC, IMD and bus–rail relation outputs were regenerated from
  these labels.

Canonical (`cluster_clean_version_fullweek/`, `rq1_context_metrics_analysis/`,
`rq2test analysis/`) is kept, unmodified, as the superseded historical
reference -- its 7/16-PPT-era numbers should no longer be cited as the
current result.

## Clustering results used

- **Rail**: `numbat_all_area_test`'s all-modes merged clustering (LU + DLR +
  Overground + Elizabeth line, co-located NLCs merged), K=5, NaPTAN-matched
  **403-station refit** (after merging Paddington NR/TfL; 16 stations excluded for having no
  NaPTAN Greater-London coordinate match at all -- Reading, Slough,
  Maidenhead, Watford Junction, Shenfield, etc., confirmed genuinely outside
  Greater London). This mirrors canonical's own scope convention: canonical's
  270-station clustering already includes several border Underground
  stations outside the strict Greater London boundary (Amersham, Chesham,
  Epping, etc.) and only excludes them *downstream* from LNWC/IMD, not from
  the clustering itself -- so this refit does the same. K=5 was confirmed
  2026-07-30 as the best-supported K against both of its closest BIC rivals
  (K=6 and K=7) on a 200-bootstrap/20-seed stability battery -- see
  `numbat_all_area_test/README.md` and
  `numbat_all_area_test/outputs/data/rail_allmodes_k_selection_panel.csv`
  and the current stability outputs.
- **Bus**: `rq1_bus_stoparea_clustering`'s official StopArea allocation, CLR
  feature transform, K=4 -- adopted 2026-07-29 (BIC-preferred K for CLR; the
  bootstrap min-cluster Jaccard is 0.401 at K=4 vs 0.883 at K=3, a known and
  disclosed stability tradeoff -- see
  `rq1_bus_stoparea_clustering/outputs/clr/diagnostics/kdiag.csv`). 3,372
  LSOAs (min_direction>=36, single-condition sample rule). This folder
  previously pointed at the `strict_min72_raw_share` sensitivity sample
  (K=4, 3,009 LSOAs, min direction>=72); that sample is still available as a
  sensitivity check but was never adopted -- CLR StopArea K=4 (a different,
  later K=4 candidate) is what's actually adopted.

**Why the rail refit**: the original 420-station all-modes K=5 included 16
stations with no NaPTAN Greater-London match at all, which made up 17.6%
(12/68) of one cluster alongside several large National Rail interchanges
with activity comparable to the two largest clusters. Excluding them before
fitting (not just downstream) changed the partition substantially --
ARI=0.492 vs the pre-exclusion result on the then-current 404 common stations, and the
BIC-preferred K shifted from 6 to 5 -- see `numbat_all_area_test/README.md`
for the historical before/after and verification battery. The later Paddington
correction changes the population from 404 to 403; against the immediately
preceding 404-station labels, the corrected common-station partition has
ARI=0.670, so the change is not merely cosmetic.

## What this folder deliberately does NOT include

The pooled, cluster-blind continuous-metric x LNWC/IMD "main line" test
(`rq2test analysis/src/run_direct_metrics_analysis.py` /
`run_imd_analysis.py`'s main line) is not reproduced here. It pools every
station/LSOA regardless of cluster and cannot say which cluster drives an
observed relationship -- flagged provisional since 2026-07-14, still a
separate open item independent of which clustering is primary (see
`project_rq2_continuous_metrics_status.md`).

## Run

From this folder, in order (each script reads the previous one's output):

```powershell
py -3 src/run_context_metrics.py
py -3 src/run_lnwc_analysis.py
py -3 src/run_imd_analysis.py
py -3 src/build_comparison_report.py
```

## Folder structure

```text
rq2_new_clusters_analysis/
├── README.md
├── src/
│   ├── config.py
│   ├── run_context_metrics.py       # continuous variable layer + internal KW/epsilon^2
│   ├── run_lnwc_analysis.py         # cluster x LNWC (rail: fresh 403-station Voronoi)
│   ├── run_imd_analysis.py          # cluster x IMD2025 weak line
│   └── build_comparison_report.py   # joins the three legs + compares vs canonical
└── outputs/
    ├── data/
    ├── figures/
    ├── spatial/
    ├── report/
    └── workbook/
```

## Main outputs

- `outputs/report/CONTEXT_METRICS.md`, `LNWC_ASSOCIATION.md`,
  `IMD_ASSOCIATION.md`: per-stage results.
- `outputs/report/COMBINED_COMPARISON.md`: internal coherence + LNWC + IMD
  joined into one table per mode, current vs the retired canonical result
  side by side. **Cite this for current RQ1/RQ2 numbers**, not
  `rq2test analysis`'s outputs.
- `outputs/data/comparison_internal_coherence.csv`,
  `comparison_external_association.csv`: the same comparison as
  machine-readable tables.

## Headline result (last regenerated 2026-08-07)

- **Bus StopArea CLR K=4**: internal coherence and external LNWC/IMD
  association both improve over the old canonical K=3 (raw_share,
  pre-StopArea), including on canonical's two specific weak spots
  (direction_balance, weekend_ratio). Current LNWC Cramer's V is 0.252 and
  IMD epsilon-squared is 0.063.
- **Rail all-modes K=5 (403 stations clustered, 387 LNWC/IMD-eligible)**:
  **internal coherence is mixed and external LNWC/IMD association is still
  consistently weaker than the old canonical 270-station Underground-only
  result** (LNWC Cramer's V 0.381 vs 0.443; IMD epsilon-squared 0.049 vs
  0.123) -- adopting all-modes K=5 as primary does **not** reverse this. The
  reason it was adopted anyway is a scope-defensibility argument, not an
  association-strength one: it directly answers the "why Underground only,
  not all NUMBAT rail modes" question raised at the 2026-07-17 supervisor
  meeting, and K=5 is the best-supported K within that wider scope (BIC
  outright winner, and more stable than both K=6 and K=7 under bootstrap/seed
  resampling). **Any write-up citing this result should state both facts
  together**: the scope is now more defensible, but the cluster-to-context
  story is weaker than the narrower Underground-only version was.

## Interpretation boundary

These are area-level associations between observed transport-use patterns
and area context (LNWC, IMD), not passenger-level or causal claims. Sample
universes differ across rows in the comparison tables (different N per
clustering), so effect-size differences are directional evidence, not a
controlled like-for-like test.
