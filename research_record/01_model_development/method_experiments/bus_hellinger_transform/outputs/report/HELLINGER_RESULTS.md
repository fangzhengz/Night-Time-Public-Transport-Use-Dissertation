## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Verification Status: ANALYZED
- Version Label: bus_hellinger_transform_v1

# Hellinger-transformed bus clustering: results

## Fixed design

- n=3,365 LSOAs; exact official hub-first raw-share sample.
- Two independent 36-cell direction compositions; transform `sqrt(p)`.
- Exact zeros preserved; no pseudo-count or alpha shrinkage.
- GMM covariance grid=['spherical', 'diag', 'tied', 'full']; K=2..12; n_init=20; seed=42.
- Bootstrap K=2..8; 20 replicates; bootstrap n_init=3.
- Absolute BIC is used only within the Hellinger feature space.

## BIC minima by covariance

| covariance   |   K |           BIC |   min_cluster_n |   min_cluster_share |
|:-------------|----:|--------------:|----------------:|--------------------:|
| diag         |  12 | -1224037.4553 |             188 |              0.0559 |
| full         |   3 | -1435704.1802 |             920 |              0.2734 |
| spherical    |  12 | -1061068.2484 |             185 |              0.0550 |
| tied         |  12 | -1377916.9253 |              35 |              0.0104 |

Global BIC family retained; no degeneracy override.

Reporting covariance family: **full**.

## K diagnostics

|       K |           BIC |   silhouette |   davies_bouldin |   zero_bin_eta2 |   activity_eta2 |   timing_mean_eta2 |   min_cluster_share |   bootstrap_ari_mean |   bootstrap_min_cluster_jaccard_mean |
|--------:|--------------:|-------------:|-----------------:|----------------:|----------------:|-------------------:|--------------------:|---------------------:|-------------------------------------:|
|  2.0000 | -1426516.2283 |       0.1985 |           2.0022 |          0.8499 |          0.2727 |             0.1551 |              0.3477 |               0.9867 |                               0.9905 |
|  3.0000 | -1435704.1802 |       0.0861 |           4.5606 |          0.8590 |          0.5619 |             0.1702 |              0.2734 |               0.8724 |                               0.8541 |
|  4.0000 | -1422183.0188 |       0.0516 |           4.8054 |          0.8503 |          0.6068 |             0.1617 |              0.0633 |               0.8172 |                               0.3851 |
|  5.0000 | -1426062.5839 |       0.0166 |           6.8175 |          0.9118 |          0.6363 |             0.2326 |              0.1034 |               0.6319 |                               0.3009 |
|  6.0000 | -1405273.2202 |       0.0310 |           4.5984 |          0.9085 |          0.6078 |             0.2169 |              0.0187 |               0.6318 |                               0.0424 |
|  7.0000 | -1387851.6718 |       0.0017 |           5.2985 |          0.9068 |          0.6805 |             0.2772 |              0.0360 |               0.4645 |                               0.0816 |
|  8.0000 | -1369220.6906 |       0.0197 |           3.7377 |          0.9068 |          0.6154 |             0.3431 |              0.0276 |               0.5534 |                               0.0539 |
|  9.0000 | -1357478.5193 |       0.0147 |           4.0769 |          0.9220 |          0.6247 |             0.3553 |              0.0306 |             nan      |                             nan      |
| 10.0000 | -1337554.2889 |       0.0007 |           4.0220 |          0.9209 |          0.6150 |             0.4305 |              0.0187 |             nan      |                             nan      |
| 11.0000 | -1323319.5730 |       0.0022 |           3.6364 |          0.9153 |          0.6467 |             0.4455 |              0.0149 |             nan      |                             nan      |
| 12.0000 | -1300595.6361 |       0.0019 |           3.5631 |          0.9077 |          0.6446 |             0.4583 |              0.0140 |             nan      |                             nan      |

## Pre-declared selection screen

|   K |           BIC |   min_cluster_share |   bootstrap_ari_mean |   bootstrap_min_cluster_jaccard_mean | size_pass   | stability_pass   | jaccard_pass   | structural_screen_pass   | selected   |
|----:|--------------:|--------------------:|---------------------:|-------------------------------------:|:------------|:-----------------|:---------------|:-------------------------|:-----------|
|   2 | -1426516.2283 |              0.3477 |               0.9867 |                               0.9905 | True        | True             | True           | True                     | False      |
|   3 | -1435704.1802 |              0.2734 |               0.8724 |                               0.8541 | True        | True             | True           | True                     | True       |
|   4 | -1422183.0188 |              0.0633 |               0.8172 |                               0.3851 | True        | True             | False          | False                    | False      |
|   5 | -1426062.5839 |              0.1034 |               0.6319 |                               0.3009 | True        | False            | False          | False                    | False      |
|   6 | -1405273.2202 |              0.0187 |               0.6318 |                               0.0424 | False       | False            | False          | False                    | False      |
|   7 | -1387851.6718 |              0.0360 |               0.4645 |                               0.0816 | False       | False            | False          | False                    | False      |
|   8 | -1369220.6906 |              0.0276 |               0.5534 |                               0.0539 | False       | False            | False          | False                    | False      |

