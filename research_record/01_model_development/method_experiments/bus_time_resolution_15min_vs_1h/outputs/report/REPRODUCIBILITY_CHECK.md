# Reproducibility check

- Verification status: VERIFIED for the primary matched-diagonal K=4 comparison.
- Verification date: 2026-07-02.
- Same fixed feature matrices, seeds and ten bootstrap index arrays were used.

The 15-minute and 1-hour K=4 diagonal models were re-fitted after the complete
validation run. The following fields matched the saved results to an absolute
tolerance of `1e-12` for both resolutions:

- common 1-hour-space silhouette;
- mean across-seed ARI;
- mean bootstrap ARI;
- share of LSOAs with bootstrap assignment stability below 0.8;
- LNWC Cramér's V.

The tied-covariance models are retained as a failed sensitivity test because
they produce dominant clusters above 90% and/or clusters smaller than 20 LSOAs.
They are not part of the recommended comparison.
