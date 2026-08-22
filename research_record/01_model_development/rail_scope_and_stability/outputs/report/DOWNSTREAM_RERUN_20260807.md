# Post-Paddington Rail downstream rerun record

**Run date:** 2026-08-07  
**Rail clustering input:** current post-Paddington all-modes Rail result  
**Current clustered Rail universe:** 403 stations, K=5

This record documents the active downstream analyses re-executed after the
Paddington NR/TfL co-location correction and the resulting Rail refit.  All
analyses below read the current Rail labels directly, or use current Rail
station coordinates/catchments produced by that refit.

## Rerun analyses and current outputs

| Downstream analysis | Current output | Relevant Rail universe |
|---|---|---|
| RQ2 context metrics, LNWC, IMD and 800 m sensitivity | `FYP/rq2_new_clusters_analysis/outputs/report/COMBINED_COMPARISON.md` and `outputs_800m/report/` | 403 clustered; 387 in strict spatial/context coverage |
| LOAC association | `FYP/rq2_loac_analysis/outputs/report/RESULTS_SUMMARY.md` | 387 / 403 |
| Spatial Signatures association | `FYP/rq2_spatial_signatures_analysis/outputs/report/RESULTS.md` | 387 / 403 |
| Facility diversity association | `FYP/rq2_facility_diversity_analysis/outputs/report/RESULTS.md` | 387 / 403 |
| Independent-variable contextual analysis and figures | `FYP/rq2_independent_variables/outputs/report/RESULTS.md` | 403 labels; 389 complete-variable observations |
| Bus--Rail spatial relation and station-level permutation test | `FYP/bus_rail_relation_analysis/outputs/report/RESULTS.md` | 403 clustered stations |
| RQ3 MSOA mismatch, mode decomposition, hourly check and map | `FYP/rq3_mismatch_analysis/outputs/report/` | Rail activity geography is retained independently of clustering; the RQ1 label check uses current labels |
| RQ3 RQ1-cluster descriptive check | `FYP/rq3_mismatch_analysis/outputs/report/RQ1_CLUSTER_CHECK.md` | 279 MSOAs linked to the current 403-station labels |
| Active Rail nested-substructure screen | `FYP/numbat_all_area_test/cluster_substructure/outputs/` | current C1 (26 stations) and C4 (167 stations) |

## Interpretation of differing denominators

The 403-station figure is the current Rail clustering universe.  The 387 used
in the core RQ2 contextual analyses is the stricter spatial/context coverage
universe.  The independent-variable table has its own complete-variable rule,
leaving 389 observations.  These are analysis-specific eligibility rules, not
alternative Rail cluster fits.

The RQ3 main activity panel intentionally retains a wider Rail geographic
universe before its MSOA linkage because it analyses observed public-transport
activity, rather than only the station-clustering sample.  Its RQ1 cluster
check separately links the current 403-station labels to MSOAs.

## Nested-substructure compatibility note

After the corrected refit, the former central departure-dominant pattern is
top-level **C1** (26 stations), not C2.  The active nested screen was therefore
re-anchored to C1.  New active files use `c1_*` and `c1ab_*` names.  The
compatibility-named `nested_c2_map.*` is a current C1 map retained only to avoid
breaking an existing file reference; the current README states this explicitly.

## Historical material not rerun

Archived exploratory Rail variants and their archived figures were not
overwritten.  They are not inputs to the active RQ1/RQ2/RQ3 outputs listed
above and should remain labelled as historical rather than being cited as the
current result.
