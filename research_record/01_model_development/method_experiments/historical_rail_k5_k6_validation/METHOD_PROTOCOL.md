# Method Protocol: K=5 versus K=6

## Question

Does K=6 add a reproducible sixth temporal-use type, or does it mainly
fragment/reallocate the K=5 solution without improving separation and
stability?

## Evidence order

1. **Reproducibility gate**: refit the same diagonal GMM using the saved seed and
   hyperparameters. Saved and refitted labels must have ARI approximately 1.
2. **Model-fit evidence**: retain BIC as evidence about the fitted density model.
3. **Separation evidence**: compare global and cluster-level silhouette, CH, and
   DB indices using the saved labels.
4. **Structural evidence**: quantify K=5/K=6 overlap, best matching, purity, and
   cross-cluster reallocation.
5. **Resampling evidence**: fit each K on the same 200 bootstrap samples and
   predict all original stations. Match components by maximum Jaccard overlap.
6. **Optimization evidence**: refit the full dataset under 20 random seeds and
   compare each solution with the saved reference.
7. **Parsimony decision**: prefer the additional component only when it adds a
   reproducible and meaningfully separated structure, not merely a lower BIC.

## Operational summaries

For cluster-level Jaccard, the report uses the following descriptive bands:

- `< 0.50`: weak recurrence;
- `0.50 to < 0.75`: moderate recurrence;
- `>= 0.75`: strong recurrence.

These are transparent operational labels for this audit, not universal
statistical significance thresholds.

For global silhouette, a K=6 minus K=5 change smaller than 0.01 is described as
no material improvement for this audit. The raw values are always reported so
the conclusion does not depend on the wording.

## Excluded from K selection

- LNWC and IMD associations;
- station catchment composition;
- downstream RQ2 strength or significance;
- whether a solution more closely resembles an expected CBD/suburban map.

Station name and fare zone are retained only as audit identifiers.

## Limits

- Stations are treated as the resampling units.
- The feature matrix is high-dimensional (270 stations by 344 features).
- The bootstrap evaluates stability conditional on the existing feature
  engineering, GMM family, and diagonal covariance assumption.
- Stability does not establish causal, functional, or socio-economic meaning.
