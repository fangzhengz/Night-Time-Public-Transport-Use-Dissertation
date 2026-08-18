## Material Passport

- Origin: `numbat_all_area_test` extension check -- stability battery (K=5 vs K=6)
- Generated: 2026-08-07T04:37:00.750218+00:00
- Verification status: checked -- **this is a VALIDATION report, not the official one**
- Retroactive label added: 2026-08-17 (see below); the numbers in this file are unchanged.

> **NOT the official K-selection report.** This is a robustness/validation
> battery comparing the adopted solution against an adjacent candidate; it
> is not the official basis for K selection. Any dissertation text citing
> random-seed ARI, bootstrap ARI, or weakest-cluster Jaccard must use
> `08_k_selection_panel.py`'s `rail_allmodes_k_selection_panel.csv` (the
> official source, matching the main-text figure; K=5 there reads 0.964 /
> 0.510 / 0.301 respectively) -- not the `seed_ARI_mean` / `bootstrap_ARI_mean_200`
> / `weakest_cluster_jaccard` columns below (0.859 / 0.480 / 0.399), which
> measure agreement WITH the saved/adopted labels rather than agreement
> AMONG same-budget seeds/resamples and are therefore numerically different
> from the official figures even though the column names look alike. See
> `numbat_all_area_test/README.md`'s "Interpretation boundary" section.

# All-Modes Rail Clustering: K=5 vs K=6 Internal Stability Check (validation version)

## Scope

This check uses only the 344-dimensional full-week entry/exit feature
matrix for the 403 all-modes stations (LU + DLR + Overground + Elizabeth
line; trams are structurally excluded, see the main comparison report) and
the saved K=5/K=6 labels. This pair checks the adopted solution
against an adjacent candidate as a supplementary robustness check; it does
not replace `08_k_selection_panel.py`'s official result, which remains the
authoritative source for BIC ranking and for the random-seed/bootstrap
stability numbers. Methodology (diag
GMM, bootstrap=200, seed_runs=20) is identical to
`rail_k_selection_validation`.

## Global evidence

| K | BIC_refit    | silhouette | calinski_harabasz | davies_bouldin | bootstrap_ARI_mean_200 | bootstrap_ARI_q025_200 | bootstrap_ARI_q975_200 | weakest_cluster_jaccard | weak_cluster_count | seed_ARI_mean |
| - | ------------ | ---------- | ----------------- | -------------- | ---------------------- | ---------------------- | ---------------------- | ----------------------- | ------------------ | ------------- |
| 5 | -1899714.293 | 0.104      | 44.843            | 2.179          | 0.480                  | 0.277                  | 0.814                  | 0.399                   | 3                  | 0.859         |
| 6 | -1898930.005 | 0.108      | 43.425            | 2.073          | 0.454                  | 0.232                  | 0.701                  | 0.316                   | 5                  | 0.672         |

- BIC difference (K6 minus K5): `784.288`. K=5 has lower (better) refitted BIC than K=6.
- Silhouette difference (K6 minus K5): `0.003818`.
- Paired 200-replicate bootstrap ARI: K=5 = `0.480`,
  K=6 = `0.454`.
- Paired difference K5 minus K6: mean `0.026`,
  95% empirical interval `[-0.349, 0.392]`;
  K=5 is higher in `57.0%` of paired resamples.
- Full-data random-seed mean ARI: K=5 = `0.859`,
  K=6 = `0.672`.

## K=5 to K=6 structure

- Adjusted Rand Index: `0.606`
- Best one-to-one matched stations: `296` /
  `403` (`73.4%`)

| K5_cluster | matched_K6_cluster | intersection | reference_size | candidate_size | jaccard |
| ---------- | ------------------ | ------------ | -------------- | -------------- | ------- |
| 0          | 1                  | 62           | 89             | 69             | 0.646   |
| 1          | 3                  | 13           | 26             | 14             | 0.481   |
| 2          | 0                  | 48           | 90             | 63             | 0.457   |
| 3          | 4                  | 28           | 31             | 28             | 0.903   |
| 4          | 5                  | 145          | 167            | 158            | 0.806   |

## Weak K=6 components under bootstrap

| K6_cluster | jaccard_mean | share_jaccard_below_0_50 |
| ---------- | ------------ | ------------------------ |
| 0          | 0.419        | 0.770                    |
| 1          | 0.475        | 0.550                    |
| 2          | 0.316        | 0.770                    |
| 3          | 0.423        | 0.645                    |
| 4          | 0.495        | 0.490                    |

## Full cluster-level silhouette

| K | cluster | n   | silhouette_mean | silhouette_median | negative_share |
| - | ------- | --- | --------------- | ----------------- | -------------- |
| 5 | 0       | 89  | 0.025           | 0.020             | 0.427          |
| 5 | 1       | 26  | -0.063          | -0.085            | 0.692          |
| 5 | 2       | 90  | 0.026           | 0.033             | 0.422          |
| 5 | 3       | 31  | 0.016           | 0.026             | 0.452          |
| 5 | 4       | 167 | 0.230           | 0.223             | 0.000          |
| 6 | 0       | 63  | 0.057           | 0.054             | 0.381          |
| 6 | 1       | 69  | 0.066           | 0.076             | 0.203          |
| 6 | 2       | 71  | 0.029           | 0.045             | 0.310          |
| 6 | 3       | 14  | -0.020          | -0.001            | 0.500          |
| 6 | 4       | 28  | 0.006           | -0.002            | 0.500          |
| 6 | 5       | 158 | 0.211           | 0.213             | 0.013          |

## Interpretation rules

1. Bootstrap measures resampling recurrence, not the probability a given K is correct.
2. Random-seed stability measures optimisation sensitivity; it is a distinct concept.
3. This is the same methodology as `rail_k_selection_validation` (canonical
   270 stations, K=5 vs K=6) applied to a different station scope --
   numbers are not directly comparable across the two reports (different
   station counts and feature distributions); read each within its own scope.

## Limitations

- Conditional on the current 344-dim features, normalisation, GMM family, and diagonal covariance.
- 133 of the 403 stations here were only added in this extension
  check and have not had the same manual review as the canonical 270,
  though the 14 co-located cross-mode sites have been merged via
  `01b_merge_colocated_stations.py`.
- Stability does not by itself confer urban-functional or socio-economic meaning on a cluster.

## Reproduction

```
python src/07_stability_allmodes.py
```
