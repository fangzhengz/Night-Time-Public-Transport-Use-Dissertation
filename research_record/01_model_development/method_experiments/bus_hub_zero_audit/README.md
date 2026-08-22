# RQ1 bus hub and zero-direction audit

This workspace audits whether LSOA-level bus records with an exactly zero
boarding or alighting direction are genuine directional observations or are
created by splitting the stops of one official interchange across LSOAs.

It is deliberately separate from all runnable clustering folders. It does not
refit a cluster model and does not alter the original BUSTO, stop, lookup, or
feature files.

## Inputs

- `../巴士数据/NaPTAN_data/*.xml`: official NaPTAN local-authority export(s).
- `../巴士数据/Bus_Stops.csv`: TfL stop-code to ATCO-code crosswalk and stop
  coordinates.
- `../outputs/preprocessed_busto/busto_stop_qhr_night.parquet`: stop-level
  night-time BUSTO boardings and alightings.
- `../cluster_clean_version_grouped/outputs/preprocessed/
  bus_stop_lsoa_lookup.csv`: the current LSOA21 point-in-polygon assignment.
- `../cluster_clean_version_grouped/outputs/preprocessed/
  bus_lsoa_night_long.parquet`: independent LSOA totals used for a consistency
  check.

The current LSOA21 lookup is used intentionally. An older lookup under
`outputs/preprocessed_busto/` assigns a number of stops to different LSOAs and
is not used here.

## Official hub definition

For each stop point:

1. Join `BUSTO stopcode -> Bus_Stops.STOP_CODE -> NAPTAN_ATCO`.
2. Join `NAPTAN_ATCO -> NaPTAN StopAreaRef`.
3. If the StopArea has a `ParentStopAreaRef`, use the parent as the logical hub.
4. Otherwise use the immediate StopArea as the logical hub.

This hierarchy is used only to audit cross-boundary splitting. It does not
move demand between LSOAs or force all similarly named stops into one area.

## Run

```powershell
python src/run_hub_zero_audit.py
```

## Main outputs

- `outputs/data/input_manifest.csv`: file hashes, sizes, versions and rows.
- `outputs/data/stop_hub_crosswalk.csv`: stop-to-StopArea/parent-hub/LSOA
  crosswalk with directional totals.
- `outputs/data/logical_hub_summary.csv`: official hub totals and cross-LSOA
  flags.
- `outputs/data/hub_lsoa_direction_summary.csv`: demand split by hub and LSOA.
- `outputs/data/lsoa_direction_zero_audit.csv`: every exact one-direction-zero
  LSOA and whether official hub evidence supports a boundary split.
- `outputs/data/lsoa_clustering_eligibility.csv`: deterministic exclusion flag
  for the two-direction clustering input; near-zero imbalance is flagged but
  not automatically excluded.
- `outputs/data/audit_summary.csv`: key counts and consistency checks.
- `outputs/report/RESULTS_SUMMARY.md`: human-readable findings and limits.

## Decision boundary

- Exact zero in either direction: excluded from the two-direction clustering
  fit, retained in the audit and map outputs.
- Both directions positive but highly imbalanced: retained, with an advisory
  flag for sensitivity analysis.
- Bayesian shrinkage is not applied here. It belongs downstream and only to
  non-structural, non-zero low-information profiles.
