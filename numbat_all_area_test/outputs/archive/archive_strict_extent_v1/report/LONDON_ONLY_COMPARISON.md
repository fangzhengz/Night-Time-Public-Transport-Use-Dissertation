# Does excluding out-of-Greater-London stations change the all-modes rail clustering?

## Material Passport

- Verification Status: ANALYZED
- Version Label: rail_allmodes_london_only_comparison_v1

## What changed

32 of 420 all-modes stations were removed before feature-building/GMM-fitting (not just downstream from LNWC/IMD as before) -- 16 with no NaPTAN Greater-London (area 490) coordinate match at all, 16 with coordinates but physically outside the Greater London/LNWC boundary. Everything else (feature engineering, GMM search grid, N_INIT=20, RANDOM_STATE=42) is identical to `02_build_features_allmodes.py` / `03_cluster_allmodes.py`.

## 1. Does the BIC-preferred K change?

**No.** Both the original 420-station and the new 388-station London-only run prefer diag-covariance K=6 by BIC -- consistent with canonical's own BIC-preferred K. Excluding the out-of-London stations does not change which K the model-selection criterion favours.

```
ORIGINAL (420 stations):
=== rail_allmodes: X (420, 344) ===
BIC-best (of ['diag', 'full']): covariance=diag, K=6, BIC=-1501451.4
  diag: best K=6 (BIC -1501451.4)
  full: best K=2 (BIC -934276.7)
kdiag (cov=diag) silhouette: K2=0.316, K3=0.149, K4=0.130, K5=0.116, K6=0.087, K7=0.113, K8=0.092, K9=0.095, K10=0.060, K11=0.067, K12=0.083
kdiag (cov=diag) BIC: K2=-1480613.7, K3=-1490429.4, K4=-1496339.0, K5=-1499102.4, K6=-1501451.4, K7=-1499670.3, K8=-1501283.8, K9=-1499155.5, K10=-1498731.7, K11=-1496826.6, K12=-1495004.7

LONDON-ONLY (388 stations):
=== rail_allmodes_london: X (388, 344) ===
BIC-best (of ['diag', 'full']): covariance=diag, K=6, BIC=-1392697.1
  diag: best K=6 (BIC -1392697.1)
  full: best K=2 (BIC -822803.1)
kdiag (cov=diag) silhouette: K2=0.328, K3=0.170, K4=0.163, K5=0.098, K6=0.091, K7=0.119, K8=0.111, K9=0.101, K10=0.107, K11=0.112, K12=0.112
kdiag (cov=diag) BIC: K2=-1374657.9, K3=-1383257.5, K4=-1388130.2, K5=-1391494.8, K6=-1392697.1, K7=-1390403.6, K8=-1390202.9, K9=-1389282.4, K10=-1387594.1, K11=-1386229.1, K12=-1385458.6
```

## 2. K-sweep diagnostics, side by side

| K | BIC (420) | silhouette (420) | bootstrap ARI (420) | BIC (388, London-only) | silhouette (388) | bootstrap ARI (388) |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | -1480614 | 0.316 | 0.830 | -1374658 | 0.328 | 0.834 |
| 3 | -1490429 | 0.149 | 0.473 | -1383258 | 0.170 | 0.612 |
| 4 | -1496339 | 0.130 | 0.593 | -1388130 | 0.163 | 0.644 |
| 5 | -1499102 | 0.116 | 0.448 | -1391495 | 0.098 | 0.416 |
| 6 | -1501451 | 0.087 | 0.455 | -1392697 | 0.091 | 0.484 |
| 7 | -1499670 | 0.113 | 0.399 | -1390404 | 0.119 | 0.441 |
| 8 | -1501284 | 0.092 | 0.437 | -1390203 | 0.111 | 0.433 |
| 9 | -1499155 | 0.095 | 0.435 | -1389282 | 0.101 | 0.465 |
| 10 | -1498732 | 0.060 | 0.364 | -1387594 | 0.107 | 0.463 |
| 11 | -1496827 | 0.067 | 0.360 | -1386229 | 0.112 | 0.488 |
| 12 | -1495005 | 0.083 | 0.389 | -1385459 | 0.112 | 0.415 |

