# Method protocol: Rail ILR sensitivity

## Question

Does the current raw-share Rail K=5 typology remain recognisable and
reproducible when entry and exit temporal profiles are analysed in non-redundant
ILR coordinates after explicit zero handling?

## Fixed factors

1. Station sample, day types, time windows, and temporal bins.
2. Direction-wise full-week normalization concept.
3. GMM random state 42, `n_init=20`, `reg_covar=1e-6`, and `max_iter=300`.
4. Diagonal covariance as the primary comparison family.
5. K range 2-12; stability reported for K=3-8.
6. LNWC, IMD, geography, station volume, and downstream interpretation are
   excluded from model selection.

## Changed factor

Each 172-part entry/exit composition receives an empirical-prior posterior
with `alpha=1`, then a 171-coordinate standard Helmert ILR transform. The two
directions are concatenated into 342 features.

## Evidence order

1. Coordinate audit: positivity, closure, orthonormal basis, and preservation
   of CLR/Aitchison distances.
2. Same-K label agreement: ARI, NMI, best one-to-one match, and cluster Jaccard
   for raw versus ILR K=5 (and K=6 as a secondary comparison).
3. Internal separation: silhouette, Calinski-Harabasz, Davies-Bouldin, and
   cluster sizes for diagonal-GMM K=2-12.
4. Station bootstrap: 200 paired resamples for K=3-8, predicting all original
   stations and matching clusters by maximum Jaccard overlap.
5. Full-data seed sensitivity: 20 refits for K=3-8.
6. Four-covariance BIC grid as a secondary model-family diagnostic.

## Operational interpretation bands

These are transparent audit rules rather than universal thresholds:

- raw/ILR label agreement is strong when ARI and NMI are both at least 0.80,
  best-match share is at least 0.85, and no matched raw K=5 cluster has Jaccard
  below 0.50;
- agreement is partial when ARI is at least 0.65 but the strong rule is not met;
- cluster recurrence is weak below mean matched Jaccard 0.50, moderate from
  0.50 to below 0.75, and strong at or above 0.75;
- bootstrap global recurrence of the ILR K=5 solution is treated as acceptable
  for this audit when mean ARI is at least 0.60 and every cluster has mean
  matched Jaccard at least 0.50;
- silhouette differences below 0.01 are described as no material improvement.

## Decision boundary

The test may support, partially support, or challenge the robustness of the
current K=5 typology. It cannot identify a true natural K, prove functional
station types, or establish that Rail/Bus differences are caused by transport
mode alone.
