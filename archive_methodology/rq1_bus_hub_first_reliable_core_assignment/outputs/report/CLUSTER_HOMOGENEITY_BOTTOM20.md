# Within-cluster homogeneity: bottom-20%-excluded K=3 and K=4

Same diagnostic as `巴士聚类错误修改/outputs/report/CLUSTER_HOMOGENEITY.md`,
computed here on the bottom-20%-by-total-activity-excluded sample (cutoff=243.44, n_core=2874) for direct comparison against the adopted min(boardings,alightings)>=36 threshold.

Whole-sample average distance to the grand centroid: 0.0890.
`relative_compactness_vs_sample` below 1 means the cluster is tighter
than the retained sample as a whole.

## Summary

|      K |   cluster |         n |   share |   mean_silhouette |   relative_compactness_vs_sample |   log_total_activity_mean |   log_total_activity_cv |   post_midnight_share_mean |   post_midnight_share_cv |   deep_night_share_mean |   deep_night_share_cv |   post_midnight_persistence_mean |   post_midnight_persistence_cv |
|-------:|----------:|----------:|--------:|------------------:|---------------------------------:|--------------------------:|------------------------:|---------------------------:|-------------------------:|------------------------:|----------------------:|---------------------------------:|-------------------------------:|
| 3.0000 |    0.0000 | 1939.0000 |  0.6747 |            0.1244 |                           0.9017 |                    7.1776 |                  0.1486 |                     0.0919 |                   0.3719 |                  0.0527 |                0.4645 |                           0.1483 |                         0.4373 |
| 3.0000 |    1.0000 |  302.0000 |  0.1051 |           -0.0414 |                           1.1660 |                    7.2033 |                  0.1708 |                     0.1664 |                   0.4017 |                  0.0976 |                0.5675 |                           0.3181 |                         0.5434 |
| 3.0000 |    2.0000 |  633.0000 |  0.2203 |            0.0876 |                           0.9488 |                    6.7657 |                  0.1187 |                     0.1495 |                   0.3024 |                  0.1004 |                0.3955 |                           0.2604 |                         0.4200 |
| 4.0000 |    0.0000 |  224.0000 |  0.0779 |           -0.1827 |                           1.2804 |                    6.7932 |                  0.1565 |                     0.1659 |                   0.4239 |                  0.0997 |                0.6041 |                           0.3187 |                         0.5764 |
| 4.0000 |    1.0000 | 1191.0000 |  0.4144 |            0.2200 |                           0.7206 |                    7.9518 |                  0.1057 |                     0.1231 |                   0.3268 |                  0.0709 |                0.4111 |                           0.2106 |                         0.4110 |
| 4.0000 |    2.0000 |  399.0000 |  0.1388 |           -0.0469 |                           1.0248 |                    6.3890 |                  0.0803 |                     0.1456 |                   0.3460 |                  0.0993 |                0.4715 |                           0.2518 |                         0.4893 |
| 4.0000 |    3.0000 | 1060.0000 |  0.3688 |           -0.1083 |                           1.0899 |                    6.4471 |                  0.0975 |                     0.0767 |                   0.3708 |                  0.0461 |                0.5308 |                           0.1185 |                         0.4126 |

Full table (std, IQR, all six raw metrics):
`outputs/diagnostics/bottom20_cluster_homogeneity.csv`.
Boxplots: `outputs/figures/bottom20_homogeneity_boxplots_k{3,4}.png`.