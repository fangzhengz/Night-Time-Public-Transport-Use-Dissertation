# Within-cluster homogeneity: literature mean>=1/hour threshold, K=3 and K=4

Same diagnostic as `CLUSTER_HOMOGENEITY_BOTTOM20.md` and `巴士聚类错误修改/outputs/report/CLUSTER_HOMOGENEITY.md`, computed here on the min(boardings,alightings)>=36 sample (n_core=3,365, 93.65% retained) for direct comparison against the bottom-20%-by-total-activity comparator.

Whole-sample average distance to the grand centroid, by K: K=3: 0.0971; K=4: 0.0971.
`relative_compactness_vs_sample` below 1 means the cluster is tighter
than the retained sample as a whole.

## Summary

|      K |   cluster |         n |   share |   mean_silhouette |   relative_compactness_vs_sample |   log_total_activity_mean |   log_total_activity_cv |   post_midnight_share_mean |   post_midnight_share_cv |   deep_night_share_mean |   deep_night_share_cv |   post_midnight_persistence_mean |   post_midnight_persistence_cv |
|-------:|----------:|----------:|--------:|------------------:|---------------------------------:|--------------------------:|------------------------:|---------------------------:|-------------------------:|------------------------:|----------------------:|---------------------------------:|-------------------------------:|
| 3.0000 |    0.0000 | 1283.0000 |  0.3813 |           -0.1328 |                           1.1878 |                    5.9039 |                  0.1233 |                     0.0726 |                   0.4847 |                  0.0450 |                0.6741 |                           0.1123 |                         0.5408 |
| 3.0000 |    1.0000 | 1621.0000 |  0.4817 |            0.2677 |                           0.7249 |                    7.6757 |                  0.1169 |                     0.1198 |                   0.3431 |                  0.0706 |                0.4384 |                           0.2032 |                         0.4272 |
| 3.0000 |    2.0000 |  461.0000 |  0.1370 |           -0.1731 |                           1.1979 |                    6.1874 |                  0.1589 |                     0.1594 |                   0.4073 |                  0.1020 |                0.5725 |                           0.2915 |                         0.5816 |
| 4.0000 |    0.0000 | 1147.0000 |  0.3409 |           -0.1523 |                           1.1955 |                    5.8717 |                  0.1270 |                     0.0680 |                   0.4819 |                  0.0417 |                0.6873 |                           0.1043 |                         0.5387 |
| 4.0000 |    1.0000 | 1062.0000 |  0.3156 |            0.1894 |                           0.6724 |                    8.0561 |                  0.1075 |                     0.1190 |                   0.3799 |                  0.0670 |                0.4476 |                           0.2050 |                         0.4933 |
| 4.0000 |    2.0000 |  311.0000 |  0.0924 |           -0.2202 |                           1.2912 |                    5.9894 |                  0.1498 |                     0.1614 |                   0.4279 |                  0.1061 |                0.6150 |                           0.2977 |                         0.6149 |
| 4.0000 |    3.0000 |  845.0000 |  0.2511 |            0.0135 |                           0.8182 |                    6.7649 |                  0.0913 |                     0.1257 |                   0.3146 |                  0.0796 |                0.4203 |                           0.2107 |                         0.3819 |

Full table (std, IQR, all six raw metrics):
`outputs/diagnostics/literature_mean1ph_cluster_homogeneity.csv`.
Boxplots: `outputs/figures/literature_mean1ph_homogeneity_boxplots_k{3,4}.png`.