# RQ2 sensitivity clusters -- IMD2025 weak-line association (800 m catchment sidecar)

## Material Passport

- Origin Date: 2026-08-08T17:16:42.906264+00:00
- Verification Status: ANALYZED
- Version Label: rq2_new_clusters_imd_800m_v1

## Design

- Same design as this folder's own 1200 m run (outputs/report/IMD_ASSOCIATION.md); only the rail catchment radius differs (800 m vs 1200 m Voronoi-clipped station buffers, rebuilt over the same 387-station all-modes refit). Bus is catchment-independent and unaffected.
- Weak line only: does IMD score differ across sensitivity clusters (Kruskal-Wallis). The pooled 'main line' continuous-metric x IMD test is intentionally not reproduced here -- it is cluster-blind by design and was not part of the user's current report version either.
- Rail IMD is the area-weighted average of the 800 m Voronoi-clipped catchments built in run_lnwc_analysis_800m.py.

## Coverage

- Bus: 3383/3383 LSOAs matched to IMD (100.0%).
- Rail: 387/403 stations eligible for both LNWC-extent and IMD analysis (LNWC-eligible alone: 387; IMD-matched alone: 389).

## Weak line: cluster vs IMD score (Kruskal-Wallis)

- bus cluster -> imd_score: H=204.16, epsilon2=0.060, BH-adjusted p=5.326e-44.
- rail cluster -> imd_score: H=21.51, epsilon2=0.046, BH-adjusted p=0.0002513.

## Interpretation boundary

- IMD describes the deprivation profile of resident/surrounding populations, not the transport users themselves.
- Distance-to-centre is not modelled here (that belongs to the pooled main-line design, which is deliberately excluded).
- Compare against this folder's own 1200 m weak-line numbers (outputs/report/IMD_ASSOCIATION.md) and the canonical numbers via the combined report, not in isolation.