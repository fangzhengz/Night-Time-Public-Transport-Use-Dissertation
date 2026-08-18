## Material Passport

- ID: `hub-first-core-threshold-screen-literature_mean1ph`
- Type: code experiment result
- Verification status: ANALYZED
- Created UTC: 2026-07-20T18:42:10.448713+00:00
- Scope: threshold screen with per-threshold BIC-driven K selection;
  no forced K, no posterior assignment yet

# Hub-first reliable-core threshold screen (v2: BIC picks K per threshold)

## Why this version does not fix K

The historical K=3 result comes from a pipeline this project has since
shown to be activity-noise-contaminated. Requiring K=3 to keep winning
after the contamination is removed would assume the answer. This script
instead lets BIC choose each threshold's own preferred K from an
exploratory scan (K=2..12, full covariance,
n_init=5), confirms the winning K at n_init=
20, and gates on that K. K=3 is refit and
shown alongside purely as a labelled reference point, never as a requirement.

## Fixed design

- Thresholds: [36.0]
- K scan range: 2..12
- Full-covariance GMM; scan n_init=5; deep-dive n_init=20; seed=42
- Core criterion: min(total_boardings, total_alightings) >= threshold
- Features: fixed hub-first alpha=0 direction-normalized 72-vector
- Total elapsed seconds: 59.790

**BIC-best K shift away from K=3: none: every screened threshold still has BIC-best K=3.**

## Threshold-level gate (own BIC-best K)

|   threshold |   pct_core |   bic_best_k | bic_best_k_differs_from_reference   |   bic_best_k_activity_eta2 |   bic_best_k_timing_mean_eta2 | gate_pass_at_bic_best_k   | part_of_consecutive_pass_run   | coverage_band            | strict_candidate   |   reference_k3_activity_eta2 | reference_k3_gate_pass   |
|------------:|-----------:|-------------:|:------------------------------------|---------------------------:|------------------------------:|:--------------------------|:-------------------------------|:-------------------------|:-------------------|-----------------------------:|:-------------------------|
|   36.000000 |  93.654328 |            3 | False                               |                   0.501834 |                      0.279090 | False                     | False                          | preferred_at_least_75pct | False              |                     0.501834 | False                    |

## Exploratory scan grid (all screened K, n_init=5)

Informational only -- not gating. Low n_init means individual cells can
be noisy; only the deep-dive-confirmed BIC-best K per threshold is used
for the decision above.

|   threshold |   k |   bic_within_threshold |   activity_eta2 |   timing_mean_eta2 | gate_activity_below_timing   |   min_cluster_pct | converged   |
|------------:|----:|-----------------------:|----------------:|-------------------:|:-----------------------------|------------------:|:------------|
|   36.000000 |   2 |        -1939845.278709 |        0.356345 |           0.005175 | False                        |         31.173848 | True        |
|   36.000000 |   3 |        -1949075.974494 |        0.501900 |           0.283332 | False                        |         13.967311 | True        |
|   36.000000 |   4 |        -1935647.133628 |        0.533957 |           0.296274 | False                        |          6.864785 | True        |
|   36.000000 |   5 |        -1919493.134950 |        0.569701 |           0.315508 | False                        |          4.457652 | True        |
|   36.000000 |   6 |        -1905353.633785 |        0.570708 |           0.366884 | False                        |          4.784547 | True        |
|   36.000000 |   7 |        -1888134.401524 |        0.615719 |           0.338476 | False                        |          4.457652 | True        |
|   36.000000 |   8 |        -1871938.155688 |        0.619715 |           0.358535 | False                        |          3.774146 | True        |
|   36.000000 |   9 |        -1852142.653006 |        0.568885 |           0.439262 | False                        |          2.526003 | True        |
|   36.000000 |  10 |        -1833121.798425 |        0.570644 |           0.401414 | False                        |          1.901932 | True        |
|   36.000000 |  11 |        -1815406.370674 |        0.570449 |           0.404039 | False                        |          1.396731 | True        |
|   36.000000 |  12 |        -1796379.078928 |        0.584571 |           0.426546 | False                        |          1.634473 | True        |

## Deep-dive confirmatory fits (BIC-best K and K=3 reference, n_init=20)

|   threshold |   k | is_bic_best_k   |   bic_within_threshold |   activity_eta2 |   timing_mean_eta2 |   activity_to_timing_ratio | gate_activity_below_timing   |   min_cluster_pct | converged   |   fit_seconds |
|------------:|----:|:----------------|-----------------------:|----------------:|-------------------:|---------------------------:|:-----------------------------|------------------:|:------------|--------------:|
|   36.000000 |   3 | True            |        -1949113.909883 |        0.501834 |           0.279090 |                   1.798108 | False                        |         13.699851 | True        |      6.586972 |

## Automated verdict

No threshold passed the strict gate at its own BIC-best K.

BIC values are valid for comparing K values within the same threshold
and must not be used to rank different thresholds with different samples.