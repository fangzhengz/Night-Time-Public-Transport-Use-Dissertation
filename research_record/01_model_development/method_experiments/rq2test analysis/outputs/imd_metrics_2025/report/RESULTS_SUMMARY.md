# RQ2 IMD extension (IMD2025 refresh) -- provisional results

## Material Passport

- Origin Mode: run
- Origin Date: 2026-07-24T01:24:47.011735+00:00
- Verification Status: ANALYZED
- Version Label: rq2_imd_extension_v2_imd2025

## Design

- IMD 2025 (MHCLG, released 2025-10; File 7), natively published on 2021 LSOA boundaries -- no ONS best-fit crosswalk needed. All 4,994 Greater London 2021 LSOAs matched directly (0 missing), versus 4,813/4,994 (96.4%) under the IMD2019 crosswalk (see outputs/imd_metrics/ for the superseded IMD2019 run, retained for comparison).
- IMD is an independent socio-economic lens, parallel to LNWC (per Mikaella's guidance): not fused into the RQ1 cluster typology, not used as a covariate competing with LNWC.
- Weak line: does IMD score differ across RQ1 shape clusters (Kruskal-Wallis).
- Main line: do continuous context metrics vary with IMD, controlling for distance to Charing Cross (Freedman-Lane permutation, mirroring the LNWC centrality test).
- Caution: IMD2025 revised 20 of 55 indicators and switched the Income domain from a Before-Housing-Costs to an After-Housing-Costs basis, so IMD2025 scores are not a like-for-like update of IMD2019 scores -- treat cross-version score comparisons with care.

## Coverage

- Bus: 4100/4100 LSOAs matched to IMD (100.0%).
- Rail: 254/270 stations eligible for both LNWC-extent and IMD analysis (LNWC-eligible alone: 254; IMD-matched alone: 257).

## Weak line: RQ1 cluster vs IMD score (Kruskal-Wallis)

- bus cluster -> imd_score: H=206.06, epsilon²=0.050, BH-adjusted p=1.801e-45.
- rail cluster -> imd_score: H=34.58, epsilon²=0.123, BH-adjusted p=5.67e-07.

## Main line: continuous metrics by IMD decile (bus, Kruskal-Wallis)

- `log_total_activity`: H=453.73, epsilon²=0.109, BH-adjusted p=9.131e-92.
- `post_midnight_share`: H=634.77, epsilon²=0.153, BH-adjusted p=2.867e-130.
- `direction_balance`: H=15.22, epsilon²=0.002, BH-adjusted p=0.0852.
- `weekend_ratio`: H=197.26, epsilon²=0.046, BH-adjusted p=1.655e-37.

## Centrality-adjusted exploratory omnibus tests (IMD score, partial R² beyond distance)

- bus `log_total_activity`: partial R²=0.060, Freedman-Lane p=0.0010, BH-adjusted p=0.0013, Spearman r (raw, unadjusted)=0.292.
- bus `post_midnight_share`: partial R²=0.084, Freedman-Lane p=0.0010, BH-adjusted p=0.0013, Spearman r (raw, unadjusted)=0.373.
- bus `direction_balance`: partial R²=0.002, Freedman-Lane p=0.0050, BH-adjusted p=0.0050, Spearman r (raw, unadjusted)=-0.023.
- bus `weekend_ratio`: partial R²=0.013, Freedman-Lane p=0.0010, BH-adjusted p=0.0013, Spearman r (raw, unadjusted)=0.213.
- rail `log_total_activity`: partial R²=0.008, Freedman-Lane p=0.1600, BH-adjusted p=0.1600, Spearman r (raw, unadjusted)=0.159.
- rail `night_tube_extension_share`: partial R²=0.011, Freedman-Lane p=0.0950, BH-adjusted p=0.1267, Spearman r (raw, unadjusted)=0.082.
- rail `direction_balance`: partial R²=0.020, Freedman-Lane p=0.0220, BH-adjusted p=0.0440, Spearman r (raw, unadjusted)=0.041.
- rail `weekend_common_ratio`: partial R²=0.061, Freedman-Lane p=0.0010, BH-adjusted p=0.0040, Spearman r (raw, unadjusted)=0.291.

## Interpretation boundary

- STATUS (2026-07-14): the 'Main line' centrality-adjusted partial-R^2 results above are PROVISIONAL, not a primary RQ2 result -- they pool all stations/LSOAs regardless of RQ1 cluster and cannot say which cluster type drives the relationship. A new method is pending. This status is unchanged from the IMD2019 run; the IMD2025 refresh only changes the deprivation source and coverage, not this design limitation. The 'Weak line' (cluster vs IMD score) is unaffected and remains a kept, primary result.
- IMD describes the deprivation profile of resident/surrounding populations, not the transport users themselves.
- Rail IMD is an area-weighted average of the 1,200 m Voronoi-clipped catchment; restricted to the same LNWC-eligible station set used in the RQ2 baseline for comparability.
- Distance to centre is the only confounder modelled; spatial autocorrelation is not addressed.
- IMD2025 indicator data reference period is closer to the 2024/25 NUMBAT/BUSTO transport data than IMD2019 was, but the two are still not contemporaneous with the LNWC classification build; all results remain area-level associations, not passenger-level or causal claims.