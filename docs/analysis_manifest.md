# Analysis manifest

This is the authoritative crosswalk between the submitted dissertation and the active repository path.

## Rail usage typology

| Step | Code | Main output | Frozen check |
|---|---|---|---|
| NUMBAT extraction and harmonisation | `analysis/01_data_preparation/rail/src/01_preprocess_rail_allmodes.py` | final station-quarter-hour long table (local, Parquet) | 471 raw NLC units |
| Co-location merge and spatial match | `01b_merge_colocated_stations.py`, `01c_match_naptan_coords.py`, `01d_filter_naptan_matched.py` | final matched long table and coordinates | 456 merged sites; 440 NaPTAN-matched |
| Feature construction | `analysis/02_mode_specific_clustering/rail/src/02_build_features_allmodes.py` | 440-dimensional direction/day/time composition | 403 active stations |
| Model fit | `03_cluster_allmodes.py`, `03b_full_covariance_grid_check.py` | K labels and BIC grid | diagonal GMM K=5 |
| Selection and uncertainty | `08_k_selection_panel.py`, `10_posterior_membership_summary.py` | `results/diagnostics/rail/model_selection.csv` | BIC -1,900,159.516; seed ARI 0.964; bootstrap ARI 0.510 |
| Cluster interpretation | `09_cluster_names.py` | `rail_cluster_names.csv` | cluster sizes 89, 26, 90, 31, 167 |

## Bus usage typology

| Step | Code | Main output | Frozen check |
|---|---|---|---|
| Chunked BUSTO extraction | `analysis/01_data_preparation/bus/src/preprocess_busto.py` | stop-quarter-hour night table (local, Parquet) | 18:00–05:00; 1,873,645 rows; 19,579 stops |
| StopArea and LSOA allocation | `build_stoparea_data.py` | LSOA-quarter-hour long table (local, Parquet) | conservation checks pass |
| CLR feature construction | `analysis/02_mode_specific_clustering/bus/src/01_prepare_features.py` | 66-dimensional CLR matrix (local, Parquet) | both directions >=33; 3,383 retained LSOAs |
| Model fit and uncertainty | `02_run_clustering.py`, `07_posterior_membership.py`, `08_seed_agreement.py` | labels and diagnostics | full-covariance GMM K=4 |
| Cluster interpretation | `06_cluster_names.py` | `bus_cluster_names.csv` | cluster sizes 604, 1,134, 1,069, 576 |

## Behavioural descriptors

`analysis/03_lnwc_context/src/run_context_metrics.py` joins fixed cluster labels to post-clustering descriptors; it does not refit either clustering. The formal Bus descriptor set contains five items: log total activity, directional balance, post-23:00 share, post-midnight persistence and weekend-to-weekday ratio. The formal Rail set contains log total activity, directional balance, post-23:00 share and weekend common-window ratio.

The raw cluster means, their z-score standardisations and the Kruskal–Wallis tests are distinct outputs. See [`metric_dictionary.md`](metric_dictionary.md).

## LNWC context

| Mode | Estimand | Code | Main statistical output |
|---|---|---|---|
| Rail | seven-part LNWC composition within 800m Voronoi-clipped catchments, equal weight per distinct intersecting LSOA | `analysis/03_lnwc_context/src/run_lnwc_analysis.py` | permutation R²=0.262920, p=0.001, n=389, 999 permutations |
| Bus | dominant LNWC group for each fitted LSOA | same | chi-square=647.497, df=18, Cramer's V=0.252585, n=3,383 |

The complete machine-readable result, including the Rail R² and permutation p-value, is [`results/tables/lnwc_association_full.csv`](../results/tables/lnwc_association_full.csv).

## Twenty-variable area context

`analysis/04_urban_context/src/01_build_variable_table.py` builds mode-specific contextual panels. `02_run_association_tests.py` runs Kruskal–Wallis tests with epsilon-squared and mode-wise Benjamini–Hochberg correction. `03_per_cluster_tests.py` runs cluster-versus-rest Mann–Whitney tests and reports rank-biserial correlations. `04_build_figures.py` and `06_build_cluster_panels.py` produce the rankings and profiles.

- Omnibus tests: [`results/tables/context_omnibus_tests.csv`](../results/tables/context_omnibus_tests.csv)
- Cluster-versus-rest tests: [`results/tables/context_cluster_vs_rest_tests.csv`](../results/tables/context_cluster_vs_rest_tests.csv)
- Full profile matrices: `results/tables/*_context_cluster_z.csv`

## Figure crosswalk

Reader-facing files use descriptive names so that the analytical meaning is independent of manuscript pagination or section numbering. `results/figures/` contains byte-identical copies of the submitted figures from `paper/source/figures/`. Rebuilt outputs are kept separately in `results/recomputed_figures/`: the reporting script first writes local build products to `results/generated_figures/`, and `scripts/publish_results.py` then promotes adopted rebuilds without overwriting the submitted presentation layer. `results/manifest.csv` records the rebuild sources and hashes.
