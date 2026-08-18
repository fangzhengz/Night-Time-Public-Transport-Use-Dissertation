# Does excluding no-NaPTAN-match stations change the all-modes rail clustering?

## Material Passport

- Verification Status: ANALYZED
- Version Label: rail_allmodes_london_only_comparison_v2_naptan_match_criterion

## What changed

16 of 420 all-modes stations were removed before feature-building/GMM-fitting (not just downstream from LNWC/IMD as before) -- specifically, only stations with no NaPTAN Greater-London (area 490) coordinate match at all. This corrects an earlier same-day attempt (archived at `outputs/archive_strict_extent_v1/`) that also excluded stations physically outside the strict Greater London boundary polygon even when they DO have a NaPTAN match (e.g. Amersham, Chesham, Epping) -- inconsistent with canonical, whose own 270-station clustering already includes those same border stations and only excludes them downstream from LNWC/IMD. That is now this refit's convention too: 404 stations enter the clustering; the LNWC/IMD-extent check is applied only at the `rq2_new_clusters_analysis` stage. Everything else (feature engineering, GMM search grid, N_INIT=20, RANDOM_STATE=42) is identical to `02_build_features_allmodes.py` / `03_cluster_allmodes.py`.

## 1. Does the BIC-preferred K change?

**Yes.** Original: diag-covariance K=6 (BIC=-1501451.4). After excluding the 16 no-match stations: diag-covariance K=5 (BIC=-1446368.9). Unlike the (superseded) stricter-extent attempt, which left the BIC-preferred K unchanged at 6, this smaller, more targeted exclusion does shift the model-selection optimum.

## 2. K-sweep diagnostics, side by side

| K | BIC (420) | silhouette (420) | bootstrap ARI (420) | BIC (404, refit) | silhouette (404) | bootstrap ARI (404) |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | -1480614 | 0.316 | 0.830 | -1428226 | 0.317 | 0.833 |
| 3 | -1490429 | 0.149 | 0.473 | -1438557 | 0.149 | 0.561 |
| 4 | -1496339 | 0.130 | 0.593 | -1442874 | 0.145 | 0.556 |
| 5 | -1499102 | 0.116 | 0.448 | -1446369 | 0.102 | 0.524 |
| 6 | -1501451 | 0.087 | 0.455 | -1445565 | 0.104 | 0.498 |
| 7 | -1499670 | 0.113 | 0.399 | -1445623 | 0.113 | 0.479 |
| 8 | -1501284 | 0.092 | 0.437 | -1446113 | 0.099 | 0.472 |
| 9 | -1499155 | 0.095 | 0.435 | -1444647 | 0.107 | 0.502 |
| 10 | -1498732 | 0.060 | 0.364 | -1444555 | 0.113 | 0.393 |
| 11 | -1496827 | 0.067 | 0.360 | -1442981 | 0.104 | 0.454 |
| 12 | -1495005 | 0.083 | 0.389 | -1440404 | 0.084 | 0.414 |

Silhouette at K=5 specifically: 0.116 -> 0.102. This project's standing finding is that silhouette in this GMM/compositional-simplex setting is not a defect-detection metric worth optimising (see `project_silhouette_benchmark_recalibration_2026-07-23` memory) -- read the ARI and cluster-composition evidence below as the more decision-relevant signal.

## 3. K=5 partition comparison: how much actually changed for the 404 common stations?

ARI between the original K=5 labels (restricted to the 404 common stations) and the freshly refit K=5 labels: **0.492**. Best cluster-to-cluster match (Hungarian algorithm on Jaccard):

|   orig_cluster |   london_cluster |   jaccard |   orig_cluster_n_common |   london_cluster_n |   intersection |
|---------------:|-----------------:|----------:|------------------------:|-------------------:|---------------:|
|          0.000 |            3.000 |     0.628 |                 205.000 |            163.000 |        142.000 |
|          1.000 |            1.000 |     0.694 |                  36.000 |             25.000 |         25.000 |
|          2.000 |            4.000 |     0.796 |                  94.000 |             82.000 |         78.000 |
|          3.000 |            2.000 |     0.786 |                  13.000 |             12.000 |         11.000 |
|          4.000 |            0.000 |     0.447 |                  56.000 |            122.000 |         55.000 |

Full contingency table (rows = original cluster, columns = new refit cluster):

|   cluster_orig |   0 |   1 |   2 |   3 |   4 |
|---------------:|----:|----:|----:|----:|----:|
|              0 |  63 |   0 |   0 | 142 |   0 |
|              1 |   0 |  25 |   0 |   9 |   2 |
|              2 |   4 |   0 |   0 |  12 |  78 |
|              3 |   0 |   0 |  11 |   0 |   2 |
|              4 |  55 |   0 |   1 |   0 |   0 |

## 4. Which original cluster had the most excluded stations, and where did its survivors land?

|   cluster_orig |   n_excluded |   n_total |   share_excluded |
|---------------:|-------------:|----------:|-----------------:|
|              4 |       12.000 |    68.000 |            0.176 |
|              3 |        2.000 |    15.000 |            0.133 |
|              2 |        1.000 |    95.000 |            0.011 |
|              0 |        1.000 |   206.000 |            0.005 |
|              1 |        0.000 |    36.000 |            0.000 |

Original cluster 4 had the highest concentration of now-excluded stations: 12/68 (17.6%). Of its 56 surviving (common) members, 55 (98.2%) land together in the new fit's cluster 0, which has 122 members in total -- the other 67 are absorbed from other original clusters, meaning cluster 4's clean survivors did not stay a distinct group on their own; they merged into a larger cluster once the excluded stations were removed.

## Interpretation limits

- This is a partition-level comparison (does membership change), not yet a re-run of the downstream LNWC/IMD linkage -- see `rq2_new_clusters_analysis` for that, rerun on the K=5 labels from this refit.
- Silhouette not improving is expected given this project's established silhouette caveats and does not by itself argue against the exclusion; the ARI and cluster-composition findings above are the more decision-relevant evidence.
- K=5 is reported in parts 3-4 for direct comparability with the canonical adopted choice, not necessarily because it is this sample's own BIC-preferred K (see part 1).