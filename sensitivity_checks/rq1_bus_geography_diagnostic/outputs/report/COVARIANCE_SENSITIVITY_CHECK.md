# Quick check: does diag covariance fix the full-covariance instability?

Same X_bus.parquet, same fit() settings as the adopted pipeline (`cluster_clean_version_fullweek/src/04_cluster.py`); only covariance_type changed to 'diag'.

## 1. Does diag also collapse to the K-range ceiling? (spherical/diag/tied all previously hit K=12 (Codex audit, full covariance was the only exception at K=3))

|   K |          BIC |
|----:|-------------:|
|   2 | -1.99917e+06 |
|   3 | -2.0753e+06  |
|   4 | -2.10459e+06 |
|   5 | -2.12673e+06 |
|   6 | -2.14117e+06 |
|   7 | -2.14828e+06 |
|   8 | -2.15963e+06 |
|   9 | -2.16181e+06 |
|  10 | -2.16732e+06 |
|  11 | -2.17325e+06 |
|  12 | -2.17699e+06 |

BIC-best K for diag covariance: **12**.

## 2. Geography and activity-dominance at diag's BIC-best K and at K=3

|   K | is_bic_best_for_diag   |   n_units |   geo_eta2_distance |   activity_eta2_log_total |
|----:|:-----------------------|----------:|--------------------:|--------------------------:|
|   3 | False                  |      4100 |           0.0758649 |                  0.332094 |
|  12 | True                   |      4100 |           0.185659  |                  0.61622  |

Compare against the full-covariance adopted solution (`../rq1_bus_geography_diagnostic/outputs/data/bus_distance_eta2_by_k.csv`: K=3 geo eta2=0.049) and the metric~cluster result (`../rq1_context_metrics_analysis/outputs/data/bus_cluster_metric_significance.csv`: K=3 full-cov activity epsilon2=0.518).

## 3. Cheap threshold-robustness (single refit, no bootstrap -- indicative only)

|   K |   threshold |   n_kept |   ari_vs_full_data_labels |
|----:|------------:|---------:|--------------------------:|
|   3 |          50 |     3890 |                  0.694379 |
|   3 |         250 |     3072 |                  0.383543 |
|  12 |          50 |     3890 |                  0.545824 |
|  12 |         250 |     3072 |                  0.538829 |

## Reading

- If diag's BIC-best K is still at the range ceiling, or activity_eta2 stays as high as full covariance's 0.518, diag alone does not fix the problem -- the issue is more likely the feature space itself (per-direction share normalisation on sparse/low-activity units), and Codex's coverage-tier design is probably necessary, not just a covariance-type swap.
- If diag gives a sensible (non-ceiling) K with meaningfully lower activity_eta2 and higher threshold-robustness ARI than full covariance's 0.535/0.092 at thresholds 50/500, that is a cheap, promising direction worth a fuller (but still scoped) sensitivity grid.