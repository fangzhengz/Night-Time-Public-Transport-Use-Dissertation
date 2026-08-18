## Material Passport

- Origin: `numbat_all_area_test` extension check -- stability battery (K=6 vs K=7)
- Generated: 2026-07-22T22:40:08.527159+00:00
- Verification status: checked

# All-Modes Rail Clustering: K=6 vs K=7 Internal Stability Check

## Scope

This check uses only the 344-dimensional full-week entry/exit feature
matrix for the 420 all-modes stations (LU + DLR + Overground + Elizabeth
line; trams are structurally excluded, see the main comparison report) and
the saved K=6/K=7 labels. K=6/K=7 is this
all-modes dataset's own closest BIC pair (see `rail_allmodes_bic_best.txt`)
-- the direct analogue of why the canonical 270-station study chose K=5 vs
K=6 (the two live candidates, not an arbitrary pick). Methodology (diag
GMM, bootstrap=200, seed_runs=20) is identical to
`rail_k_selection_validation`.

## Global evidence

| K | BIC_refit    | silhouette | calinski_harabasz | davies_bouldin | bootstrap_ARI_mean_200 | bootstrap_ARI_q025_200 | bootstrap_ARI_q975_200 | weakest_cluster_jaccard | weak_cluster_count | seed_ARI_mean |
| - | ------------ | ---------- | ----------------- | -------------- | ---------------------- | ---------------------- | ---------------------- | ----------------------- | ------------------ | ------------- |
| 6 | -1501451.394 | 0.087      | 34.449            | 2.856          | 0.460                  | 0.238                  | 0.665                  | 0.214                   | 5                  | 0.598         |
| 7 | -1499670.261 | 0.113      | 39.491            | 2.236          | 0.438                  | 0.253                  | 0.686                  | 0.304                   | 5                  | 0.509         |

- BIC difference (K7 minus K6): `1781.134`. K=6 has lower (better) refitted BIC than K=7.
- Silhouette difference (K7 minus K6): `0.025679`.
- Paired 200-replicate bootstrap ARI: K=6 = `0.460`,
  K=7 = `0.438`.
- Paired difference K6 minus K7: mean `0.022`,
  95% empirical interval `[-0.319, 0.308]`;
  K=6 is higher in `53.0%` of paired resamples.
- Full-data random-seed mean ARI: K=6 = `0.598`,
  K=7 = `0.509`.

## K=6 to K=7 structure

- Adjusted Rand Index: `0.645`
- Best one-to-one matched stations: `308` /
  `420` (`73.3%`)

| K6_cluster | matched_K7_cluster | intersection | reference_size | candidate_size | jaccard |
| ---------- | ------------------ | ------------ | -------------- | -------------- | ------- |
| 0          | 2                  | 50           | 86             | 74             | 0.455   |
| 1          | 5                  | 27           | 33             | 27             | 0.818   |
| 2          | 3                  | 40           | 78             | 42             | 0.500   |
| 3          | 1                  | 161          | 170            | 180            | 0.852   |
| 4          | 4                  | 10           | 13             | 17             | 0.500   |
| 5          | 0                  | 20           | 40             | 29             | 0.408   |

## Weak K=7 components under bootstrap

| K7_cluster | jaccard_mean | share_jaccard_below_0_50 |
| ---------- | ------------ | ------------------------ |
| 2          | 0.323        | 0.820                    |
| 3          | 0.463        | 0.610                    |
| 4          | 0.412        | 0.720                    |
| 5          | 0.417        | 0.695                    |
| 6          | 0.304        | 0.840                    |

## Full cluster-level silhouette

| K | cluster | n   | silhouette_mean | silhouette_median | negative_share |
| - | ------- | --- | --------------- | ----------------- | -------------- |
| 6 | 0       | 86  | 0.021           | 0.022             | 0.488          |
| 6 | 1       | 33  | 0.062           | 0.060             | 0.152          |
| 6 | 2       | 78  | -0.022          | -0.030            | 0.667          |
| 6 | 3       | 170 | 0.214           | 0.206             | 0.006          |
| 6 | 4       | 13  | -0.272          | -0.285            | 1.000          |
| 6 | 5       | 40  | 0.044           | 0.021             | 0.450          |
| 7 | 0       | 29  | 0.183           | 0.192             | 0.138          |
| 7 | 1       | 180 | 0.214           | 0.229             | 0.011          |
| 7 | 2       | 74  | 0.130           | 0.120             | 0.054          |
| 7 | 3       | 42  | -0.052          | -0.061            | 0.714          |
| 7 | 4       | 17  | -0.133          | -0.115            | 0.824          |
| 7 | 5       | 27  | 0.001           | 0.006             | 0.481          |
| 7 | 6       | 51  | -0.031          | -0.026            | 0.725          |

## Interpretation rules

1. Bootstrap measures resampling recurrence, not the probability a given K is correct.
2. Random-seed stability measures optimisation sensitivity; it is a distinct concept.
3. This is the same methodology as `rail_k_selection_validation` (canonical
   270 stations, K=5 vs K=6) applied to a different station scope --
   numbers are not directly comparable across the two reports (different
   station counts and feature distributions); read each within its own scope.

## Limitations

- Conditional on the current 344-dim features, normalisation, GMM family, and diagonal covariance.
- 150 of the 420 stations here were only added in this extension
  check and have not had the same manual review as the canonical 270,
  though the 13 co-located cross-mode sites have been merged via
  `01b_merge_colocated_stations.py`.
- Stability does not by itself confer urban-functional or socio-economic meaning on a cluster.

## Reproduction

```
python src/07_stability_allmodes.py
```
