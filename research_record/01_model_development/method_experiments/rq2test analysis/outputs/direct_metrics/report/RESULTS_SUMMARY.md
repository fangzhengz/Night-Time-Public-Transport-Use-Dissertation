# RQ2 direct transport metrics × LNWC — provisional results

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-07-14T18:41:51.456303+00:00
- Verification Status: ANALYZED
- Version Label: rq2_direct_metrics_v1

## Design

- Bus: 4100 LSOAs, direct seven-category LNWC label.
- Rail: 254 eligible stations, seven-part catchment composition.
- Primary weighting is one LSOA/station per observation. Rail group means use fractional catchment shares.
- Centrality sensitivity controls only straight-line distance to Charing Cross.

## Bus descriptive contrasts

- `log_total_activity`: highest group 1 (7.619); lowest group 7 (5.314).
- `post_midnight_share`: highest group 1 (0.123); lowest group 7 (0.060).
- `direction_balance`: highest group 1 (0.015); lowest group 5 (-0.189).
- `weekend_ratio`: highest group 1 (0.835); lowest group 7 (0.724).

## Bus omnibus results

- `log_total_activity`: H=610.42, epsilon²=0.148, BH-adjusted p=5.284e-128.
- `post_midnight_share`: H=276.29, epsilon²=0.066, BH-adjusted p=1.305e-56.
- `direction_balance`: H=183.58, epsilon²=0.043, BH-adjusted p=5.903e-37.
- `weekend_ratio`: H=498.56, epsilon²=0.120, BH-adjusted p=3.439e-104.

## Rail fractional-composition contrasts

- `log_total_activity`: highest group 1 (10.814); lowest group 7 (8.903).
- `night_tube_extension_share`: highest group 4 (0.047); lowest group 1 (0.028).
- `direction_balance`: highest group 1 (0.156); lowest group 7 (-0.506).
- `weekend_common_ratio`: highest group 3 (0.872); lowest group 6 (0.734).

## Centrality-adjusted exploratory omnibus tests

- bus `log_total_activity`: partial R²=0.084, Freedman–Lane p=0.0010, BH-adjusted p=0.0010.
- bus `post_midnight_share`: partial R²=0.051, Freedman–Lane p=0.0010, BH-adjusted p=0.0010.
- bus `direction_balance`: partial R²=0.020, Freedman–Lane p=0.0010, BH-adjusted p=0.0010.
- bus `weekend_ratio`: partial R²=0.017, Freedman–Lane p=0.0010, BH-adjusted p=0.0010.
- rail `log_total_activity`: partial R²=0.169, Freedman–Lane p=0.0010, BH-adjusted p=0.0013.
- rail `night_tube_extension_share`: partial R²=0.077, Freedman–Lane p=0.0030, BH-adjusted p=0.0030.
- rail `direction_balance`: partial R²=0.471, Freedman–Lane p=0.0010, BH-adjusted p=0.0013.
- rail `weekend_common_ratio`: partial R²=0.156, Freedman–Lane p=0.0010, BH-adjusted p=0.0013.

## Interpretation boundary

- STATUS (2026-07-14): the centrality-adjusted partial-R^2 results below are PROVISIONAL, not a primary RQ2 result. They pool all stations/LSOAs regardless of RQ1 cluster, so they cannot say which cluster type drives the relationship -- this was judged disconnected from the actual RQ2 question and a new method is pending. Do not cite these partial-R^2 numbers as a settled finding without checking for an updated version of this analysis.
- LNWC is available only as a seven-category area typology. The analysis cannot isolate its underlying worker counts, industries or three-hour components.
- Results are area-level associations, not evidence that passengers belong to the worker groups described by an LNWC portrait.
- Distance to centre is only one confounder. Spatial autocorrelation, service supply and interchange structure are not yet modelled.
- Rail Night Tube extension reflects both use and service availability.
- Bus remains an LSOA-level analysis and cannot support stop- or route-level behavioural claims.