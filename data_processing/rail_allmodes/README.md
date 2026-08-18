# All-modes rail data processing

This folder is the independent entry point for converting raw NUMBAT
rail-family workbooks (LU, DLR, Overground, Elizabeth line, Tram) into a
single analysis-ready long table, restricted to stations with a NaPTAN
Greater-London coordinate match.

It deliberately does **not** decide which stations have non-zero
night-time activity, build clustering features, or fit any model -- those
remain the job of whichever downstream analysis consumes this folder's
output (currently `FYP/numbat_all_area_test/`).

Moved 2026-07-24 out of `numbat_all_area_test/src/` (where `01`/`01b` used
to live) into its own folder, mirroring how `data_processing/bus_stoparea/`
is separated from `rq1_bus_stoparea_clustering/` -- preprocessing/station-
filtering now has one home independent of any one downstream clustering
analysis, and its own audit trail (`outputs/report/RAIL_ALLMODES_PREPROCESSING.md`).

## Pipeline boundary

Inputs:

1. `FYP/地铁进出站数据/NBT24*_outputs.xlsx` — raw NUMBAT quarter-hour
   station entry/exit workbooks, one per day type (MON/TWT/FRI/SAT/SUN).
2. `FYP/地铁进出站数据/地铁车站空间数据/Underground_Stations.csv` — LU
   station coordinates (same lookup table as
   `FYP/analysis code/04_join_station_coords.py`).
3. `FYP/numbat_all_area_test/NaPTAN_data/490.xml` — official NaPTAN
   Greater-London (area 490) stop dataset, used for non-LU coordinate
   matching.

Processing rule (see `outputs/report/RAIL_ALLMODES_PREPROCESSING.md` for
the full station-count chain with current numbers):

1. `01_preprocess_rail_allmodes.py` — extract every NLC across all NUMBAT
   rail-family modes into one long table (no `has_lu` filter, unlike the
   canonical Underground-only preprocessing).
2. `01b_merge_colocated_stations.py` — sum entry/exit counts for the 14
   known co-located, cross-mode sites (e.g. each Heathrow terminal's
   Underground and Elizabeth-line sides, plus Paddington NR/TfL) into one
   physical station each.
3. `01c_match_naptan_coords.py` — match every merged station to a
   coordinate (LU stations via `Underground_Stations.csv`; others via
   NaPTAN `490.xml` RSE/TMU stop points, token-normalised name matching).
   Coordinate matching depends only on station name/mode, not on
   clustering or activity level, so it runs here, independent of any
   downstream analysis.
4. `01d_filter_naptan_matched.py` — drop stations with no NaPTAN match
   (confirmed genuinely outside Greater London, not a matching bug) and
   write the final preprocessed long table.

Outputs are written under `outputs/`:

- `data/` — intermediate artifacts from each step (raw/merged long tables,
  meta, mode lookup, coordinate match, crosswalk).
- `preprocessed/numbat_allmodes_station_qhr_all_daytypes_final.parquet` —
  the final artifact downstream analyses should read.
- `report/RAIL_ALLMODES_PREPROCESSING.md` — the full station-count chain
  and the list of excluded stations with reasons.

## Run

From `D:\SDS2025_workspace\CASA_FYP`:

```powershell
py -3 FYP\data_processing\rail_allmodes\src\01_preprocess_rail_allmodes.py
py -3 FYP\data_processing\rail_allmodes\src\01b_merge_colocated_stations.py
py -3 FYP\data_processing\rail_allmodes\src\01c_match_naptan_coords.py
py -3 FYP\data_processing\rail_allmodes\src\01d_filter_naptan_matched.py
```

## Relationship to `numbat_all_area_test`

This folder replaces the **data-generation dependency** on
`numbat_all_area_test`'s own former `01`/`01b` scripts (moved here
unmodified except for path depth) and former `05`'s coordinate-matching
half (extracted here as `01c`). `numbat_all_area_test/src/02_build_features_allmodes.py`
reads this folder's `outputs/preprocessed/numbat_allmodes_station_qhr_all_daytypes_final.parquet`
directly and applies its own independent zero-activity filter
(`MIN_TOTAL=1` on windowed night activity), arriving at the 403-station
clustering population -- this folder's 440-station output is not yet that
final population; see the preprocessing report for why the two numbers
differ and why that is expected, not an inconsistency.

An even earlier, stricter version of the NaPTAN-match filter (excluding a
further 16 stations that DO have a match but fail a stricter geometric
Greater-London-boundary test) was tried and reverted the same day it was
built -- see `numbat_all_area_test/outputs/archive_strict_extent_v1/README.md`.
