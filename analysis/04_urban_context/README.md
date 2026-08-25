# 04 · Urban context (20-variable analysis)

The second contextual lens alongside LNWC: tests whether the Rail and Bus
clusters differ on 20 independent socio-economic and built-environment
variables (deprivation domains, age structure, tenure, car access, industry
mix, OS POI facility count/diversity, etc.), again by joining fixed cluster
labels rather than refitting.

## Scripts (`src/`)

1. `00_download_census.py` — optional, run once: pulls the Census/Nomis
   tables this folder needs into `data/`; later steps pick up whatever is
   present and skip cleanly if a table is missing.
2. `01_build_variable_table.py` — builds the LSOA variable table and attaches
   it to both clusterings. Its `attach_facilities()` step spatially joins the
   licensed OS Points of Interest layer (`data/raw/os_poi/poi_6438516.gpkg`,
   path set in `config.py`) to every London LSOA and derives the two POI
   variables that enter the formal 20-variable set:
   - `log1p_poi_count` — total POI count per LSOA (mean across intersecting
     LSOAs for the Rail catchments), log1p-transformed for skew;
   - `shannon_group` — unnormalised Shannon diversity of those POIs across
     the nine top-level OS POI Groups, i.e. facility-type mix rather than
     sheer count.

   These two were added to the variable set on 2026-08-07; see the
   `RE-ADDED 2026-08-08` note near the top of `config.py` for the full
   decision history. They supersede the earlier, standalone facility-diversity
   trial preserved for reference in
   [`research_record/02_context_alternatives/facility_diversity/`](../../research_record/02_context_alternatives/facility_diversity/) —
   that folder is a superseded exploratory version, not an alternative
   currently in use.
3. `02_run_association_tests.py` — omnibus Kruskal–Wallis + epsilon-squared
   per variable per mode, Benjamini–Hochberg corrected within each mode.
4. `03_per_cluster_tests.py` — the companion cluster-versus-rest test: which
   cluster is high or low on which variable (Mann–Whitney, rank-biserial
   correlation).
5. `04_build_figures.py` — cluster profile heatmap, boxplots, correlation
   matrix.
6. `06_build_cluster_panels.py` — the integrated per-cluster figure (temporal
   curve + spatial map + context profile in one row).
7. `config.py`, `geo_utils.py` — shared configuration and the Voronoi/geometry
   helper used by the Rail catchment construction.

## Data (`data/`)

Cached per-LSOA Census/administrative tables (TS003, TS007b, TS011, TS021,
TS045, TS054, TS060, TS066, BRES) fetched by `00_download_census.py`.

## Output

`results/tables/context_omnibus_tests.csv`,
`results/tables/context_cluster_vs_rest_tests.csv`, and the per-mode
`*_context_cluster_z.csv` profile matrices. See
[`docs/analysis_manifest.md`](../../docs/analysis_manifest.md) for the full
crosswalk.
