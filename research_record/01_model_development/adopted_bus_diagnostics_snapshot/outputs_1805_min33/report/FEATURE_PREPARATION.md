## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Verification Status: ANALYZED
- Version Label: stoparea_min33_raw_clr_v1

# StopArea bus feature preparation

## Fixed and changed factors

- Fixed: LSOA unit, three day types, 18:00-05:00 hourly window, 33 bins per direction, min-direction threshold 33.
- Changed: upstream demand allocation now uses official child StopAreas instead of parent hub-first grouping.
- Parallel variants: direction-wise raw shares and direction-wise CLR after alpha=1 empirical-prior zero handling.

## Audit

| metric                            |                value |
|:----------------------------------|---------------------:|
| input_lsoas                       | 3797                 |
| retained_lsoas                    | 3383                 |
| excluded_lsoas                    |  414                 |
| feature_columns_per_variant       |   66                 |
| raw_share_max_boarding_sum_error  |    8.881784197e-16   |
| raw_share_max_alighting_sum_error |    8.881784197e-16   |
| clr_max_boarding_zero_sum_error   |    9.85878045867e-14 |
| clr_max_alighting_zero_sum_error  |    1.10134124043e-13 |

The raw-share and CLR matrices use exactly the same retained LSOAs and raw counts.
Input hashes are stored in `outputs/features/input_manifest.csv`.

Runtime: Python 3.13.7, pandas 2.3.3, NumPy 2.3.5.