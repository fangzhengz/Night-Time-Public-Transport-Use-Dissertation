# Night-Time Transit Clustering and Deprivation in London: Code and Results

**Title**: Mapping Night-Time Transit Activity Clusters and Their Relationship to Night-Worker and Deprivation Indicators in London

**Author**: [Your Name]  
**Institution**: CASA, UCL  
**Academic Year**: 2025–2026

---

## Overview

This repository contains code, processed data, and results for a dissertation studying night-time bus and rail transit clusters in London and their association with night-worker residence (LNWC) and deprivation (IMD/LOAC).

### Key Questions

1. **RQ1**: Where and when do night-time transit users concentrate? (clustering)
2. **RQ2**: How do these clusters align with night-worker residence and deprivation?
3. **Bus×Rail**: Do bus activity clusters organise around rail nodes?

### Key Results

- **Bus**: 4 clusters (StopArea-level, CLR K=4, 18:00–05:00 window)
  - Night-persistent high-activity cluster (1,383 LSOAs, 40.6% of fitted demand)
  - Explains 52% of activity variance, associated with LNWC night workers (ρ=0.254, p<0.001)
  
- **Rail**: 5 clusters (all-modes including LU/DLR/LOD, K=5, 403 stations post-Paddington merge)
  - Inner night-destination cluster enriched for LNWC (V=0.381, p<0.001)
  - Clear night/day functional specialisation across clusters
  
- **Spatial**: 54.3% of bus LSOAs within 400 m of a rail station are night-persistent clusters (vs 33.5% baseline); sharp walking-distance effect, stable across concentric rings

---

## Repository Structure

```
├── README.md                         (this file)
├── DATA_SOURCES.md                   (guide to obtaining raw data not in repo)
├── METHODOLOGY_TIMELINE.md           (evolution of methods; archive notes)
├── .gitignore
│
├── data_processing/                  (preprocessing pipelines, NOT raw data)
│   ├── bus_stoparea/                 (bus data → LSOA-level features)
│   │   ├── src/                      (Python scripts)
│   │   ├── outputs_1805_min33/       (18:00–05:00 adopted; archived outputs/ is 06:00 old window)
│   │   └── README.md
│   └── rail_allmodes/                (NUMBAT → station-level features)
│       ├── src/
│       ├── outputs/                  (current K=5, 403 stations post-Paddington)
│       └── README.md
│
├── clustering/
│   ├── bus/                          (← rq1_bus_stoparea_clustering)
│   │   ├── src/                      (clustering pipeline)
│   │   ├── outputs_1805_min33/       (K=4 CLR labels + diagnostics; adopted)
│   │   ├── cluster_substructure/     (nested 3-way split of night-persistent cluster)
│   │   └── README.md
│   └── rail/                         (← numbat_all_area_test)
│       ├── src/
│       ├── outputs/                  (K=5 labels + diagnostics)
│       ├── cluster_substructure/     (West End night-origin core diagnostic)
│       └── README.md
│
├── rq2_associations/
│   ├── lnwc_imd/                     (← rq2_new_clusters_analysis)
│   │   ├── src/
│   │   ├── outputs/                  (primary: 800m equal-weight)
│   │   ├── outputs_800m/             (area-weighted sidecar, stable results)
│   │   └── README.md
│   ├── independent_variables/        (← rq2_independent_variables)
│   │   ├── data/                     (Census/BRES CSVs, <2MB)
│   │   ├── outputs/data/*_z.csv      (20-variable z-score matrices)
│   │   └── README.md
│   ├── loac/                         (← rq2_loac_analysis)
│   │   ├── src/
│   │   └── outputs/
│   └── facility_diversity_sidecar/   (← rq2_facility_diversity_analysis)
│       └── (POI analysis; raw geodata excluded per .gitignore)
│
├── bus_rail_relation/                (Clara's "does bus sit next to rail?" analysis)
│   ├── src/
│   ├── outputs/
│   └── README.md
│
├── sensitivity_checks/
│   ├── rq1_bus_05cutoff_sensitivity/  (18:00–05:00 vs 06:00 window)
│   ├── rq1_bus_k_selection_check/     (seed stability for K=2–8)
│   └── rq1_bus_geography_diagnostic/  (central/outer LSOA mixing audit)
│
├── dissertation/
│   ├── final_figures/                 (Chapter 4 figures + tables)
│   │   ├── FIGURE_SOURCE_INVENTORY.md (data source for each figure)
│   │   ├── Figure_4_*.png             (main-text figures)
│   │   ├── Appendix_*.png             (appendix figures)
│   │   └── Table_4_*.csv              (main-text tables)
│   ├── main_body_current.docx         (current dissertation main body)
│   ├── TRANSFORM_MAP.md               (structural edit audit trail)
│   └── narrative_arc_and_source_index.md (Decision log + result sources)
│
├── archive_methodology/              (Historical method iterations; for reference only)
│   ├── hub_first_reclustering/       (pre-adopted bus method)
│   ├── rq1_bus_ilr_transform/        (tested but not adopted)
│   ├── rq1_rail_method_tests/        (robustness diagnostics for rail)
│   ├── historical_reference_cluster_clean_version_fullweek/  (prior canonical version)
│   └── rq2test analysis/             (earlier RQ2 baseline, superseded)
│
├── rq3_mismatch_analysis/            (Code only; RQ3 formally dropped 2026-08-05)
│   ├── src/
│   └── README.md
│
├── map/
│   └── London_LSOA_2021_Boundaries.geojson  (spatial reference)
│
└── legacy_analysis_scripts/          (early exploratory notebooks, reference only)
    └── analysis code/
```

