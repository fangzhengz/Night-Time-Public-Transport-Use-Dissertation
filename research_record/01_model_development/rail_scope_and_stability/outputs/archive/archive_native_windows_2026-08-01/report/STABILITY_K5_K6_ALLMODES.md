## Material Passport

- Origin: `numbat_all_area_test` extension check -- stability battery (K=5 vs K=6)
- Generated: 2026-07-24T00:36:17.438767+00:00
- Verification status: checked

# All-Modes Rail Clustering: K=5 vs K=6 Internal Stability Check

## Scope

This check uses only the 344-dimensional full-week entry/exit feature
matrix for the 404 all-modes stations (LU + DLR + Overground + Elizabeth
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
| 5 | -1446368.898 | 0.102      | 39.357            | 2.641          | 0.500                  | 0.276                  | 0.785                  | 0.288                   | 2                  | 0.894         |
| 6 | -1445565.279 | 0.104      | 41.338            | 2.135          | 0.484                  | 0.278                  | 0.712                  | 0.333                   | 4                  | 0.624         |

- BIC difference (K6 minus K5): `803.619`. K=5 has lower (better) refitted BIC than K=6.
- Silhouette difference (K6 minus K5): `0.002056`.
- Paired 200-replicate bootstrap ARI: K=5 = `0.500`,
  K=6 = `0.484`.
- Paired difference K5 minus K6: mean `0.016`,
  95% empirical interval `[-0.294, 0.353]`;
  K=5 is higher in `50.5%` of paired resamples.
- Full-data random-seed mean ARI: K=5 = `0.894`,
  K=6 = `0.624`.

## K=5 to K=6 structure

- Adjusted Rand Index: `0.656`
- Best one-to-one matched stations: `312` /
  `404` (`77.2%`)

| K5_cluster | matched_K6_cluster | intersection | reference_size | candidate_size | jaccard |
| ---------- | ------------------ | ------------ | -------------- | -------------- | ------- |
| 0          | 2                  | 75           | 122            | 76             | 0.610   |
| 1          | 0                  | 25           | 25             | 29             | 0.862   |
| 2          | 1                  | 10           | 12             | 12             | 0.714   |
| 3          | 5                  | 151          | 163            | 163            | 0.863   |
| 4          | 4                  | 51           | 82             | 52             | 0.614   |

## Weak K=6 components under bootstrap

| K6_cluster | jaccard_mean | share_jaccard_below_0_50 |
| ---------- | ------------ | ------------------------ |
| 0          | 0.476        | 0.535                    |
| 1          | 0.333        | 0.820                    |
| 3          | 0.368        | 0.700                    |
| 4          | 0.456        | 0.650                    |

## Full cluster-level silhouette

| K | cluster | n   | silhouette_mean | silhouette_median | negative_share |
| - | ------- | --- | --------------- | ----------------- | -------------- |
| 5 | 0       | 122 | 0.045           | 0.045             | 0.336          |
| 5 | 1       | 25  | 0.001           | -0.005            | 0.520          |
| 5 | 2       | 12  | -0.245          | -0.251            | 1.000          |
| 5 | 3       | 163 | 0.219           | 0.227             | 0.006          |
| 5 | 4       | 82  | 0.035           | 0.033             | 0.476          |
| 6 | 0       | 29  | 0.019           | 0.010             | 0.310          |
| 6 | 1       | 12  | -0.135          | -0.093            | 0.833          |
| 6 | 2       | 76  | 0.063           | 0.060             | 0.237          |
| 6 | 3       | 72  | 0.039           | 0.040             | 0.361          |
| 6 | 4       | 52  | 0.057           | 0.050             | 0.365          |
| 6 | 5       | 163 | 0.199           | 0.198             | 0.012          |

## Interpretation rules

1. Bootstrap measures resampling recurrence, not the probability a given K is correct.
2. Random-seed stability measures optimisation sensitivity; it is a distinct concept.
3. This is the same methodology as `rail_k_selection_validation` (canonical
   270 stations, K=5 vs K=6) applied to a different station scope --
   numbers are not directly comparable across the two reports (different
   station counts and feature distributions); read each within its own scope.

## Limitations

- Conditional on the current 344-dim features, normalisation, GMM family, and diagonal covariance.
- 134 of the 404 stations here were only added in this extension
  check and have not had the same manual review as the canonical 270,
  though the 13 co-located cross-mode sites have been merged via
  `01b_merge_colocated_stations.py`.
- Stability does not by itself confer urban-functional or socio-economic meaning on a cluster.

## Reproduction

```
python src/07_stability_allmodes.py
```
