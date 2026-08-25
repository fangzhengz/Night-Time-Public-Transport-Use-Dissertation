# 01 · Data preparation

Turns the raw NUMBAT (rail) and BUSTO (bus) exports into the analysis-ready
long tables that `02_mode_specific_clustering/` builds features from. Nothing
in this stage clusters, labels, or interprets — it only cleans, matches, and
allocates.

## Rail (`rail/src/`)

Run in numeric order:

1. `01_preprocess_rail_allmodes.py` — preprocess all NUMBAT rail-family modes
   (LU, DLR, London Overground, Elizabeth line, Tram) into one long table.
2. `01b_merge_colocated_stations.py` — merge co-located, cross-mode NUMBAT
   NLCs (e.g. Heathrow's separate mode records) into single physical stations.
3. `01c_match_naptan_coords.py` — match every merged station to a NaPTAN
   coordinate.
4. `01d_filter_naptan_matched.py` — restrict to stations with a NaPTAN
   Greater-London (area 490) coordinate match; this is the final rail
   long table.

## Bus (`bus/src/`)

1. `preprocess_busto.py` — chunked read of the raw BUSTO total-demand CSVs
   (never loads all files into memory at once); produces a stop-quarter-hour
   night table.
2. `build_stoparea_data.py` — allocates stops to their NaPTAN child StopArea,
   then to LSOA, producing the canonical LSOA-quarter-hour long table.

## Output

Local, gitignored Parquet intermediates under each mode's `outputs*/`
directory. See [`docs/analysis_manifest.md`](../../docs/analysis_manifest.md)
for the exact output files and frozen row/station counts, and
[`docs/data_provenance.md`](../../docs/data_provenance.md) for the raw inputs
these scripts expect (placed under `authorised_data/`).
