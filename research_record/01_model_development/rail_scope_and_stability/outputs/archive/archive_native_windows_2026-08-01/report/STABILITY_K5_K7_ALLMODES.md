## Material Passport

- Origin: `numbat_all_area_test` extension check -- stability battery (K=5 vs K=7)
- Generated: 2026-07-29T23:29:34.687939+00:00
- Verification status: checked

# All-Modes Rail Clustering: K=5 vs K=7 Internal Stability Check

## Scope

This check uses only the 344-dimensional full-week entry/exit feature
matrix for the 404 all-modes stations (LU + DLR + Overground + Elizabeth
line; trams are structurally excluded, see the main comparison report) and
the saved K=5/K=7 labels. K=5/K=7 is this
all-modes dataset's own closest BIC pair (see `rail_allmodes_bic_best.txt`)
-- the direct analogue of why the canonical 270-station study chose K=5 vs
K=6 (the two live candidates, not an arbitrary pick). Methodology (diag
GMM, bootstrap=200, seed_runs=20) is identical to
`rail_k_selection_validation`.

## Global evidence

| K | BIC_refit    | silhouette | calinski_harabasz | davies_bouldin | bootstrap_ARI_mean_200 | bootstrap_ARI_q025_200 | bootstrap_ARI_q975_200 | weakest_cluster_jaccard | weak_cluster_count | seed_ARI_mean |
| - | ------------ | ---------- | ----------------- | -------------- | ---------------------- | ---------------------- | ---------------------- | ----------------------- | ------------------ | ------------- |
| 5 | -1446368.898 | 0.102      | 39.357            | 2.641          | 0.500                  | 0.276                  | 0.785                  | 0.288                   | 2                  | 0.894         |
| 7 | -1445623.397 | 0.113      | 43.716            | 2.067          | 0.472                  | 0.259                  | 0.711                  | 0.331                   | 4                  | 0.703         |

- BIC difference (K7 minus K5): `745.501`. K=5 has lower (better) refitted BIC than K=7.
- Silhouette difference (K7 minus K5): `0.011164`.
- Paired 200-replicate bootstrap ARI: K=5 = `0.500`,
  K=7 = `0.472`.
- Paired difference K5 minus K7: mean `0.028`,
  95% empirical interval `[-0.329, 0.384]`;
  K=5 is higher in `56.0%` of paired resamples.
- Full-data random-seed mean ARI: K=5 = `0.894`,
  K=7 = `0.703`.

## K=5 to K=7 structure

- Adjusted Rand Index: `0.581`
- Best one-to-one matched stations: `269` /
  `404` (`66.6%`)

| K5_cluster | matched_K7_cluster | intersection | reference_size | candidate_size | jaccard |
| ---------- | ------------------ | ------------ | -------------- | -------------- | ------- |
| 0          | 2                  | 66           | 122            | 67             | 0.537   |
| 1          | 4                  | 18           | 25             | 21             | 0.643   |
| 2          | 6                  | 6            | 12             | 11             | 0.353   |
| 3          | 1                  | 140          | 163            | 151            | 0.805   |
| 4          | 3                  | 39           | 82             | 60             | 0.379   |

## Weak K=7 components under bootstrap

| K7_cluster | jaccard_mean | share_jaccard_below_0_50 |
| ---------- | ------------ | ------------------------ |
| 3          | 0.400        | 0.660                    |
| 4          | 0.405        | 0.660                    |
| 5          | 0.331        | 0.715                    |
| 6          | 0.434        | 0.650                    |

## Full cluster-level silhouette

| K | cluster | n   | silhouette_mean | silhouette_median | negative_share |
| - | ------- | --- | --------------- | ----------------- | -------------- |
| 5 | 0       | 122 | 0.045           | 0.045             | 0.336          |
| 5 | 1       | 25  | 0.001           | -0.005            | 0.520          |
| 5 | 2       | 12  | -0.245          | -0.251            | 1.000          |
| 5 | 3       | 163 | 0.219           | 0.227             | 0.006          |
| 5 | 4       | 82  | 0.035           | 0.033             | 0.476          |
| 7 | 0       | 30  | 0.158           | 0.176             | 0.167          |
| 7 | 1       | 151 | 0.198           | 0.201             | 0.013          |
| 7 | 2       | 67  | 0.070           | 0.072             | 0.209          |
| 7 | 3       | 60  | 0.097           | 0.111             | 0.217          |
| 7 | 4       | 21  | -0.110          | -0.116            | 0.905          |
| 7 | 5       | 64  | 0.040           | 0.051             | 0.312          |
| 7 | 6       | 11  | 0.032           | 0.024             | 0.364          |

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
