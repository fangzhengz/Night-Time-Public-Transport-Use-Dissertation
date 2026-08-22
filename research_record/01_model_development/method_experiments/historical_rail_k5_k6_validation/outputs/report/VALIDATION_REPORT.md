## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run + validate
- Origin Date: 2026-07-19T21:51:19.104672+00:00
- Verification Status: VERIFIED
- Version Label: rail_k_selection_validation_v1

# Rail K=5 versus K=6 Validation Report

## Scope and decision boundary

This audit uses only the 344-dimensional full-week entry/exit temporal feature
matrix and the saved K=5/K=6 labels. LNWC, IMD, catchment composition, and other
downstream interpretation variables are excluded from model selection. Station
names are audit identifiers only.

## Verdict

**On balance, the internal evidence supports retaining K=5 as the primary parsimonious typology within the current feature engineering and diagonal-GMM design, but the preference is not decisive. K=6 remains the BIC-preferred density model and is more stable across full-data random-seed refits; K=5 has higher mean station-resampling stability, while K=6 contains two weakly recurring components and does not improve separation.**

This is not a claim that K=5 is the true natural number of station types. It is
a bounded model-selection judgment conditional on the current inputs, GMM
family, diagonal covariance, and feature normalization.

## Global evidence

| K | BIC_refit   | silhouette | calinski_harabasz | davies_bouldin | bootstrap_ARI_mean_200 | bootstrap_ARI_q025_200 | bootstrap_ARI_q975_200 | weakest_cluster_jaccard | weak_cluster_count | seed_ARI_mean |
| - | ----------- | ---------- | ----------------- | -------------- | ---------------------- | ---------------------- | ---------------------- | ----------------------- | ------------------ | ------------- |
| 5 | -974893.293 | 0.142      | 51.247            | 1.792          | 0.630                  | 0.316                  | 0.873                  | 0.579                   | 0                  | 0.714         |
| 6 | -975013.528 | 0.141      | 48.226            | 1.824          | 0.562                  | 0.325                  | 0.781                  | 0.391                   | 2                  | 0.810         |

The refitted BIC difference (K=6 minus K=5) is
`-120.235`; lower BIC favors K=6. The global
silhouette difference is `-0.000215`, which is
below the protocol's 0.01 material-improvement description. Paired 200-replicate
bootstrap ARI is `0.630` for K=5 and
`0.562` for K=6. The paired difference
`K5 - K6` has mean `0.068` and a 95%
empirical interval from `-0.377` to
`0.450`; K=5 is higher in
`66.0%` of paired resamples. Because the
interval crosses zero, this is directional rather than decisive evidence.

## K=5 to K=6 structure

- Adjusted Rand Index: `0.770`
- Best one-to-one matched stations: `221` /
  `270` (`81.9%`)

| K5_cluster | matched_K6_cluster | intersection | reference_size | candidate_size | jaccard |
| ---------- | ------------------ | ------------ | -------------- | -------------- | ------- |
| 0          | 2                  | 111          | 119            | 113            | 0.917   |
| 1          | 4                  | 11           | 15             | 19             | 0.478   |
| 2          | 0                  | 30           | 44             | 51             | 0.462   |
| 3          | 3                  | 21           | 38             | 21             | 0.553   |
| 4          | 1                  | 48           | 54             | 49             | 0.873   |

The relationship is therefore assessed from the full transition table rather
than described as a single clean nested split.

## Weak K=6 components under bootstrap

| K6_cluster | jaccard_mean | share_jaccard_below_0_50 |
| ---------- | ------------ | ------------------------ |
| 0          | 0.437        | 0.600                    |
| 5          | 0.391        | 0.680                    |

For comparison, the complete cluster-level distributions are stored in
`../data/bootstrap_cluster_stability_summary.csv`. A low matched Jaccard means
that component membership changes, merges, or fragments across resamples.

## Cluster separation warning

| K | cluster | n   | silhouette_mean | silhouette_median | negative_share |
| - | ------- | --- | --------------- | ----------------- | -------------- |
| 5 | 0       | 119 | 0.218           | 0.237             | 0.025          |
| 5 | 1       | 15  | 0.108           | 0.165             | 0.333          |
| 5 | 2       | 44  | 0.117           | 0.122             | 0.114          |
| 5 | 3       | 38  | 0.142           | 0.149             | 0.237          |
| 5 | 4       | 54  | 0.004           | -0.002            | 0.519          |
| 6 | 0       | 51  | 0.117           | 0.117             | 0.157          |
| 6 | 1       | 49  | 0.023           | 0.005             | 0.429          |
| 6 | 2       | 113 | 0.205           | 0.209             | 0.009          |
| 6 | 3       | 21  | 0.260           | 0.259             | 0.048          |
| 6 | 4       | 19  | 0.137           | 0.100             | 0.211          |
| 6 | 5       | 17  | -0.008          | -0.001            | 0.529          |

Posterior probabilities are not used as evidence of stability because a fitted
high-dimensional GMM can assign extreme posterior probabilities even when
between-cluster separation or resampling recurrence is weak.

## Random-seed stability

| K | reference_cluster | jaccard_mean | jaccard_min | share_exact_jaccard_1 |
| - | ----------------- | ------------ | ----------- | --------------------- |
| 5 | 0                 | 0.821        | 0.759       | 0.050                 |
| 5 | 1                 | 0.584        | 0.458       | 0.100                 |
| 5 | 2                 | 0.638        | 0.277       | 0.000                 |
| 5 | 3                 | 0.718        | 0.517       | 0.100                 |
| 5 | 4                 | 0.791        | 0.704       | 0.000                 |
| 6 | 0                 | 0.759        | 0.276       | 0.000                 |
| 6 | 1                 | 0.865        | 0.686       | 0.050                 |
| 6 | 2                 | 0.881        | 0.642       | 0.000                 |
| 6 | 3                 | 0.844        | 0.500       | 0.100                 |
| 6 | 4                 | 0.890        | 0.550       | 0.500                 |
| 6 | 5                 | 0.843        | 0.400       | 0.400                 |

This checks optimization sensitivity on the full dataset and is distinct from
bootstrap sampling sensitivity. K=6 has the higher mean full-data seed ARI
(`0.810` versus `0.714`), so the evidence
does not support claiming that K=5 is superior under every stability concept.

## Interpretation rules

1. BIC is reported accurately and is not relabelled as supporting K=5.
2. LNWC/IMD agreement is not used to choose K.
3. Small size alone is not grounds for rejecting a component.
4. A proposed sixth type must show recurrence and separation, not only a
   post-hoc narrative.
5. K=5 should be described as a parsimonious primary typology, with K=6 as the
   BIC-preferred sensitivity solution.

## Fallacy scan

- Coverage: 11/11 checked.
- Garden of forking paths / look-elsewhere: controlled by reporting both K and
  prespecifying the internal evidence order.
- Ecological fallacy: LNWC/IMD and area interpretation are excluded here.
- Correlation/causation and reverse causality: no causal claim is made.
- Simpson's paradox, Berkson's paradox, collider bias, base-rate neglect,
  regression to the mean, and survivorship bias were not triggered by this
  resampling comparison.

## Reproducibility and limits

- Saved labels were refitted with the original seed and hyperparameters.
- Full input hashes and package versions are in `RUN_METADATA.json`.
- The bootstrap resamples stations and is conditional on the existing 344
  features and diagonal-GMM family.
- Cluster stability does not establish functional or socio-economic meaning.
