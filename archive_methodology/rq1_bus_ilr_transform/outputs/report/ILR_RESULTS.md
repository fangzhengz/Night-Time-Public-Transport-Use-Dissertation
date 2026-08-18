# ILR-coordinate bus clustering: results

## Material Passport

- Mode: deterministic feature reconstruction plus stochastic GMM/bootstrap
- Input sample: 3,365 LSOAs, exact match to CLR and official raw-share sample
- Zero handling: same empirical-prior posterior, alpha=1.0
- Standard ILR coordinates: 70
- Retained non-zero sample-space dimensions: 58
- Existing CLR outputs modified: no

## Coordinate audit

```json
{
  "n_lsoa": 3365,
  "clr_columns": 72,
  "ilr_columns": 70,
  "centered_ilr_rank": 58,
  "retained_variance_fraction": 0.9999999999999998,
  "max_sampled_distance_error_clr_vs_ilr70": 7.105427357601002e-15,
  "max_sampled_distance_error_ilr70_vs_rank": 9.237055564881302e-14,
  "min_retained_explained_variance": 0.00773610428616636,
  "max_abs_rebuilt_clr_vs_saved_clr": 0.0
}
```

The standard Helmert ILR and rank-reduced fitted coordinates preserve the same
Aitchison/CLR sample distances. Absolute BIC values must not be compared with
the old redundant 72-column CLR fit because the fitted dimensionality differs.

## BIC grid summary

| covariance   |   K |         BIC |   min_cluster_n |   min_cluster_share |
|:-------------|----:|------------:|----------------:|--------------------:|
| diag         |  12 | 224707.9538 |              54 |              0.0160 |
| full         |   4 | 136320.8935 |             558 |              0.1658 |
| spherical    |  12 | 466802.8122 |             156 |              0.0464 |
| tied         |  12 | 298706.8540 |              34 |              0.0101 |

Global BIC minimum family used directly; no override needed.

Reporting family: **full**. BIC-preferred K within this family: **4**.

## K diagnostics

|       K |         BIC |   silhouette |   davies_bouldin |   activity_eta2 |   zero_bin_eta2 |   timing_mean_eta2 |   min_cluster_share |   bootstrap_ari_mean |   bootstrap_min_cluster_jaccard_mean |
|--------:|------------:|-------------:|-----------------:|----------------:|----------------:|-------------------:|--------------------:|---------------------:|-------------------------------------:|
|  2.0000 | 268032.2684 |       0.2616 |           1.3545 |          0.5103 |          0.4966 |             0.1007 |              0.4256 |               0.3824 |                               0.6570 |
|  3.0000 | 160956.6248 |       0.1932 |           1.9548 |          0.5585 |          0.8282 |             0.1893 |              0.2805 |               0.8618 |                               0.8729 |
|  4.0000 | 136320.8935 |       0.1492 |           2.4911 |          0.5741 |          0.9182 |             0.1941 |              0.1658 |               0.7880 |                               0.4271 |
|  5.0000 | 145283.6902 |       0.1431 |           2.5066 |          0.5783 |          0.9278 |             0.2033 |              0.0698 |               0.7709 |                               0.1251 |
|  6.0000 | 146731.1740 |       0.1350 |           2.8055 |          0.5896 |          0.9288 |             0.2060 |              0.0128 |             nan      |                             nan      |
|  7.0000 | 153968.8272 |       0.0694 |           3.2886 |          0.6225 |          0.9423 |             0.2188 |              0.0178 |             nan      |                             nan      |
|  8.0000 | 158659.8969 |       0.0754 |           3.3650 |          0.6272 |          0.9491 |             0.2293 |              0.0187 |             nan      |                             nan      |
|  9.0000 | 164267.1690 |       0.0703 |           3.5987 |          0.6544 |          0.9438 |             0.2249 |              0.0137 |             nan      |                             nan      |
| 10.0000 | 181769.9956 |       0.0492 |           3.2608 |          0.6281 |          0.9452 |             0.2285 |              0.0199 |             nan      |                             nan      |
| 11.0000 | 180253.3948 |       0.0549 |           3.3505 |          0.6428 |          0.9466 |             0.2420 |              0.0131 |             nan      |                             nan      |
| 12.0000 | 194095.0745 |       0.0598 |           3.2010 |          0.6390 |          0.9442 |             0.2514 |              0.0122 |             nan      |                             nan      |

## Direct label comparison with CLR

|        K |   ARI_ilr_vs_clr |
|---------:|-----------------:|
| 3.000000 |         1.000000 |
| 4.000000 |         1.000000 |

## Per-cluster diagnostics

|      K |   cluster |         n |   share |   mean_silhouette |   relative_compactness_vs_sample |   zero_bin_count_mean |   log_total_activity_mean |   post_midnight_share_mean |
|-------:|----------:|----------:|--------:|------------------:|---------------------------------:|----------------------:|--------------------------:|---------------------------:|
| 3.0000 |    0.0000 | 1249.0000 |  0.3712 |           -0.2235 |                           0.9896 |                6.0424 |                    6.4142 |                     0.1116 |
| 3.0000 |    1.0000 | 1172.0000 |  0.3483 |            0.5330 |                           0.3922 |                0.0265 |                    7.9841 |                     0.1340 |
| 3.0000 |    2.0000 |  944.0000 |  0.2805 |            0.3226 |                           0.7939 |               24.0932 |                    5.8271 |                     0.0682 |
| 4.0000 |    0.0000 |  558.0000 |  0.1658 |            0.2319 |                           0.6974 |               26.8136 |                    5.5997 |                     0.0592 |
| 4.0000 |    1.0000 | 1132.0000 |  0.3364 |            0.4782 |                           0.3826 |                0.0027 |                    8.0152 |                     0.1348 |
| 4.0000 |    2.0000 |  607.0000 |  0.1804 |            0.0524 |                           0.8591 |               18.6952 |                    6.2450 |                     0.0885 |
| 4.0000 |    3.0000 | 1068.0000 |  0.3174 |           -0.1876 |                           0.8696 |                3.7537 |                    6.4428 |                     0.1138 |

## Interpretation boundary

ILR is a non-redundant coordinate expression of the same posterior compositions,
not a new substantive feature definition. Similar labels are expected when the
same full-covariance model optimum is recovered. A difference would indicate a
numerical/regularisation effect, not new passenger information.
