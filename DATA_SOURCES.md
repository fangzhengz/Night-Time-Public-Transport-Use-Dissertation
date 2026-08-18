# Data Sources and Acquisition Guide

This repository does **not** include the raw input data (bus/rail transaction flows, census data), as these are large (>1.5GB) and/or subject to licensing or official access controls. This document explains how to obtain them if you need to fully replicate the project from scratch.

## Raw Data Not Included

### Bus Data (BUSTO)
- **File**: TfL iBus open data (12 quarter-hour demand files, ~53–110 MB each)
- **Source**: [TfL Unified API](https://api.tfl.gov.uk/) or [data.london.gov.uk](https://data.london.gov.uk/)
- **Timeframe**: One full week (7 day-types) covering Oct–Nov 2024
- **Variables**: Stop ID, service/route, entry/exit counts per 15-min interval
- **In this repo**: Preprocessing pipeline in `data_processing/bus_stoparea/src/`, which consumes the raw BUSTO CSVs and outputs `bus_lsoa_night_qhr_*.parquet` (12–13 MB each, used for clustering)

### Rail Data (NUMBAT)
- **File**: TfL iBus/NUMBAT database extracts (5 Excel workbooks, one per day-type)
- **Source**: TfL internal data request or [accessible datasets](https://tfl.gov.uk/info-for/open-data-users/) if available
- **Coverage**: London Underground (LU) + Docklands Light Railway (DLR) + London Overground (LOD), 403 unique stations (after Paddington NR/TfL co-location merge)
- **Variables**: Station ID, entry/exit counts per 15-min interval by day-type
- **In this repo**: Preprocessing pipeline in `data_processing/rail_allmodes/src/`, which outputs `numbat_allmodes_station_qhr_*.parquet`

### Spatial Boundaries
- **LSOA 2021 boundaries (GeoJSON)**: [Open Geography Portal](https://geoportal.statistics.gov.uk/) (ONS official)
  - Included in repo at `map/London_LSOA_2021_Boundaries.geojson` (2.8 MB)
- **NaPTAN coordinates**: National Public Transport Access Nodes dataset ([data.gov.uk](https://data.gov.uk/))
  - Not included raw; processed version used internally by the pipeline

### Socio-Economic Data (Public, Small)
- **LNWC (London Night-Time Workers Classification)**: [LNWC documentation](https://www.ucl.ac.uk/) (contact UCL Geography or see project documentation)
  - Small reference tables included in repo (e.g., `rq2_independent_variables/data/lnwc_category_labels.csv`)
- **IMD 2025 (Index of Multiple Deprivation)**: [UK Ministry of Housing website](https://www.gov.uk/government/statistics/indices-of-deprivation-2025)
  - Small reference CSVs included in repo for LSOA lookups
- **OS POI (Ordnance Survey Points of Interest)**: Proprietary; requires institutional license
  - Only the processed counts (not raw data) are included in `rq2_facility_diversity_analysis/outputs/`

## What *Is* Included

### Intermediate Processed Data (Small, Traceable)
- **Cluster labels** (K=4 for bus StopArea, K=5 for rail all-modes): CSV files in `*/outputs/data/`
- **Association test results** (LNWC, IMD, LOAC): CSV files in `rq2_*/outputs/data/`
- **Feature matrices** (z-scored contextual variables): `rq2_independent_variables/outputs/data/*_cluster_matrix_z.csv`

These are small enough (<2 MB each) to store in Git and re-run downstream analyses without regenerating from raw transaction counts.

## Replication Path

If you have legitimate access to the raw data above (or can obtain it):

1. Place raw BUSTO CSVs in a local folder accessible to the preprocessing pipeline
2. Place raw NUMBAT Excel files similarly
3. Edit the path references in:
   - `data_processing/bus_stoparea/src/config.py`
   - `data_processing/rail_allmodes/src/config.py`
4. Run the preprocessing scripts:
   ```bash
   cd data_processing/bus_stoparea && python src/01_run_pipeline.py
   cd ../rail_allmodes && python src/01_run_pipeline.py
   ```
5. This generates the intermediate `.parquet` files that feed the clustering and RQ2 analyses
6. Re-run the clustering and analysis scripts (see `README.md` in each analysis folder)

## Figures and Tables

All Chapter 4 figures and tables in the dissertation are fully reproducible from the intermediate processed data and cluster labels already in this repo, without needing raw transaction data. See `dissertation/final_figures/FIGURE_SOURCE_INVENTORY.md` for the exact data sources for each figure.

## Licensing Notes

- **TfL data**: Open data license (OGL 3.0). Requires attribution.
- **ONS spatial data**: Open Government License (OGL 3.0)
- **UCL LNWC**: Check with UCL; may require research ethics approval or data-sharing agreement
- **OS data**: Check Ordnance Survey licensing terms (not openly available)
- **Academic papers** (referenced in `参考文献/`): Standard copyright; not included in this open repository to comply with IP restrictions

## Questions?

See individual README.md files in each analysis folder for detailed method documentation and data dictionaries.