Selected reporting K: **3** (lowest within-Hellinger BIC among pre-screened stable/non-tiny K=2..8 solutions).

## Transform acceptance verdict: **FAIL**

- Zero-bin eta2 reduction versus CLR at K=3: -3.7%
  (gate >= 25%; pass=False).
- Timing eta2 retention versus CLR: 90.0%
  (gate >= 85%; pass=True).
- Structural size/stability/Jaccard screen pass=True.

Passing this screen means Hellinger is a defensible zero-preserving replacement
candidate under the declared diagnostics. It does not prove that remaining zeros
represent demand rather than service availability.

## Same-K transform comparison (selected K)

|   K | transform   |   zero_bin_eta2 |   activity_eta2 |   timing_mean_eta2 |   silhouette_within_transform |   min_cluster_share |   bootstrap_ari_mean |   bootstrap_min_cluster_jaccard_mean |
|----:|:------------|----------------:|----------------:|-------------------:|------------------------------:|--------------------:|---------------------:|-------------------------------------:|
|   3 | raw_share   |          0.5402 |          0.5018 |             0.2791 |                        0.0546 |              0.1370 |               0.6075 |                               0.3963 |
|   3 | CLR         |          0.8282 |          0.5585 |             0.1893 |                        0.1932 |              0.2805 |               0.8618 |                               0.8729 |
|   3 | Hellinger   |          0.8590 |          0.5619 |             0.1702 |                        0.0861 |              0.2734 |               0.8724 |                               0.8541 |

Silhouette values are reported for completeness but are not directly comparable
across transformed coordinate spaces. Raw-metric eta2 and label ARI are directly
comparable because they use the same LSOAs and external metrics.

|      K |   hellinger_vs_raw_ARI |   hellinger_vs_clr_ARI |   raw_vs_clr_ARI |
|-------:|-----------------------:|-----------------------:|-----------------:|
| 3.0000 |                 0.4824 |                 0.6120 |           0.3434 |

## Selected cluster signatures

|      K |   cluster |         n |   log_total_activity_mean |   log_total_activity_median |   direction_balance_mean |   direction_balance_median |   post_midnight_share_mean |   post_midnight_share_median |   deep_night_share_mean |   deep_night_share_median |   post_midnight_persistence_mean |   post_midnight_persistence_median |   weekend_ratio_mean |   weekend_ratio_median |   zero_bin_count_mean |   zero_bin_count_median |   post_midnight_zero_bin_count_mean |   post_midnight_zero_bin_count_median |
|-------:|----------:|----------:|--------------------------:|----------------------------:|-------------------------:|---------------------------:|---------------------------:|-----------------------------:|------------------------:|--------------------------:|---------------------------------:|-----------------------------------:|---------------------:|-----------------------:|----------------------:|------------------------:|------------------------------------:|--------------------------------------:|
| 3.0000 |    0.0000 | 1136.0000 |                    5.9232 |                      5.8233 |                  -0.1839 |                    -0.1974 |                     0.0728 |                       0.0678 |                  0.0471 |                    0.0414 |                           0.1131 |                             0.1019 |               0.7532 |                 0.7445 |               22.7773 |                 23.0000 |                             22.4595 |                               23.0000 |
| 3.0000 |    1.0000 | 1309.0000 |                    7.9131 |                      7.7695 |                  -0.0754 |                    -0.0908 |                     0.1240 |                       0.1184 |                  0.0711 |                    0.0663 |                           0.2136 |                             0.1953 |               0.8152 |                 0.8098 |                0.4813 |                  0.0000 |                              0.4813 |                                0.0000 |
| 3.0000 |    2.0000 |  920.0000 |                    6.2852 |                      6.2978 |                  -0.1238 |                    -0.1495 |                     0.1260 |                       0.1153 |                  0.0790 |                    0.0691 |                           0.2173 |                             0.1853 |               0.8002 |                 0.7867 |                4.1489 |                  2.0000 |                              4.0467 |                                2.0000 |

## Spatial diagnostic

|      K |   n_matched |   central_outer_total_variation |   central_outer_same_cluster_probability |
|-------:|------------:|--------------------------------:|-----------------------------------------:|
| 3.0000 |    330.0000 |                          0.2876 |                                   0.3613 |

## Figure inventory

- K diagnostics: `outputs/figures/hellinger_kdiag_full.png`.
- Construct diagnostics: `outputs/figures/hellinger_construct_diagnostics.png`.
- Profiles: `hellinger_profiles_k2.png` through `hellinger_profiles_k8.png`.
- Maps: `hellinger_map_k2.png` through `hellinger_map_k8.png`.
- Selected outputs: `hellinger_selected_profiles.png`,
  `hellinger_selected_map.png`, `hellinger_selected_feature_heatmap.png`.
