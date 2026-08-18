## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Origin Date: 2026-07-20T14:01:44.220643+00:00
- Verification Status: ANALYZED
- Version Label: hub_first_alpha_grid_screen_v1

# Hub-first bus K=3 alpha-grid screen

## Experiment Result

- **ID**: hub_first_bus_alpha_grid_2026-07-20
- **Type**: analysis / conditional multinomial resampling
- **Status**: completed
- **Command**: `py -3 src\run_alpha_grid_screen.py --alphas 0 5 20 50 100 200 --k 3 --covariance full --n-init 20 --seed 42 --replicates 20`
- **Working Directory**: `D:\SDS2025_workspace\CASA_FYP\FYP\rq1_bus_hub_first_alpha_grid_screen`
- **Started**: 2026-07-20T14:01:06.402474+00:00
- **Duration**: 37.8 seconds
- **Rows**: 3,593 LSOAs
- **Fixed model**: K=3, covariance=full, n_init=20, seed=42

## Reproduction gates

- Rebuilt alpha=5 features max absolute difference from saved reference: 5.551e-17
- Rebuilt alpha=5 labels ARI versus saved reference: 1.000000
- Rebuilt alpha=0 labels ARI versus saved reference: 1.000000
- Exact reference sample reproduced: True

## Screening results

|   alpha |   kw_epsilon2_log_total_activity |   eta2_log_total_activity |   timing_mean_eta2 |   timing_retention_vs_alpha5 |   resample_below450_ari_mean |   resample_below450_ari_gain_vs_alpha5 |   min_cluster_share |   median_weaker_direction_prior_weight |   pct_min_direction_reliability_lt_0_5 |   ari_vs_alpha5 | strict_screen_pass   |
|--------:|---------------------------------:|--------------------------:|-------------------:|-----------------------------:|-----------------------------:|---------------------------------------:|--------------------:|---------------------------------------:|---------------------------------------:|----------------:|:---------------------|
|       0 |                        0.591005  |                 0.522216  |           0.283973 |                     0.949923 |                     0.61772  |                              0.0260635 |           0.13749   |                              0         |                               0        |        0.812934 | False                |
|       5 |                        0.582918  |                 0.517979  |           0.298943 |                     1        |                     0.591656 |                              0         |           0.13749   |                              0.0173954 |                               0.306151 |        1        | False                |
|      20 |                        0.530036  |                 0.480058  |           0.29501  |                     0.986845 |                     0.525595 |                             -0.0660609 |           0.119677  |                              0.0661305 |                               1.47509  |        0.742123 | False                |
|      50 |                        0.28389   |                 0.276231  |           0.345851 |                     1.15691  |                     0.506785 |                             -0.0848709 |           0.0873922 |                              0.150407  |                              10.1586   |        0.416163 | False                |
|     100 |                        0.0773498 |                 0.0753476 |           0.402653 |                     1.34692  |                     0.518151 |                             -0.0735051 |           0.0943501 |                              0.261484  |                              23.1561   |        0.182325 | False                |
|     200 |                        0.0846021 |                 0.0864221 |           0.399787 |                     1.33733  |                     0.516418 |                             -0.0752387 |           0.0940718 |                              0.414566  |                              40.2449   |        0.120001 | False                |

Strict screen candidates: **None**

This is a screening result, not automatic adoption. A passing alpha may enter
a separate full K/covariance and model-bootstrap analysis. Absolute BIC values
must not be compared across alpha-transformed feature matrices.

## Pre-declared screen gates

An alpha passes only if all conditions hold:

1. activity KW epsilon-squared is at least 20% below alpha=5;
2. activity ANOVA eta-squared is below the mean eta-squared of the three timing metrics;
3. mean timing eta-squared retains at least 85% of alpha=5;
4. below-450 conditional-resampling ARI improves by at least 0.05 over alpha=5;
5. every cluster contains at least 5% of LSOAs;
6. no more than 25% of LSOAs are prior-dominated in their weaker direction
   (direction reliability below 0.5).

## Resampling interpretation

For each replicate, two independent 36-cell multinomial profiles were drawn
conditional on each LSOA's rounded observed direction total and raw direction
shares. The already fitted alpha-specific GMM then classified both profiles.
The same random count-resamples were used for every alpha. This isolates
count-driven classification repeatability; it does not include GMM refitting
uncertainty.

## Warnings and limitations

- Hub-allocation counts are fractional. Multinomial sample sizes therefore use
  rounded direction totals; the diagnostic is an approximation.
- The resampling distribution is conditional on observed shares and assumes
  multinomial variation. It does not model extra-Poisson variation, week-to-week
  change, or spatial dependence.
- Stronger alpha can mechanically move low-count profiles toward the global
  prior. Lower activity association alone is not evidence of recovered local
  information.
- The below-450 subgroup is a diagnostic band, not a transferred final cutoff.
- GMM maximum posterior is model-internal certainty and is not a count-reliability
  measure.

## Fallacy scan

- **Coverage**: 11/11 statistical fallacy types checked.

| Fallacy | Status | Current relevance |
|---|---|---|
| Simpson's paradox | NOTE | Overall and below/above-450 stability are both reported. |
| Ecological fallacy | CAUTION | LSOA labels cannot be interpreted as individual passenger behaviour. |
| Berkson/selection bias | CAUTION | The fixed sample excludes below-50 and one-direction-zero cases. |
| Collider bias | NOTE | No covariate adjustment is used in this screen. |
| Base-rate neglect | NOTE | Not a diagnostic-classification accuracy study. |
| Regression to the mean | NOTE | No extreme-group pre/post claim is made. |
| Survivorship bias | CAUTION | Exclusion rules and retained n are explicit. |
| Look-elsewhere effect | CAUTION | Six alphas are screened; gates were fixed before inspecting results. |
| Garden of forking paths | CAUTION | Fixed factors and gates are recorded in README and this report. |
| Correlation versus causation | CAUTION | Effect sizes quantify association, not causal dominance. |
| Reverse causality | NOTE | No directional causal claim is made. |
