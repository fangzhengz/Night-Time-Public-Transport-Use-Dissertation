## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Verification Status: VERIFIED for feature invariants and K=3 deterministic refit; ANALYZED for clustering interpretation
- Version Label: stoparea_min33_clr_v1

# StopArea bus clustering: clr

## Specification

- Sample: 3,383 LSOAs with total>=50 and both direction totals>=33.
- Features: 66 (33 boarding + 33 alighting).
- GMM scan grid: K=2..12, covariance=['spherical', 'diag', 'tied', 'full'], n_init=20, seed=42.
- Reporting covariance: full. Global BIC minimum family used directly.
- Global BIC grid minimum: covariance=full, K=4.
- Reported solution for K=[3, 4]: refitted at n_init=100 across seeds [42, 7, 123, 2026, 999], maximum-likelihood solution retained, cluster ids aligned to the scan solution. Other K keep their scan fit.
- K=3 scan refit reproducibility: exact labels=True, ARI=1.000000.

## Reported-solution refit

|   K |   n_init | seeds                   |   best_seed |     best_BIC |    worst_BIC |   BIC_range_across_seeds |   improvement_over_scan_BIC |   ari_vs_scan |     scan_BIC |
|----:|---------:|:------------------------|------------:|-------------:|-------------:|-------------------------:|----------------------------:|--------------:|-------------:|
|   3 |      100 | [42, 7, 123, 2026, 999] |          42 | -351975.1569 | -351975.1569 |                   0.0000 |                      0.0000 |        1.0000 | -351975.1569 |
|   4 |      100 | [42, 7, 123, 2026, 999] |           7 | -365890.1204 | -365890.1204 |                   0.0000 |                      0.0000 |        1.0000 | -365890.1204 |

## K diagnostics

|   K |            BIC |       scan_BIC | labels_from   |   silhouette |   davies_bouldin |   activity_eta2 |   min_cluster_share |   post_midnight_share_eta2 |   deep_night_share_eta2 |   post_midnight_persistence_eta2 |   direction_balance_eta2 |   weekend_ratio_eta2 |   timing_mean_eta2 |   bootstrap_ari_mean |   bootstrap_ari_sd |   bootstrap_min_cluster_jaccard_mean |
|----:|---------------:|---------------:|:--------------|-------------:|-----------------:|----------------:|--------------------:|---------------------------:|------------------------:|---------------------------------:|-------------------------:|---------------------:|-------------------:|---------------------:|-------------------:|-------------------------------------:|
|   2 | -248314.960908 | -248314.960908 | scan          |     0.271699 |         1.290215 |        0.519236 |            0.417677 |                   0.237065 |                0.168999 |                         0.211889 |                 0.041105 |             0.029727 |           0.205984 |             0.363195 |           0.180575 |                             0.647964 |
|   3 | -351975.156852 | -351975.156852 | refit         |     0.205939 |         1.845406 |        0.561643 |            0.283181 |                   0.390302 |                0.323956 |                         0.334672 |                 0.050558 |             0.040779 |           0.349643 |             0.844294 |           0.070486 |                             0.858037 |
|   4 | -365890.120356 | -365890.120355 | refit         |     0.164609 |         2.314568 |        0.576461 |            0.170263 |                   0.417456 |                0.329643 |                         0.356802 |                 0.054169 |             0.044417 |           0.367967 |             0.785321 |           0.019845 |                             0.315606 |
|   5 | -353265.417057 | -353265.417057 | scan          |     0.159586 |         2.353072 |        0.578769 |            0.059710 |                   0.424086 |                0.342078 |                         0.361704 |                 0.052870 |             0.044272 |           0.375956 |             0.758957 |           0.118556 |                             0.251427 |
|   6 | -349384.203139 | -349384.203139 | scan          |     0.148602 |         2.594666 |        0.586588 |            0.028673 |                   0.424961 |                0.339531 |                         0.362132 |                 0.056500 |             0.044190 |           0.375541 |             0.726946 |           0.075190 |                             0.017520 |
|   7 | -338101.417197 | -338101.417197 | scan          |     0.075708 |         3.018964 |        0.626720 |            0.027490 |                   0.434322 |                0.350334 |                         0.373257 |                 0.061519 |             0.044972 |           0.385971 |             0.634181 |           0.045619 |                             0.036739 |
|   8 | -335491.803000 | -335491.803000 | scan          |     0.073941 |         2.874006 |        0.629985 |            0.019805 |                   0.438176 |                0.361272 |                         0.375776 |                 0.063613 |             0.046810 |           0.391742 |             0.638571 |           0.044942 |                             0.053166 |
|   9 | -323801.927635 | -323801.927635 | scan          |     0.080366 |         3.255242 |        0.650414 |            0.012119 |                   0.431314 |                0.360014 |                         0.370429 |                 0.063628 |             0.046244 |           0.387252 |           nan        |         nan        |                           nan        |
|  10 | -308446.454829 | -308446.454829 | scan          |     0.055517 |         3.060451 |        0.646149 |            0.010346 |                   0.440083 |                0.368023 |                         0.377195 |                 0.066260 |             0.048803 |           0.395100 |           nan        |         nan        |                           nan        |
|  11 | -290946.154262 | -290946.154262 | scan          |     0.057159 |         3.051835 |        0.641087 |            0.011528 |                   0.446051 |                0.372380 |                         0.384092 |                 0.071444 |             0.050146 |           0.400841 |           nan        |         nan        |                           nan        |
|  12 | -279265.723289 | -279265.723289 | scan          |     0.067657 |         2.779012 |        0.640187 |            0.010346 |                   0.475740 |                0.409590 |                         0.412369 |                 0.084523 |             0.053720 |           0.432566 |           nan        |         nan        |                           nan        |

## Candidate-cluster homogeneity

|        K |   cluster |           n |    share |   mean_silhouette |   relative_compactness_vs_sample |   mean_log_total_activity |   mean_post_midnight_share |
|---------:|----------:|------------:|---------:|------------------:|---------------------------------:|--------------------------:|---------------------------:|
| 3.000000 |  0.000000 | 1277.000000 | 0.377476 |         -0.238989 |                         0.985891 |                  6.379405 |                   0.067164 |
| 3.000000 |  1.000000 | 1148.000000 | 0.339344 |          0.559390 |                         0.367280 |                  7.960534 |                   0.092130 |
| 3.000000 |  2.000000 |  958.000000 | 0.283181 |          0.375470 |                         0.727786 |                  5.776963 |                   0.027103 |
| 4.000000 |  0.000000 |  604.000000 | 0.178540 |          0.265276 |                         0.633991 |                  5.568400 |                   0.021396 |
| 4.000000 |  1.000000 | 1134.000000 | 0.335205 |          0.495782 |                         0.365844 |                  7.972135 |                   0.092419 |
| 4.000000 |  2.000000 | 1069.000000 | 0.315992 |         -0.197304 |                         0.866905 |                  6.396761 |                   0.071352 |
| 4.000000 |  3.000000 |  576.000000 | 0.170263 |          0.078724 |                         0.794971 |                  6.211235 |                   0.040791 |

## Central-versus-outer diagnostic

|        K |   central_outer_total_variation |   central_outer_same_cluster_probability |
|---------:|--------------------------------:|-----------------------------------------:|
| 3.000000 |                        0.356880 |                                 0.355057 |
| 4.000000 |                        0.356880 |                                 0.345034 |

## Interpretation boundary

This run classifies temporal composition after StopArea-based allocation. It does not include total scale, adjacency or distance in the fitted GMM, and therefore does not establish a causal or spatial service typology by itself.