### What Is NOT Included

- **Raw data** (1.5GB+): Bus/rail transaction CSVs, NUMBAT Excel files, POI geodatabases. See `DATA_SOURCES.md` for acquisition.
- **Intermediate parquet files**: Large regenerable processed datasets (preprocessed bus/rail features). See `.gitignore`; scripts regenerate them from source as needed.
- **Tool caches** (`.codex_review*`, `.agents`, `.claude`, etc.): Removed before commit.
- **Dissertation drafts**: Only the current version + final figures kept; earlier versions and QA subdirectories excluded.

---

## Quick Start: Reproduce Figures

All Chapter 4 figures and tables in the dissertation can be regenerated from this repository **without** raw data:

```bash
cd dissertation
python ../scripts/build_ch4_final_figures.py
```

This script reads locked cluster labels and intermediate result CSVs already in the repo, and outputs all main-text figures to `dissertation/final_figures/`.

**Data dependency**: The script requires Python 3.8+, pandas, geopandas, matplotlib, numpy. See individual analysis folders for full environment specs.

---

## Methodology Overview

### Bus Clustering (RQ1)

- **Input**: TfL iBUS quarter-hour demand data, stop-level aggregated to StopArea geometry
- **Method**: Gaussian Mixture Model (GMM) with Centered Log-Ratio (CLR) compositional algebra, K=4, 18:00–05:00 window
- **Output**: 3,383 fitted LSOAs classified into 4 night-activity clusters
- **Key paper**: `clustering/bus/README.md` + `data_processing/bus_stoparea/README.md`

### Rail Clustering (RQ1)

- **Input**: TfL NUMBAT multi-modal (LU/DLR/LOD) station entry/exit data
- **Method**: GMM, K=5, 18:00–05:00 window across 5 day-types, 403 stations (post-Paddington co-location fix)
- **Output**: 403 stations classified into 5 night-functional clusters
- **Key paper**: `clustering/rail/README.md` + `data_processing/rail_allmodes/README.md`

### LNWC and IMD Association (RQ2)

- **Method**: Two-layer analysis
  1. Omnibus Kruskal-Wallis + epsilon² for each contextual variable vs cluster membership
  2. Per-cluster z-score profiles (20 variables)
- **Variables**: Deprivation (IMD quintiles), night-worker presence (LNWC categories), infrastructure (POI density), employment (BRES workplace counts by sector)
- **Primary sidecar**: LOAC supergroup classification (separate ecological perspective)
- **Key papers**: `rq2_associations/lnwc_imd/README.md` + `rq2_associations/independent_variables/README.md`

### Bus×Rail Spatial Relationship

- **Finding**: Bus night-persistent clusters concentrate within 400 m of rail stations (54.3% vs 33.5% baseline)
- **Design**: Point-in-polygon distance + permutation test for cluster×rail-type contingency
- **Key paper**: `bus_rail_relation/README.md`

**For detailed methodology, see README.md in each analysis folder and `dissertation/` decision logs.**

---

## Key Decisions and Rationale

### Why K=4 for Bus? Why K=5 for Rail?

See `sensitivity_checks/rq1_bus_k_selection_check/` for the seed stability battery (n_init=100, K=2–8). K=4 is reproducible (bootstrap Jaccard 0.534); K=3 is less stable. For rail, see `clustering/rail/README.md` and `clustering/rail/outputs/` for the K-selection diagnostic panel.

### Why 18:00–05:00? Why Not 06:00?

See `sensitivity_checks/rq1_bus_05cutoff_sensitivity/` which reprocesses under both windows. The 05:00 cutoff is tighter to true night hours; both windows give similar results but 05:00 is formally adopted.

### Why StopArea Not Hub-First?

See `METHODOLOGY_TIMELINE.md` under "Phase 1", and `archive_methodology/rq1_bus_hub_first_reclustering/README.md`. Hub-first had systematic central/outer mixing artefacts (ARI=0.570). StopArea is simpler and cleaner.

### Why Compositional CLR and Not Raw Shares?

CLR is applied post-hoc for significance testing (zero-bin dominance in GMM), not as a coordinate transformation. Raw shares were the original input. See `clustering/bus/README.md` for diagnostics; both are defensible but raw shares are primary in final report.

