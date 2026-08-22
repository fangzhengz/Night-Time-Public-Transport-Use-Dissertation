# RQ2 IMD extension (IMD2025, 800 m rail catchment sensitivity) -- provisional results

## Material Passport

- Origin Mode: run
- Origin Date: 2026-07-24T01:09:51.282246+00:00
- Verification Status: ANALYZED
- Version Label: rq2_imd_extension_v2_imd2025_800m

## Design

- Same design as the 1200 m canonical run (outputs/imd_metrics_2025/report/RESULTS_SUMMARY.md); only the rail catchment radius differs (800 m vs 1200 m Voronoi-clipped station buffers). Bus is catchment-independent (direct LSOA join) and is unaffected.
- IMD is an independent socio-economic lens, parallel to LNWC (per Mikaella's guidance): not fused into the RQ1 cluster typology, not used as a covariate competing with LNWC.
- Weak line: does IMD score differ across RQ1 shape clusters (Kruskal-Wallis).
- Main line: do continuous context metrics vary with IMD, controlling for distance to Charing Cross (Freedman-Lane permutation, mirroring the LNWC centrality test).

## Coverage

- Bus: 4100/4100 LSOAs matched to IMD (100.0%).
- Rail: 254/270 stations eligible for both LNWC-extent and IMD analysis (LNWC-eligible alone: 254; IMD-matched alone: 256).

## Weak line: RQ1 cluster vs IMD score (Kruskal-Wallis)

- bus cluster -> imd_score: H=206.06, epsilon²=0.050, BH-adjusted p=1.801e-45.
- rail cluster -> imd_score: H=33.29, epsilon²=0.118, BH-adjusted p=1.041e-06.

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
- rail `log_total_activity`: partial R²=0.007, Freedman-Lane p=0.1800, BH-adjusted p=0.1800, Spearman r (raw, unadjusted)=0.145.
- rail `night_tube_extension_share`: partial R²=0.011, Freedman-Lane p=0.1020, BH-adjusted p=0.1360, Spearman r (raw, unadjusted)=0.080.
- rail `direction_balance`: partial R²=0.020, Freedman-Lane p=0.0270, BH-adjusted p=0.0540, Spearman r (raw, unadjusted)=0.028.
- rail `weekend_common_ratio`: partial R²=0.060, Freedman-Lane p=0.0010, BH-adjusted p=0.0040, Spearman r (raw, unadjusted)=0.283.

## Interpretation boundary

- STATUS: the 'Main line' centrality-adjusted partial-R^2 results above are PROVISIONAL, not a primary RQ2 result -- same pooled-design caveat as the 1200 m canonical run, unrelated to the catchment radius change. The 'Weak line' (cluster vs IMD score) is the primary comparison of interest for this 800 m sensitivity check.
- IMD describes the deprivation profile of resident/surrounding populations, not the transport users themselves.
- Rail IMD is an area-weighted average of the 800 m Voronoi-clipped catchment (sensitivity variant); restricted to the same LNWC-eligible station set used in the 800 m RQ2 baseline for comparability.
- Distance to centre is the only confounder modelled; spatial autocorrelation is not addressed.