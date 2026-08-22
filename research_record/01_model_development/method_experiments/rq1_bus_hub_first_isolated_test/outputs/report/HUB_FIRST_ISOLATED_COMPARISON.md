# Hub-first isolation test: comparison against the true original

Single changed variable: stop-to-LSOA aggregation (hub-first vs the
original point-in-polygon assignment). MIN_TOTAL=1, no one-direction
exclusion, no weaker-direction floor, alpha=0, identical GMM search --
all copied verbatim from `cluster_clean_version_fullweek/src/config.py`.

## Sample

- original (point-in-polygon, MIN_TOTAL=1): n=4100
- hub-first (MIN_TOTAL=1, otherwise identical): n=3784
- common LSOA codes present in both: 3743
- only in original (hub-first merged them away): 357
- only in hub-first (newly appear after hub merging): 41

## Global BIC minimum

- original: covariance=full, K=3, BIC=-2297631.9
- hub-first: covariance=full, K=3, BIC=-2137124.1

## K diagnostics, side by side

|       K |   BIC_original |   silhouette_original |   calinski_harabasz_original |   davies_bouldin_original |   ARI_original |   ARI_sd_original |   BIC_hubfirst |   silhouette_hubfirst |   calinski_harabasz_hubfirst |   davies_bouldin_hubfirst |   ARI_hubfirst |   ARI_sd_hubfirst |
|--------:|---------------:|----------------------:|-----------------------------:|--------------------------:|---------------:|------------------:|---------------:|----------------------:|-----------------------------:|--------------------------:|---------------:|------------------:|
|  2.0000 |  -2221929.1488 |                0.1267 |                     214.0097 |                    3.6722 |         0.5829 |            0.2823 |  -2084433.1729 |                0.1797 |                     190.3668 |                    3.8645 |         0.8458 |            0.0749 |
|  3.0000 |  -2297631.8682 |                0.1691 |                      99.7773 |                    6.1784 |         0.8207 |            0.0441 |  -2137124.0831 |                0.1422 |                     100.9082 |                    5.8815 |         0.8120 |            0.0819 |
|  4.0000 |  -2295104.0050 |                0.0277 |                     100.1385 |                    6.3215 |         0.4091 |            0.0252 |  -2134171.5807 |                0.0240 |                     102.5283 |                    5.6541 |         0.4631 |            0.0929 |
|  5.0000 |  -2291177.8576 |                0.0252 |                      85.2507 |                    5.4558 |         0.4834 |            0.0507 |  -2128621.3634 |               -0.0020 |                      84.5633 |                    5.2790 |         0.4752 |            0.0660 |
|  6.0000 |  -2274481.3179 |                0.0251 |                      72.0778 |                    5.1509 |         0.5142 |            0.0598 |  -2113486.9698 |               -0.0146 |                      72.7034 |                    5.6032 |         0.4837 |            0.1057 |
|  7.0000 |  -2260887.0682 |                0.0197 |                      72.5303 |                    6.3480 |         0.5333 |            0.0778 |  -2094631.1097 |               -0.0269 |                      66.2858 |                    5.1176 |         0.4961 |            0.0528 |
|  8.0000 |  -2244406.0375 |                0.0015 |                      63.1410 |                    6.1944 |         0.4841 |            0.0795 |  -2077172.0433 |               -0.0330 |                      75.5981 |                    5.1822 |         0.4707 |            0.0997 |
|  9.0000 |  -2223234.5512 |               -0.0135 |                      82.8535 |                    5.5543 |         0.4844 |            0.0450 |  -2058563.4564 |               -0.0224 |                      82.8248 |                    4.8457 |         0.5080 |            0.0881 |
| 10.0000 |  -2204633.2041 |               -0.0258 |                      63.0634 |                    5.8270 |         0.4862 |            0.0888 |  -2040252.7772 |               -0.0287 |                      78.1202 |                    4.8888 |         0.4900 |            0.0740 |
| 11.0000 |  -2187088.9055 |               -0.0259 |                      75.7755 |                    4.4135 |         0.4561 |            0.0725 |  -2024258.2868 |               -0.0418 |                      78.8045 |                    4.7952 |         0.4778 |            0.0652 |
| 12.0000 |  -2166186.9284 |               -0.0056 |                      75.4010 |                    5.0275 |         0.5320 |            0.0797 |  -2004131.2047 |               -0.0321 |                      75.0381 |                    4.4833 |         0.4818 |            0.0445 |

## Label agreement: original vs hub-first, same K, common LSOAs only

ARI compares this run's labels against the true original's labels for
the SAME candidate K, restricted to LSOA codes present in both samples
-- i.e., holding K fixed, how much does re-clustering after hub-first
reassignment alone move individual units between clusters.

|      K |   n_matched |   ARI_original_vs_hubfirst |
|-------:|------------:|---------------------------:|
| 3.0000 |   3743.0000 |                     0.6396 |
| 4.0000 |   3743.0000 |                     0.6177 |
| 5.0000 |   3743.0000 |                     0.5576 |
| 6.0000 |   3743.0000 |                     0.5026 |
| 7.0000 |   3743.0000 |                     0.5261 |
| 8.0000 |   3743.0000 |                     0.4486 |
