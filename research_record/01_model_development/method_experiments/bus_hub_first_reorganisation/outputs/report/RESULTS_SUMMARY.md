# Bus hub-first spatial reorganisation

## Material Passport

- Mode: deterministic preprocessing reconstruction
- Verification status: VERIFIED
- Rail passenger data used: no
- Rail/Underground parent coordinates used: no
- Representative points: official child BUS StopArea medoids
- Existing clustering inputs or labels modified: no

## Summary

| metric                                               |          value |
|:-----------------------------------------------------|---------------:|
| n_busto_used_stops                                   |   19589.000000 |
| n_logical_hubs                                       |   11906.000000 |
| n_parent_identifier_hubs                             |     510.000000 |
| n_hubs_official_bus_area_coordinates                 |   10655.000000 |
| n_hubs_stop_point_coordinate_fallback                |    1192.000000 |
| n_hubs_missing_coordinates                           |      59.000000 |
| activity_missing_coordinates                         |   25565.802010 |
| n_missing_coordinate_stops_without_naptan_atco       |      59.000000 |
| n_hubs_assigned_london_lsoa                          |   10778.000000 |
| n_hubs_boundary_multiple_match                       |       0.000000 |
| n_stop_points_boundary_multiple_match                |       0.000000 |
| n_stops_moved_between_lsoa                           |    2538.000000 |
| n_stops_old_lookup_diff_from_direct_point            |       0.000000 |
| activity_old_lookup_diff_from_direct_point           |       0.000000 |
| n_stops_changed_by_hub_rule                          |    2538.000000 |
| activity_changed_by_hub_rule                         | 1345755.716220 |
| n_stops_newly_included                               |       9.000000 |
| n_stops_newly_excluded                               |       9.000000 |
| current_retained_activity                            | 6926543.539720 |
| hub_first_retained_activity                          | 6930047.306560 |
| activity_moved_between_lsoa                          | 1345755.716220 |
| pct_current_activity_moved_between_lsoa              |      19.428965 |
| activity_newly_included                              |    4409.440370 |
| activity_newly_excluded                              |     905.673530 |
| n_lsoa_current                                       |    4111.000000 |
| n_lsoa_hub_first                                     |    3790.000000 |
| n_exact_direction_zero_lsoa_current                  |      15.000000 |
| n_exact_direction_zero_lsoa_hub_first                |       7.000000 |
| n_near_zero_positive_lsoa_hub_first                  |       3.000000 |
| n_exact_direction_zero_lsoa_weekday                  |      11.000000 |
| n_exact_direction_zero_lsoa_weekend                  |      11.000000 |
| n_unique_one_direction_exception_lsoas               |      14.000000 |
| n_one_direction_exceptions_meeting_min_total_weekday |       1.000000 |
| n_one_direction_exceptions_meeting_min_total_weekend |       2.000000 |
| n_zero_activity_source_stops                         |      96.000000 |
| n_zero_activity_logical_hubs                         |      64.000000 |
| max_abs_demand_conservation_diff_before_lsoa         |       0.000000 |
| abs_retained_demand_diff_in_lsoa_output              |       0.000000 |

## Why LSOA assignments changed

| dimension          | category                       |   n_stops |   n_hubs |   n_stops_changed_lsoa |   total_activity |   activity_changed_lsoa |   pct_activity_changed_within_category |
|:-------------------|:-------------------------------|----------:|---------:|-----------------------:|-----------------:|------------------------:|---------------------------------------:|
| logical_hub_source | official_bus_stop_area         |     16980 |    10161 |                   2173 |    5314304.73220 |            856161.48319 |                               16.11051 |
| logical_hub_source | parent_stop_area_identifier    |      1370 |      510 |                    365 |    1605189.35470 |            489594.23303 |                               30.50072 |
| logical_hub_source | singleton_bus_stop_fallback    |      1239 |     1239 |                      0 |     112725.31098 |                 0.00000 |                                0.00000 |
| coordinate_source  | bus_stop_point_medoid_fallback |      1204 |     1192 |                      1 |     128352.02029 |               434.15038 |                                0.33825 |
| coordinate_source  | missing                        |        59 |       59 |                      0 |      25565.80201 |                 0.00000 |                                0.00000 |
| coordinate_source  | official_bus_stop_area         |     17992 |    10575 |                   2409 |    6384898.77794 |           1170647.69520 |                               18.33463 |
| coordinate_source  | official_bus_stop_area_medoid  |       334 |       80 |                    128 |     493402.79764 |            174673.87064 |                               35.40188 |

The independent direct-point audit reproduces every comparable old LSOA
assignment. The reported changes therefore arise from the new hub rule, not
from a CRS mismatch or an accidental change of LSOA geography.

## One-direction exception areas

- Definition: after hub-to-LSOA aggregation, boardings or alightings equal
  exactly zero within the relevant weekday/weekend analysis group.
- Treatment: retained in the complete spatial dataset and reported separately,
  but ineligible for the core two-direction temporal clustering.
- This rule is evaluated before clustering and independently of the minimum
  activity threshold. The complete exception register is
  `outputs/data/one_direction_exception_areas.csv`.

## Core interchange assignments

| logical_hub_code   | logical_hub_name      |   n_member_stops |   n_member_stop_areas | representative_candidate_code   |   hub_easting |   hub_northing | hub_lsoa   | coordinate_source             |
|:-------------------|:----------------------|-----------------:|----------------------:|:--------------------------------|--------------:|---------------:|:-----------|:------------------------------|
| 940GZZLUFPK        | Finsbury Park Station |                6 |                     4 | 490G00083S                      |    531288.000 |     186805.000 | E01002734  | official_bus_stop_area_medoid |
| 940GZZLUPYB        | Putney Bridge Station |                3 |                     2 | 490G00184X                      |    524462.000 |     175876.000 | E01001916  | official_bus_stop_area_medoid |

| logical_hub_code   | logical_hub_name      | hub_lsoa   |   boardings |   alightings |
|:-------------------|:----------------------|:-----------|------------:|-------------:|
| 940GZZLUFPK        | Finsbury Park Station | E01002734  | 12553.91994 |  10085.09493 |
| 940GZZLUPYB        | Putney Bridge Station | E01001916  |  2077.82864 |   1371.47692 |

## Validity statements

- Stop-level BUSTO demand is exactly conserved when stops are grouped into hubs.
- Every parent code is used only as a grouping identifier. Hub locations come
  from member bus StopArea points or, when necessary, bus-stop point fallbacks.
- The LSOA assignment uses a point/polygon intersects relation so boundary
  points are not silently discarded. Multiple boundary matches are flagged.
- Exact one-direction-zero profiles are retained in the complete spatial data
  but explicitly flagged both overall and for the weekday/weekend analysis groups.
- The generated LSOA-long parquet is schema-compatible with the existing bus
  feature-building stage but has not yet been clustered.

## Remaining limits

- NaPTAN is a 2026 snapshot while BUSTO represents 2024/25.
- BUSTO stops listed in `unresolved_coordinate_stops.csv` have no matching
  record or NaPTAN ATCO reference in Bus_Stops.csv; they are preserved in
  the all-hub output but cannot be assigned to London without a defensible
  crosswalk. They are not silently guessed from names.
- Assigning a complete cross-boundary hub to one LSOA is a deliberate functional
  node decision; the exact moved activity is reported for sensitivity analysis.
- This spatial repair does not remove uncertainty in inferred BUSTO alightings
  or low-volume temporal profiles.