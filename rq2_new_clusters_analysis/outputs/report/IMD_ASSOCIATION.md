# RQ2 sensitivity clusters -- IMD2025 weak-line association

## Material Passport

- Origin Date: 2026-08-08T16:56:09.719927+00:00
- Verification Status: ANALYZED
- Version Label: rq2_new_clusters_imd_v1

## Design

- IMD 2025 (MHCLG, 2025-10), natively on 2021 LSOA boundaries -- same source as the canonical pipeline's IMD2025 refresh.
- Weak line only: does IMD score differ across sensitivity clusters (Kruskal-Wallis). The pooled 'main line' continuous-metric x IMD test is intentionally not reproduced here -- it is cluster-blind by design and was not part of the user's current report version either.
- Rail IMD is the equal-weight average across distinct intersecting LSOAs (one vote per LSOA, not weighted by overlap area), using the same 800 m Voronoi-clipped catchments built in run_lnwc_analysis.py (403-station all-modes geometry, not the canonical 270-station one). Changed 2026-08-08 from a previous 1,200 m, area-weighted design to match rq2_independent_variables and rq2_loac_analysis.

## Coverage

- Bus: 3383/3383 LSOAs matched to IMD (100.0%).
- Rail: 387/403 stations eligible for both LNWC-extent and IMD analysis (LNWC-eligible alone: 387; IMD-matched alone: 389).

## Weak line: cluster vs IMD score (Kruskal-Wallis)

- bus cluster -> imd_score: H=204.16, epsilon2=0.060, BH-adjusted p=5.326e-44.
- rail cluster -> imd_score: H=26.40, epsilon2=0.059, BH-adjusted p=2.632e-05.

## Interpretation boundary

- IMD describes the deprivation profile of resident/surrounding populations, not the transport users themselves.
- Distance-to-centre is not modelled here (that belongs to the pooled main-line design, which is deliberately excluded).
- Compare against the canonical weak-line numbers via the combined report, not in isolation.