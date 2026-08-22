## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Verification Status: ANALYZED
- Version Label: stoparea_only_isolated_v1

# StopArea-only isolation comparison

Only spatial preprocessing differs. Downstream feature and GMM source is
executed directly from `rq1_bus_hub_first_isolated_test/src` with paths rebound.

## Sample

| version          |   n_lsoa_min_total_1 |   n_common_all_three |
|:-----------------|---------------------:|---------------------:|
| original         |                 4100 |                 3743 |
| parent_hub_first |                 3784 |                 3743 |
| stoparea_only    |                 3791 |                 3743 |

## Global BIC minimum within each version

| version          | covariance   |   K |   BIC_within_version |
|:-----------------|:-------------|----:|---------------------:|
| original         | full         |   3 |        -2297631.8682 |
| parent_hub_first | full         |   3 |        -2137124.0831 |
| stoparea_only    | full         |   3 |        -2141222.8590 |

Absolute BIC is not compared across versions because sample size and input
realisation differ. Each value is used only for K/covariance choice within its version.

## K=3 and K=4 diagnostics

| version          |   K |           BIC |   silhouette |   calinski_harabasz |   davies_bouldin |    ARI |   ARI_sd |
|:-----------------|----:|--------------:|-------------:|--------------------:|-----------------:|-------:|---------:|
| original         |   3 | -2297631.8682 |       0.1691 |             99.7773 |           6.1784 | 0.8207 |   0.0441 |
| original         |   4 | -2295104.0050 |       0.0277 |            100.1385 |           6.3215 | 0.4091 |   0.0252 |
| parent_hub_first |   3 | -2137124.0831 |       0.1422 |            100.9082 |           5.8815 | 0.8120 |   0.0819 |
| parent_hub_first |   4 | -2134171.5807 |       0.0240 |            102.5283 |           5.6541 | 0.4631 |   0.0929 |
| stoparea_only    |   3 | -2141222.8590 |       0.1353 |            101.3014 |           5.6868 | 0.7984 |   0.0835 |
| stoparea_only    |   4 | -2138983.5360 |       0.0292 |            102.9629 |           5.5985 | 0.4784 |   0.1015 |

## Same-K label agreement

| left             | right            |   K |   n_matched |    ARI |
|:-----------------|:-----------------|----:|------------:|-------:|
| original         | stoparea_only    |   3 |        3750 | 0.6412 |
| original         | stoparea_only    |   4 |        3750 | 0.6210 |
| original         | stoparea_only    |   5 |        3750 | 0.5730 |
| original         | stoparea_only    |   6 |        3750 | 0.5517 |
| original         | stoparea_only    |   7 |        3750 | 0.5034 |
| original         | stoparea_only    |   8 |        3750 | 0.4770 |
| parent_hub_first | stoparea_only    |   3 |        3784 | 0.9795 |
| parent_hub_first | stoparea_only    |   4 |        3784 | 0.9791 |
| parent_hub_first | stoparea_only    |   5 |        3784 | 0.9109 |
| parent_hub_first | stoparea_only    |   6 |        3784 | 0.6219 |
| parent_hub_first | stoparea_only    |   7 |        3784 | 0.7116 |
| parent_hub_first | stoparea_only    |   8 |        3784 | 0.6260 |
| original         | parent_hub_first |   3 |        3743 | 0.6396 |
| original         | parent_hub_first |   4 |        3743 | 0.6177 |
| original         | parent_hub_first |   5 |        3743 | 0.5576 |
| original         | parent_hub_first |   6 |        3743 | 0.5026 |
| original         | parent_hub_first |   7 |        3743 | 0.5261 |
| original         | parent_hub_first |   8 |        3743 | 0.4486 |

## Interpretation boundary

This test identifies sensitivity to the spatial-unit definition. It does not
decide whether a child StopArea or a complete parent interchange is the true
substantive unit; that decision must use coverage, direction-zero behaviour,
stability and the RQ's area-versus-interchange interpretation together.
