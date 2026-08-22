## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Verification Status: VERIFIED for feature invariants and K=3 deterministic refit; ANALYZED for clustering interpretation
- Version Label: stoparea_min33_raw_share_v1

# StopArea bus clustering: raw_share

## Specification

- Sample: 3,383 LSOAs with total>=50 and both direction totals>=33.
- Features: 66 (33 boarding + 33 alighting).
- GMM scan grid: K=2..12, covariance=['spherical', 'diag', 'tied', 'full'], n_init=20, seed=42.
- Reporting covariance: full. Global BIC minimum family used directly.
- Global BIC grid minimum: covariance=full, K=3.
- Reported solution for K=[3, 4]: refitted at n_init=100 across seeds [42, 7, 123, 2026, 999], maximum-likelihood solution retained, cluster ids aligned to the scan solution. Other K keep their scan fit.
- K=3 scan refit reproducibility: exact labels=True, ARI=1.000000.

## Reported-solution refit

|   K |   n_init | seeds                   |   best_seed |      best_BIC |     worst_BIC |   BIC_range_across_seeds |   improvement_over_scan_BIC |   ari_vs_scan |      scan_BIC |
|----:|---------:|:------------------------|------------:|--------------:|--------------:|-------------------------:|----------------------------:|--------------:|--------------:|
|   3 |      100 | [42, 7, 123, 2026, 999] |           7 | -1781394.8470 | -1781317.3773 |                  77.4696 |                     79.4316 |        0.9813 | -1781315.4153 |
|   4 |      100 | [42, 7, 123, 2026, 999] |           7 | -1773672.2847 | -1772320.7947 |                1351.4900 |                   1469.7647 |        0.7744 | -1772202.5200 |

## K diagnostics

|   K |             BIC |        scan_BIC | labels_from   |   silhouette |   davies_bouldin |   activity_eta2 |   min_cluster_share |   post_midnight_share_eta2 |   deep_night_share_eta2 |   post_midnight_persistence_eta2 |   direction_balance_eta2 |   weekend_ratio_eta2 |   timing_mean_eta2 |   bootstrap_ari_mean |   bootstrap_ari_sd |   bootstrap_min_cluster_jaccard_mean |
|----:|----------------:|----------------:|:--------------|-------------:|-----------------:|----------------:|--------------------:|---------------------------:|------------------------:|---------------------------------:|-------------------------:|---------------------:|-------------------:|---------------------:|-------------------:|-------------------------------------:|
|   2 | -1768463.971590 | -1768463.971590 | scan          |     0.114478 |         3.624256 |        0.412872 |            0.428318 |                   0.327249 |                0.283124 |                         0.285571 |                 0.026332 |             0.018583 |           0.298648 |             0.693953 |           0.308237 |                             0.796046 |
|   3 | -1781394.846953 | -1781315.415320 | refit         |     0.065721 |         6.523177 |        0.496031 |            0.141590 |                   0.417165 |                0.406157 |                         0.364464 |                 0.028157 |             0.020788 |           0.395929 |             0.855824 |           0.029245 |                             0.798094 |
|   4 | -1773672.284702 | -1772202.519987 | refit         |     0.024471 |         5.764407 |        0.541078 |            0.078333 |                   0.450469 |                0.414509 |                         0.401914 |                 0.054192 |             0.036757 |           0.422297 |             0.719906 |           0.054578 |                             0.429518 |
|   5 | -1758345.545858 | -1758345.545858 | scan          |     0.021124 |         4.637052 |        0.539361 |            0.047295 |                   0.454075 |                0.434038 |                         0.416526 |                 0.071342 |             0.055944 |           0.434880 |             0.755427 |           0.020510 |                             0.151785 |
|   6 | -1743296.230246 | -1743296.230246 | scan          |     0.010170 |         4.426881 |        0.551894 |            0.034880 |                   0.516391 |                0.484879 |                         0.492750 |                 0.101994 |             0.087252 |           0.498007 |             0.711220 |           0.047558 |                             0.074312 |
|   7 | -1731895.215491 | -1731895.215491 | scan          |    -0.015375 |         5.180069 |        0.599262 |            0.029264 |                   0.481996 |                0.456100 |                         0.431617 |                 0.077400 |             0.071601 |           0.456571 |             0.514742 |           0.030241 |                             0.072593 |
|   8 | -1716741.295076 | -1716741.295076 | scan          |    -0.042444 |         5.397419 |        0.629638 |            0.026899 |                   0.525824 |                0.477530 |                         0.491006 |                 0.088845 |             0.108695 |           0.498120 |             0.478468 |           0.039959 |                             0.057083 |
|   9 | -1701008.143883 | -1701008.143883 | scan          |    -0.024997 |         4.504561 |        0.606741 |            0.023943 |                   0.538160 |                0.487988 |                         0.503207 |                 0.093991 |             0.094306 |           0.509785 |           nan        |         nan        |                           nan        |
|  10 | -1685501.351435 | -1685501.351435 | scan          |    -0.013990 |         4.569690 |        0.581365 |            0.023943 |                   0.545456 |                0.501138 |                         0.513759 |                 0.089698 |             0.129491 |           0.520118 |           nan        |         nan        |                           nan        |
|  11 | -1668501.324817 | -1668501.324817 | scan          |    -0.027656 |         4.728908 |        0.585501 |            0.027195 |                   0.507581 |                0.468928 |                         0.478887 |                 0.130753 |             0.157819 |           0.485132 |           nan        |         nan        |                           nan        |
|  12 | -1653427.710870 | -1653427.710870 | scan          |    -0.029836 |         4.426007 |        0.611941 |            0.020987 |                   0.544897 |                0.507295 |                         0.512968 |                 0.106870 |             0.197108 |           0.521720 |           nan        |         nan        |                           nan        |

## Candidate-cluster homogeneity

|        K |   cluster |           n |    share |   mean_silhouette |   relative_compactness_vs_sample |   mean_log_total_activity |   mean_post_midnight_share |
|---------:|----------:|------------:|---------:|------------------:|---------------------------------:|--------------------------:|---------------------------:|
| 3.000000 |  0.000000 |  479.000000 | 0.141590 |         -0.178918 |                         1.201247 |                  6.136978 |                   0.105847 |
| 3.000000 |  1.000000 | 1692.000000 | 0.500148 |          0.279682 |                         0.714134 |                  7.588212 |                   0.076117 |
| 3.000000 |  2.000000 | 1212.000000 | 0.358262 |         -0.136291 |                         1.215590 |                  5.809123 |                   0.031359 |
| 4.000000 |  0.000000 | 1446.000000 | 0.427431 |          0.244034 |                         0.687482 |                  7.754381 |                   0.078006 |
| 4.000000 |  1.000000 |  265.000000 | 0.078333 |         -0.202379 |                         1.282474 |                  6.196409 |                   0.121599 |
| 4.000000 |  2.000000 |  676.000000 | 0.199823 |         -0.134323 |                         1.037249 |                  6.224052 |                   0.068048 |
| 4.000000 |  3.000000 |  996.000000 | 0.294413 |         -0.126158 |                         1.205750 |                  5.780302 |                   0.026582 |

## Central-versus-outer diagnostic

|        K |   central_outer_total_variation |   central_outer_same_cluster_probability |
|---------:|--------------------------------:|-----------------------------------------:|
| 3.000000 |                        0.342628 |                                 0.338072 |
| 4.000000 |                        0.411081 |                                 0.257518 |

## Interpretation boundary

This run classifies temporal composition after StopArea-based allocation. It does not include total scale, adjacency or distance in the fitted GMM, and therefore does not establish a causal or spatial service typology by itself.