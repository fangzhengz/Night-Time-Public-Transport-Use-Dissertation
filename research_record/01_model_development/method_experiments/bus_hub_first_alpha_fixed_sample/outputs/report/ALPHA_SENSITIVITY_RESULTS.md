# Fixed-sample alpha=0 versus alpha=5 sensitivity

## Direct verdict

Both variants use the same 3593 hub-first LSOAs, the same
72 full-week features, and the same GMM settings. The only change is empirical
shrinkage alpha.

- alpha=0 global BIC minimum: covariance=full, K=3
- alpha=5 global BIC minimum: covariance=full, K=3
- alpha=0 versus alpha=5 full-covariance K=3 label ARI:
  0.813
- K=3 weakest matched cross-alpha cluster Jaccard:
  0.843

## Feature perturbation

|   n_lsoa |   n_features |   alpha0_rank |   alpha5_rank |   median_tv |    p95_tv |   max_tv |   pairwise_distance_correlation_500_sample |   pairwise_distance_median_abs_change |   pairwise_distance_p95_abs_change |
|---------:|-------------:|--------------:|--------------:|------------:|----------:|---------:|-------------------------------------------:|--------------------------------------:|-----------------------------------:|
|     3593 |           72 |            58 |            58 |  0.00181533 | 0.0268026 | 0.613805 |                                   0.955385 |                            0.00369384 |                          0.0259214 |

## alpha=0 BIC minima by covariance

| covariance   |   K |          BIC |   min_cluster_n |   min_cluster_share |
|:-------------|----:|-------------:|----------------:|--------------------:|
| diag         |  12 | -1.94897e+06 |              84 |         0.0233788   |
| full         |   3 | -2.06187e+06 |             494 |         0.13749     |
| spherical    |  12 | -1.65521e+06 |             164 |         0.0456443   |
| tied         |  12 | -2.01616e+06 |               2 |         0.000556638 |

## Full-covariance K diagnostics at alpha=0

|   K |          BIC |   silhouette |   davies_bouldin |   min_cluster_n |   min_cluster_share |
|----:|-------------:|-------------:|-----------------:|----------------:|--------------------:|
|   2 | -2.04011e+06 |   0.169791   |          5.89555 |            1117 |           0.310882  |
|   3 | -2.06187e+06 |   0.0757776  |          6.33647 |             494 |           0.13749   |
|   4 | -2.05276e+06 |   0.00458516 |          5.57102 |             255 |           0.0709713 |
|   5 | -2.03735e+06 |  -0.0262573  |          6.30669 |             192 |           0.0534372 |
|   6 | -2.02053e+06 |   0.00683907 |          4.31442 |             133 |           0.0370164 |
|   7 | -2.00432e+06 |  -0.030697   |          4.82508 |             108 |           0.0300584 |
|   8 | -1.98769e+06 |  -0.0333019  |          4.57669 |              75 |           0.0208739 |
|   9 | -1.96861e+06 |  -0.0264768  |          4.92293 |              84 |           0.0233788 |
|  10 | -1.95114e+06 |  -0.0373152  |          5.09211 |              78 |           0.0217089 |
|  11 | -1.93274e+06 |  -0.0375127  |          5.73132 |              69 |           0.019204  |
|  12 | -1.9125e+06  |  -0.0302228  |          4.22774 |              43 |           0.0119677 |

## Same-K alpha=0 versus alpha=5 labels

|   K |   alpha0_vs_alpha5_ARI |   mean_matched_cluster_jaccard |   min_matched_cluster_jaccard |
|----:|-----------------------:|-------------------------------:|------------------------------:|
|   2 |               0.357781 |                       0.651657 |                    0.580664   |
|   3 |               0.812934 |                       0.872101 |                    0.843284   |
|   4 |               0.720897 |                       0.771024 |                    0.648294   |
|   5 |               0.808155 |                       0.799288 |                    0.635659   |
|   6 |               0.554889 |                       0.491699 |                    0.00368324 |
|   7 |               0.602846 |                       0.548088 |                    0.331269   |
|   8 |               0.379553 |                       0.297474 |                    0.0109489  |
|   9 |               0.398671 |                       0.321084 |                    0.0142857  |
|  10 |               0.576937 |                       0.415689 |                    0.0361446  |
|  11 |               0.518164 |                       0.491793 |                    0.00361011 |
|  12 |               0.623799 |                       0.463624 |                    0.0547945  |

## Bootstrap comparison

|   K |   alpha0_bootstrap_ari_mean |   alpha0_bootstrap_ari_sd |   alpha0_bootstrap_ari_p05 |   alpha0_min_cluster_jaccard_mean |   alpha0_min_cluster_jaccard_p05 |   alpha5_bootstrap_ari_mean |   alpha5_min_cluster_jaccard_mean |
|----:|----------------------------:|--------------------------:|---------------------------:|----------------------------------:|---------------------------------:|----------------------------:|----------------------------------:|
|   2 |                    0.578055 |                 0.126198  |                   0.425768 |                         0.701493  |                       0.608116   |                    0.596535 |                         0.736077  |
|   3 |                    0.709969 |                 0.158904  |                   0.396703 |                         0.554711  |                       0.209757   |                    0.696439 |                         0.513036  |
|   4 |                    0.646103 |                 0.0507546 |                   0.563379 |                         0.403606  |                       0.285197   |                    0.537512 |                         0.28742   |
|   5 |                    0.497285 |                 0.0418275 |                   0.421864 |                         0.066013  |                       0          |                    0.572342 |                         0.212719  |
|   6 |                    0.647077 |                 0.0702423 |                   0.517947 |                         0.130761  |                       0.00581719 |                    0.500474 |                         0.0663781 |
|   7 |                    0.505502 |                 0.0568353 |                   0.446704 |                         0.0750471 |                       0          |                    0.518064 |                         0.100252  |
|   8 |                    0.395922 |                 0.032811  |                   0.342142 |                         0.0203395 |                       0          |                    0.532883 |                         0.0328299 |

## alpha=0 full K=3 recovery by cluster

|   index |   base_cluster |     mean |       std |      min |   median |      max |
|--------:|---------------:|---------:|----------:|---------:|---------:|---------:|
|       0 |              0 | 0.829671 | 0.121644  | 0.482307 | 0.864406 | 0.933124 |
|       1 |              1 | 0.554711 | 0.19769   | 0.129348 | 0.639014 | 0.80651  |
|       2 |              2 | 0.850044 | 0.0766647 | 0.566081 | 0.866762 | 0.928019 |

## Decision boundary

If K=3 and its third cluster remain similar across alpha=0 and alpha=5, the
third cluster is not created by shrinkage; its moderate bootstrap recovery must
instead be reported as an inherent boundary uncertainty. If the cross-alpha
agreement is low, K=3 cannot yet be frozen.
