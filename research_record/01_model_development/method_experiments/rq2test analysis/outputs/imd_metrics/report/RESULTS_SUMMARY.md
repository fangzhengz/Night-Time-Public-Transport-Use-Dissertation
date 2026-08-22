# RQ2 IMD extension -- provisional results

## Material Passport

- Origin Mode: run
- Origin Date: 2026-07-14T18:41:58.582211+00:00
- Verification Status: ANALYZED
- Version Label: rq2_imd_extension_v1

## Design

- IMD 2019 (File 7), joined 2011->2021 LSOA via ONS best-fit lookup (population-weighted for the 22 merged cells; 181 newly-split 2021 LSOAs with no 2011 source are excluded).
- IMD is an independent socio-economic lens, parallel to LNWC (per Mikaella's guidance): not fused into the RQ1 cluster typology, not used as a covariate competing with LNWC.
- Weak line: does IMD score differ across RQ1 shape clusters (Kruskal-Wallis).
- Main line: do continuous context metrics vary with IMD, controlling for distance to Charing Cross (Freedman-Lane permutation, mirroring the LNWC centrality test).

## Coverage

- Bus: 3965/4100 LSOAs matched to IMD (96.7%).
- Rail: 254/270 stations eligible for both LNWC-extent and IMD analysis (LNWC-eligible alone: 254; IMD-matched alone: 257).

## Weak line: RQ1 cluster vs IMD score (Kruskal-Wallis)

- bus cluster -> imd_score: H=160.16, epsilon²=0.040, BH-adjusted p=1.666e-35.
- rail cluster -> imd_score: H=30.93, epsilon²=0.108, BH-adjusted p=3.159e-06.

## Main line: continuous metrics by IMD decile (bus, Kruskal-Wallis)

- `log_total_activity`: H=343.57, epsilon²=0.085, BH-adjusted p=2.891e-68.
- `post_midnight_share`: H=575.38, epsilon²=0.143, BH-adjusted p=1.606e-117.
- `direction_balance`: H=16.83, epsilon²=0.002, BH-adjusted p=0.05139.
- `weekend_ratio`: H=178.12, epsilon²=0.043, BH-adjusted p=1.666e-33.

## Centrality-adjusted exploratory omnibus tests (IMD score, partial R² beyond distance)

- bus `log_total_activity`: partial R²=0.036, Freedman-Lane p=0.0010, BH-adjusted p=0.0010, Spearman r (raw, unadjusted)=0.255.
- bus `post_midnight_share`: partial R²=0.081, Freedman-Lane p=0.0010, BH-adjusted p=0.0010, Spearman r (raw, unadjusted)=0.359.
- bus `direction_balance`: partial R²=0.004, Freedman-Lane p=0.0010, BH-adjusted p=0.0010, Spearman r (raw, unadjusted)=-0.040.
- bus `weekend_ratio`: partial R²=0.010, Freedman-Lane p=0.0010, BH-adjusted p=0.0010, Spearman r (raw, unadjusted)=0.202.
- rail `log_total_activity`: partial R²=0.011, Freedman-Lane p=0.0990, BH-adjusted p=0.1320, Spearman r (raw, unadjusted)=0.259.
- rail `night_tube_extension_share`: partial R²=0.007, Freedman-Lane p=0.2030, BH-adjusted p=0.2030, Spearman r (raw, unadjusted)=0.037.
- rail `direction_balance`: partial R²=0.033, Freedman-Lane p=0.0040, BH-adjusted p=0.0080, Spearman r (raw, unadjusted)=0.138.
- rail `weekend_common_ratio`: partial R²=0.047, Freedman-Lane p=0.0010, BH-adjusted p=0.0040, Spearman r (raw, unadjusted)=0.297.

## Interpretation boundary

- STATUS (2026-07-14): the 'Main line' centrality-adjusted partial-R^2 results above are PROVISIONAL, not a primary RQ2 result -- they pool all stations/LSOAs regardless of RQ1 cluster and cannot say which cluster type drives the relationship. A new method is pending. The 'Weak line' (cluster vs IMD score) is unaffected and remains a kept, primary result.
- IMD describes the deprivation profile of resident/surrounding populations, not the transport users themselves.
- Rail IMD is an area-weighted average of the 1,200 m Voronoi-clipped catchment; restricted to the same LNWC-eligible station set used in the RQ2 baseline for comparability.
- Distance to centre is the only confounder modelled; spatial autocorrelation is not addressed.