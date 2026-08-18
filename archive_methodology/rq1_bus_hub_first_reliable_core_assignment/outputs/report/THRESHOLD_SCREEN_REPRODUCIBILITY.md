## Material Passport

- ID: `hub-first-core-threshold-screen-reproducibility`
- Type: code experiment result
- Verification status: ANALYZED
- Created UTC: 2026-07-20T15:59:58.778441+00:00
- Scope: threshold screen only; no final K selection or posterior assignment

# Hub-first reliable-core threshold screen

## Fixed design

- Thresholds: [100.0]
- K values: [3]
- Full-covariance GMM; n_init=5; seed=42
- Core criterion: min(total_boardings, total_alightings) >= threshold
- Features: fixed hub-first alpha=0 direction-normalized 72-vector
- Total elapsed seconds: 3.448

## Threshold-level gate

|   threshold |   n_core |   pct_core |   n_k_activity_below_timing | all_k_activity_below_timing   | part_of_consecutive_all_k_run   | coverage_band            | strict_first_pass_candidate   |   max_activity_eta2_across_k |   min_timing_mean_eta2_across_k |   max_activity_kw_epsilon2_across_k |   min_cluster_size_across_k |
|------------:|---------:|-----------:|----------------------------:|:------------------------------|:--------------------------------|:-------------------------|:------------------------------|-----------------------------:|--------------------------------:|------------------------------------:|----------------------------:|
|  100.000000 |     2761 |  76.843863 |                           1 | True                          | False                           | preferred_at_least_75pct | False                         |                     0.078477 |                        0.267426 |                            0.085159 |                         289 |

## K-specific results

|   threshold |   k |   n_core |   pct_core |   activity_eta2 |   timing_mean_eta2 |   activity_to_timing_ratio |   activity_kw_epsilon2 | gate_activity_below_timing   |   min_cluster_size | converged   |   fit_seconds |   bic_within_threshold |
|------------:|----:|---------:|-----------:|----------------:|-------------------:|---------------------------:|-----------------------:|:-----------------------------|-------------------:|:------------|--------------:|-----------------------:|
|  100.000000 |   3 |     2761 |  76.843863 |        0.078477 |           0.267426 |                   0.293452 |               0.085159 | True                         |                289 | True        |      3.330916 |        -1608092.101477 |

## Automated first-pass verdict

No threshold passed the strict first-pass gate.

The automated verdict is only a screening gate. BIC values are valid
for comparing K values within the same threshold and must not be used
to rank different thresholds with different samples.