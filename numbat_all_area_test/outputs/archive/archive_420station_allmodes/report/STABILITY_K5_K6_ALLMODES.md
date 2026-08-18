## Material Passport

- Origin: `numbat_all_area_test` extension check -- stability battery (K=5 vs K=6)
- Generated: 2026-07-22T21:35:54.426001+00:00
- Verification status: checked

# All-Modes Rail Clustering: K=5 vs K=6 Internal Stability Check

## Scope

This check uses only the 344-dimensional full-week entry/exit feature
matrix for the 420 all-modes stations (LU + DLR + Overground + Elizabeth
line; trams are structurally excluded, see the main comparison report) and
the saved K=5/K=6 labels. K=5/K=6 is this
all-modes dataset's own closest BIC pair (see `rail_allmodes_bic_best.txt`)
-- the direct analogue of why the canonical 270-station study chose K=5 vs
K=6 (the two live candidates, not an arbitrary pick). Methodology (diag
GMM, bootstrap=200, seed_runs=20) is identical to
`rail_k_selection_validation`.

## Global evidence

| K | BIC_refit    | silhouette | calinski_harabasz | davies_bouldin | bootstrap_ARI_mean_200 | bootstrap_ARI_q025_200 | bootstrap_ARI_q975_200 | weakest_cluster_jaccard | weak_cluster_count | seed_ARI_mean |
| - | ------------ | ---------- | ----------------- | -------------- | ---------------------- | ---------------------- | ---------------------- | ----------------------- | ------------------ | ------------- |
| 5 | -1499102.374 | 0.116      | 39.617            | 2.558          | 0.458                  | 0.191                  | 0.778                  | 0.386                   | 3                  | 0.635         |
| 6 | -1501451.394 | 0.087      | 34.449            | 2.856          | 0.460                  | 0.238                  | 0.665                  | 0.214                   | 5                  | 0.598         |

- BIC difference (K6 minus K5): `-2349.021`. K=6 has lower (better) refitted BIC than K=5.
- Silhouette difference (K6 minus K5): `-0.028901`.
- Paired 200-replicate bootstrap ARI: K=5 = `0.458`,
  K=6 = `0.460`.
- Paired difference K5 minus K6: mean `-0.002`,
  95% empirical interval `[-0.317, 0.311]`;
  K=5 is higher in `48.5%` of paired resamples.
- Full-data random-seed mean ARI: K=5 = `0.635`,
  K=6 = `0.598`.

## K=5 to K=6 structure

- Adjusted Rand Index: `0.669`
- Best one-to-one matched stations: `335` /
  `420` (`79.8%`)

| K5_cluster | matched_K6_cluster | intersection | reference_size | candidate_size | jaccard |
| ---------- | ------------------ | ------------ | -------------- | -------------- | ------- |
| 0          | 3                  | 170          | 206            | 170            | 0.825   |
| 1          | 1                  | 33           | 36             | 33             | 0.917   |
| 2          | 0                  | 60           | 95             | 86             | 0.496   |
| 3          | 4                  | 11           | 15             | 13             | 0.647   |
| 4          | 2                  | 61           | 68             | 78             | 0.718   |

## Weak K=6 components under bootstrap

| K6_cluster | jaccard_mean | share_jaccard_below_0_50 |
| ---------- | ------------ | ------------------------ |
| 0          | 0.380        | 0.775                    |
| 1          | 0.462        | 0.540                    |
| 2          | 0.477        | 0.500                    |
| 4          | 0.214        | 0.950                    |
| 5          | 0.399        | 0.790                    |

## Full cluster-level silhouette

| K | cluster | n   | silhouette_mean | silhouette_median | negative_share |
| - | ------- | --- | --------------- | ----------------- | -------------- |
| 5 | 0       | 206 | 0.245           | 0.244             | 0.005          |
| 5 | 1       | 36  | 0.071           | 0.084             | 0.167          |
| 5 | 2       | 95  | 0.036           | 0.025             | 0.442          |
| 5 | 3       | 15  | -0.174          | -0.133            | 1.000          |
| 5 | 4       | 68  | -0.075          | -0.083            | 0.809          |
| 6 | 0       | 86  | 0.021           | 0.022             | 0.488          |
| 6 | 1       | 33  | 0.062           | 0.060             | 0.152          |
| 6 | 2       | 78  | -0.022          | -0.030            | 0.667          |
| 6 | 3       | 170 | 0.214           | 0.206             | 0.006          |
| 6 | 4       | 13  | -0.272          | -0.285            | 1.000          |
| 6 | 5       | 40  | 0.044           | 0.021             | 0.450          |

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
