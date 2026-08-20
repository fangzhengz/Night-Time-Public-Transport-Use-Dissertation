# Repository Setup Notes

This note documents how this repository was assembled from the working
research directory, for anyone (including future me) trying to understand
what is and isn't included here.

## Provenance

This repository is a curated, redistributable snapshot of a larger local
working directory used throughout the dissertation project. It was built by
selectively copying folders and files — **no analysis scripts were modified**
in the process — while excluding raw data, cached intermediates, and
copyrighted materials that cannot be redistributed.

## What was excluded

- **Raw source data**: the original BUSTO (~1.1 GB) and NUMBAT (~58 MB)
  datasets, which are subject to their providers' own licensing terms. See
  [`DATA_SOURCES.md`](DATA_SOURCES.md) for how to obtain them directly.
- **Literature/reference PDFs** (~185 MB) and prior dissertation drafts
  (~85 MB), for copyright reasons.
- **Large intermediate Parquet files** (~12–14 MB each): not copied, but
  fully reproducible by re-running the relevant pipeline scripts against the
  raw data.
- **Broken symlinks** (e.g. stray `node_modules` links) and stale RQ3 output
  files — RQ3 (mismatch analysis) is kept as code + documentation only, with
  no cached outputs, since that direction was deprioritized during the
  project (see `METHODOLOGY_TIMELINE.md`).

## Folder organization

Original folder names and internal structure were preserved so that every
script's relative paths still work; folders were only grouped, not renamed,
under these top-level categories:

- `data_processing/{bus_stoparea, rail_allmodes}` — the two preprocessing
  pipelines (bus and rail).
- `clustering/{bus, rail}` — the final adopted clustering results (bus K=4,
  rail K=5).
- `rq2_associations/{lnwc_imd, independent_variables, loac,
  facility_diversity_sidecar, spatial_signatures_sidecar}` — the five RQ2
  association analyses.
- `bus_rail_relation_analysis` — the bus/rail spatial overlay analysis.
- `sensitivity_checks/{rq1_bus_05cutoff_sensitivity,
  rq1_bus_k_selection_check, rq1_bus_geography_diagnostic}` — robustness
  checks for the RQ1 clustering solution.
- `archive_methodology/` — eleven historical/superseded methodology
  iterations (hub-first allocation, ILR transform, day-type normalization,
  etc.), kept for transparency about the analytical path taken.
- `dissertation/final_figures/` — the Chapter 4 figures used in the final
  text, plus a provenance manifest.
- `rq3_mismatch_analysis/` — code and documentation only (no outputs; see
  above).
- `map/` — LSOA boundary GeoJSON files used for mapping.
- `legacy_analysis_scripts/` — early exploratory code kept for reference.

## Data flow verification

The authoritative path from raw data to each dissertation figure/table was
reverse-verified against the hardcoded paths in `build_ch4_final_figures.py`:

| Dissertation output | Input data | Source folder |
|---|---|---|
| Table 4.1 (clustering solutions) | `k4_labels.csv`, `rail_cluster_names.csv` | `rq1_bus_stoparea_clustering/outputs_1805_min33/clr/labels/` + `numbat_all_area_test/outputs/data/` |
| Table 4.2 (behavioral metric tests) | `*_cluster_metric_significance.csv` | `rq2_new_clusters_analysis/outputs/data/` |
| Figure 4.1 (K selection) | `kdiag.csv` (bus), `rail_allmodes_k_selection_panel.csv` (rail) | respective output directories |
| Figures 4.8/4.9 (contextual profiles) | `*_cluster_matrix_z.csv` | `rq2_independent_variables/outputs/data/` |
| Figures 4.6/4.7 (LNWC enrichment) | `rail/bus_enrichment.csv` | `rq2_new_clusters_analysis/outputs/data/` |

Conclusion: every number quoted in the dissertation text traces back to a
script + output file in this repository — there are no "orphaned"
intermediate results.

## Reproducing the figures

No raw data is required to regenerate the Chapter 4 figures from the
already-committed intermediate results:

```bash
cd dissertation
python ../scripts/build_ch4_final_figures.py
# outputs all main-text figures to final_figures/
```

To understand the full method behind any single analysis, each analysis
folder has its own `README.md` describing inputs, outputs, and script run
order. `dissertation/final_figures/FIGURE_SOURCE_INVENTORY.md` records the
exact data source for every figure, and
`dissertation/narrative_arc_and_source_index.md` records key methodological
decisions and their dates/rationale.

`METHODOLOGY_TIMELINE.md` explains why the StopArea allocation, CLR
transform, K=4 (bus), and the 18:00–05:00 night window were adopted;
`archive_methodology/` preserves the abandoned alternatives (hub-first
allocation, ILR transform, etc.) and their diagnostics, and each sensitivity
check folder documents its own validation result independently.

## Relationship to the original working directory

This repository is a clean, public-facing copy. The original working
directory (not published) retains all in-progress drafts, caches, and
experimental folders used during active development; this repository is not
affected by, and does not need to track, that ongoing work.