Silhouette at K=5 does not improve after exclusion (0.116 -> 0.098) -- consistent with this project's standing finding that silhouette in this GMM/compositional-simplex setting is not a defect-detection metric worth optimising (see `project_silhouette_benchmark_recalibration_2026-07-23` memory). This should not be read as evidence the exclusion 'didn't help' -- see part 3.

## 3. K=5 partition comparison: how much actually changed for the 388 common stations?

ARI between the original K=5 labels (restricted to the 388 common stations) and the freshly refit London-only K=5 labels: **0.454** -- a substantial reshuffling, not a simple 'same clusters minus 32 stations' cleanup. Best cluster-to-cluster match (Hungarian algorithm on Jaccard):

|   orig_cluster |   london_cluster |   jaccard |   orig_cluster_n_common |   london_cluster_n |   intersection |
|---------------:|-----------------:|----------:|------------------------:|-------------------:|---------------:|
|          0.000 |            0.000 |     0.585 |                 201.000 |            143.000 |        127.000 |
|          1.000 |            2.000 |     0.757 |                  36.000 |             29.000 |         28.000 |
|          2.000 |            3.000 |     0.781 |                  94.000 |             77.000 |         75.000 |
|          3.000 |            1.000 |     0.786 |                  13.000 |             12.000 |         11.000 |
|          4.000 |            4.000 |     0.336 |                  44.000 |            127.000 |         43.000 |

Full contingency table (rows = original cluster, columns = new London-only cluster):

|   cluster_orig |   0 |   1 |   2 |   3 |   4 |
|---------------:|----:|----:|----:|----:|----:|
|              0 | 127 |   0 |   0 |   0 |  74 |
|              1 |   8 |   0 |  28 |   0 |   0 |
|              2 |   8 |   0 |   1 |  75 |  10 |
|              3 |   0 |  11 |   0 |   2 |   0 |
|              4 |   0 |   1 |   0 |   0 |  43 |

## 4. What specifically happened to the contaminated cluster (original cluster 4, 35.3% out-of-London)

|   cluster_orig |   n_excluded |   n_total |   share_excluded |
|---------------:|-------------:|----------:|-----------------:|
|              0 |        5.000 |   206.000 |            0.024 |
|              1 |        0.000 |    36.000 |            0.000 |
|              2 |        1.000 |    95.000 |            0.011 |
|              3 |        2.000 |    15.000 |            0.133 |
|              4 |       24.000 |    68.000 |            0.353 |

Of original cluster 4's 44 surviving (in-scope) members, 43 (97.7%) stay together in the new fit's cluster 4. But that new cluster 4 has 127 members total -- the other 84 are mostly former cluster-0 members (74 of cluster 0's 201 common members move into the new cluster 4). Reading this together with part 3's low ARI: once the out-of-London anchor stations (Watford Junction, Maidenhead, Slough, Shenfield, etc., all large interchanges with a distinctive early-closing/weekday-commute-heavy temporal shape) are removed, the remaining small in-London suburban termini that used to co-cluster with them are no longer distinct enough to stay separate -- they get absorbed into what was the largest, most central cluster. This is evidence the exclusion is not merely cosmetic: part of what defined the original cluster 4 as its own group was anchored by stations that do not belong in a Greater-London-scoped analysis in the first place.

## Interpretation limits

- This is a partition-level comparison (does membership change), not yet a re-run of the downstream LNWC/IMD linkage -- see `rq2_new_clusters_analysis` for that, rerun on the K=5 labels from this London-only refit.
- Silhouette/BIC not improving is expected given this project's established silhouette caveats and does not contradict the case for exclusion; the ARI and cluster-4 findings above are the more decision-relevant evidence.
- As before, K=5 is reported here for direct comparability with the canonical adopted choice, not because it is this sample's own BIC-preferred K (that remains K=6, same as before exclusion).