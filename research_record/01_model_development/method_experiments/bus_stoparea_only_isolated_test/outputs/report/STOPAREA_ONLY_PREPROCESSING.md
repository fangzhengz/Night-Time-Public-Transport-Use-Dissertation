## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run
- Verification Status: ANALYZED
- Version Label: stoparea_only_isolated_v1

# StopArea-only preprocessing

Single changed rule: child `StopAreaCode` is the terminal grouping unit;
`ParentStopAreaRef` is ignored for grouping and coordinates.

## Summary

| metric                                       |          value |
|:---------------------------------------------|---------------:|
| n_busto_used_stops                           |   19589.000000 |
| n_stoparea_only_units                        |   12007.000000 |
| n_official_child_stopareas                   |   10768.000000 |
| n_singleton_stop_units                       |    1239.000000 |
| n_units_official_child_coordinate            |   10752.000000 |
| n_units_stop_point_fallback                  |    1196.000000 |
| n_units_missing_coordinates                  |      59.000000 |
| n_units_assigned_london_lsoa                 |   10879.000000 |
| n_units_boundary_multiple_match              |       0.000000 |
| n_lsoa_with_rows                             |    3797.000000 |
| n_lsoa_positive_activity                     |    3797.000000 |
| n_lsoa_exact_direction_zero                  |       8.000000 |
| n_stops_changed_vs_original                  |    2477.000000 |
| activity_changed_vs_original                 | 1265356.473640 |
| n_stops_changed_vs_parent_hub                |      84.000000 |
| activity_changed_vs_parent_hub               |  110193.159850 |
| n_stops_newly_included_vs_original           |       9.000000 |
| n_stops_newly_excluded_vs_original           |       9.000000 |
| max_abs_demand_conservation_diff_before_lsoa |       0.000000 |
| abs_retained_demand_diff_in_lsoa_output      |       0.000000 |

## Invariants

- The validated BUSTO-to-child-StopArea crosswalk is reused read-only.
- Stop-level boardings and alightings are conserved before London assignment.
- LSOA matching uses the same EPSG:27700 boundaries and `intersects` rule.
- Low-flow filtering, direction exclusions, feature construction and GMM do not occur here.
