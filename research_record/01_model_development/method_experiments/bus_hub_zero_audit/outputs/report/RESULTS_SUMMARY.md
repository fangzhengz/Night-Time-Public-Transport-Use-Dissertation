# Bus hub and exact-direction-zero audit

## Material Passport

- Mode: deterministic preprocessing validity audit
- Verification status: VERIFIED
- Mutation boundary: no source data, feature, label, or model was changed
- NaPTAN XML files: 490.xml

## Validation result

| metric                                        |        value |
|:----------------------------------------------|-------------:|
| n_busto_used_stops                            | 19589.000000 |
| n_stops_matched_bus_stops_csv                 | 19530.000000 |
| n_stops_matched_lsoa                          | 18451.000000 |
| pct_lsoa_stops_matched_xml_atco               |    99.311690 |
| pct_lsoa_stops_with_official_stop_area        |    99.300851 |
| pct_lsoa_stops_with_parent_stop_area          |     7.408813 |
| n_logical_hubs                                | 10667.000000 |
| n_cross_lsoa_logical_hubs                     |  1735.000000 |
| n_exact_one_direction_zero_lsoa               |    15.000000 |
| n_zero_lsoa_supported_by_hub_split            |    10.000000 |
| n_high_activity_ge_450_zero_lsoa              |     2.000000 |
| n_high_activity_ge_450_supported_by_hub_split |     2.000000 |
| max_abs_lsoa_total_reconstruction_diff        |     0.000000 |

The stop-level reconstruction exactly reproduces the current LSOA-long
direction totals within the configured numerical tolerance. The audit is
therefore evaluating the same BUSTO-to-LSOA data used by the current pipeline.

## High-activity cases

| lsoa      |   boardings |   alightings |   total_activity | supporting_hubs   |
|:----------|------------:|-------------:|-----------------:|:------------------|
| E01002735 |  7643.06084 |      0.00000 |       7643.06084 | 940GZZLUFPK       |
| E01001916 |   639.82525 |      0.00000 |        639.82525 | 940GZZLUPYB       |

| logical_hub_code   | logical_hub_name      |   n_stops |   n_lsoa | has_unmatched_stop   |   hub_boardings |   hub_alightings |
|:-------------------|:----------------------|----------:|---------:|:---------------------|----------------:|-----------------:|
| 940GZZLUFPK        | Finsbury Park Station |         6 |        2 | False                |     12553.91994 |      10085.09493 |
| 940GZZLUPYB        | Putney Bridge Station |         3 |        2 | True                 |      2077.82864 |       1371.47692 |

Both high-activity exact-zero LSOAs become bidirectional when demand is
examined across their official parent StopArea. This supports a cross-LSOA
interchange-splitting explanation rather than a literal absence of alighting.

## Operational decision

- Exclude every exact one-direction-zero LSOA from fitting the current
  two-direction temporal clustering model.
- Retain the records in maps and audit tables with an exclusion reason.
- Do not automatically exclude positive-but-imbalanced LSOAs; the
  `near_zero_ratio_lt_0_01` field is advisory only.
- Do not use Bayesian smoothing to manufacture a missing structural
  direction. Shrinkage is reserved for low-information but non-zero profiles.

## Limits

- The NaPTAN export is a 2026 snapshot, while BUSTO represents 2024/25.
- Parent StopArea coverage is concentrated at larger interchanges; many
  ordinary stop groups have only an immediate StopArea.
- The existing strict point-in-polygon lookup is audited but not repaired here.
- Hub evidence explains a zero pattern; it does not authorise moving all hub
  demand into one LSOA in the main analysis.