### Why Not Just Use LOAC as a Single Variable?

LOAC is a pre-made composite classification; using it directly would mask the ecological-fallacy vulnerability (e.g., an LSOA classified as one supergroup may contain night workers from another). Instead, we analysed LOAC separately in `rq2_associations/loac/` and let the night-worker + deprivation variables speak for themselves in the main RQ2 results.

---

## About Archived Folders

`archive_methodology/` contains historical method iterations (hub-first clustering, ILR/Hellinger transforms, daytype padding, earlier GMM prototypes). These are **not** part of the adopted analysis and should not be cited. They are archived for:

1. **Reproducibility**: So future readers can understand why certain choices were made (and others rejected)
2. **Audit trail**: If a reviewer questions a decision, the alternative can be inspected
3. **Education**: For future students who want to understand clustering pitfalls

See `METHODOLOGY_TIMELINE.md` for a summary of why each was discarded.

---

## Output Conventions

### Clustering Results

Each clustering folder outputs:
- `outputs/data/*.csv`: Cluster labels + metadata (K, covariance type, BIC, etc.)
- `outputs/figures/*.png`: Silhouette, temporal profiles, maps
- `outputs/report/RESULTS.md`: Full diagnostic text

### Association Results

Each RQ2 folder outputs:
- `outputs/data/*.csv`: Test statistics (Kruskal-Wallis H, p-values, epsilon²) + z-score matrices
- `outputs/figures/*.png`: Heatmaps + bar charts + spatial maps
- `outputs/report/RESULTS.md`: Interpretation + caveats

### Dissertation

- `dissertation/final_figures/FIGURE_SOURCE_INVENTORY.md`: Which data file feeds each figure; one-stop source truth
- `dissertation/main_body_current.docx`: Latest dissertation draft

---

## Reproducibility and Replication

### To reproduce all figures from the repository (without raw data):

```bash
cd dissertation
python ../scripts/build_ch4_final_figures.py
```

This regenerates `dissertation/final_figures/*.png` + `*.csv` from locked clustering labels and result CSVs.

### To fully replicate from raw data:

1. Acquire raw BUSTO, NUMBAT, and boundary data (see `DATA_SOURCES.md`)
2. Edit path references in `data_processing/*/src/config.py`
3. Run preprocessing pipelines:
   ```bash
   cd data_processing/bus_stoparea && python src/run_pipeline.py
   cd ../rail_allmodes && python src/run_pipeline.py
   ```
4. Run clustering:
   ```bash
   cd clustering/bus && python src/run_pipeline.py
   cd ../rail && python src/run_pipeline.py
   ```
5. Run RQ2 associations:
   ```bash
   cd rq2_associations/lnwc_imd && python src/run_pipeline.py
   cd ../independent_variables && python src/run_pipeline.py
   ```

Each folder's README contains the exact command sequence and expected runtimes.

---

## Scope and Limitations

### Geographic Scope
- London only (Greater London Authority boundary)
- Rail is London Underground + DLR + London Overground (not National Rail except Paddington TfL link)
- Bus is TfL bus routes only

### Temporal Scope
- One week (Oct–Nov 2024)
- Full-week analysis (weekday + weekend aggregated)
- Night defined as 18:00–05:00 (6 PM to 5 AM)

### Data Limitations
- Night-worker census (LNWC) is a proxy; true night-shift rosters not available
- Deprivation (IMD) is LSOA-level, not individual-level
- Bus/rail data are **transactions** (entries/exits), not origins/destinations; OD flows not available in this project

### Ecological Fallacy
- All analyses are at LSOA or station level, not individual level
- Ecological inference to individuals is invalid; see Discussion for limitations

---

## Citation

If you use code or data from this repository, please cite:

```bibtex
@mastersthesis{author2026nighttransit,
  author = {[Your Name]},
  title = {Mapping Night-Time Transit Activity Clusters and Their Relationship to Night-Worker and Deprivation Indicators in London},
  school = {University College London, Department of Geography},
  year = {2026}
}
```

For individual analyses, see the README.md and RESULTS.md files in each folder for more granular citations.

---

## Questions and Issues

- **Methodology**: See the relevant README.md in each analysis folder
- **Data provenance**: See `DATA_SOURCES.md` and `dissertation/narrative_arc_and_source_index.md`
- **Figure sources**: See `dissertation/final_figures/FIGURE_SOURCE_INVENTORY.md`
- **Historical decisions**: See `METHODOLOGY_TIMELINE.md` and `dissertation/TRANSFORM_MAP.md`

---

## License

This repository is provided for educational and research purposes. Code is released under the [MIT License](LICENSE). Data files are subject to their original licenses (see `DATA_SOURCES.md`). Dissertation text is copyright Fangzheng Zhou.

---

**Last updated**: 2026-08-18  
**Repository version**: 1.0.0  
**Python version**: 3.8+
