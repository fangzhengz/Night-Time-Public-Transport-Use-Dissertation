# Bus child-StopArea preprocessing

## Method boundary

- Grouping unit: NaPTAN child `StopAreaRef`; missing references use singleton stops.
- `ParentStopAreaRef` is audit metadata only and is not followed.
- Coordinates: official child StopArea, then member-stop medoid fallback.
- LSOA assignment: London LSOA 2021, EPSG:27700, `intersects`.
- No clustering, Bayesian smoothing, activity filtering, or feature normalization.

## Summary

| metric                                       |        value |
|:---------------------------------------------|-------------:|
| n_busto_used_stops                           | 19579.000000 |
| n_stoparea_units                             | 11998.000000 |
| n_official_child_stopareas                   | 10768.000000 |
| n_singleton_stop_units                       |  1230.000000 |
| n_units_official_child_coordinate            | 10752.000000 |
| n_units_stop_point_fallback                  |  1187.000000 |
| n_units_missing_coordinates                  |    59.000000 |
| n_units_assigned_london_lsoa                 | 10879.000000 |
| n_units_boundary_multiple_match              |     0.000000 |
| n_lsoa_with_rows                             |  3797.000000 |
| n_lsoa_positive_activity                     |  3797.000000 |
| n_lsoa_exact_direction_zero                  |     9.000000 |
| n_stops_changed_vs_original                  |     0.000000 |
| activity_changed_vs_original                 |     0.000000 |
| n_stops_newly_included_vs_original           | 18450.000000 |
| n_stops_newly_excluded_vs_original           |     0.000000 |
| max_abs_demand_conservation_diff_before_lsoa |     0.000000 |
| abs_retained_demand_diff_in_lsoa_output      |     0.000000 |

## Conservation checks

- Maximum absolute direction difference before LSOA assignment: `4.65661287308e-10`.
- Absolute retained-demand difference in LSOA output: `0`.

## Provenance

Exact input paths, sizes and SHA-256 hashes are recorded in `../audit/input_manifest.csv`.