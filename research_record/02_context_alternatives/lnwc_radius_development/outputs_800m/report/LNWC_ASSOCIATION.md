# RQ2 sensitivity clusters -- LNWC association (800 m catchment sidecar)

## Material Passport

- Origin Date: 2026-08-14T16:23:34.095220+00:00
- Verification Status: ANALYZED
- Version Label: rq2_new_clusters_lnwc_800m_v1

## Scope

- Rail: all-modes merged sensitivity clustering K=5; 800 m Voronoi-clipped catchments rebuilt over all 403 stations (sensitivity variant of this folder's own 1200 m run in outputs/report/LNWC_ASSOCIATION.md).
- Bus: StopArea CLR sensitivity clustering K=4; direct LSOA-to-LNWC join (catchment-independent, identical to the 1200 m run).
- LNWC is treated as area context, not as passenger-level characteristics.

## Coverage

- Bus LNWC match: 3383/3383 (100.0%).
- Rail: 0 stations excluded for no NaPTAN coordinate match (outside Greater London extract); 389/403 eligible for LNWC analysis; 16 station points outside the LNWC extent.
- Mean rail catchment LNWC coverage ratio: 0.973.

## Exploratory association statistics

- Bus cluster x LNWC: chi-square=647.50, Cramer's V=0.253, n=3383.
- Rail dominant-LNWC cross-tab: chi-square=224.60, Cramer's V=0.380, n=389.
- Rail seven-part composition: permutation R2=0.205, p=0.0010 (999 permutations).

## Highest enrichment ratios by cluster

### Bus

- Cluster 0: LNWC 7, ratio 2.36.
- Cluster 0: LNWC 6, ratio 1.61.
- Cluster 1: LNWC 1, ratio 2.02.
- Cluster 1: LNWC 2, ratio 1.62.
- Cluster 2: LNWC 6, ratio 1.16.
- Cluster 2: LNWC 5, ratio 1.15.
- Cluster 3: LNWC 6, ratio 1.39.
- Cluster 3: LNWC 7, ratio 1.36.

### Rail

- Cluster 0: LNWC 7, ratio 3.19.
- Cluster 0: LNWC 6, ratio 2.80.
- Cluster 1: LNWC 1, ratio 3.85.
- Cluster 1: LNWC 3, ratio 1.17.
- Cluster 2: LNWC 1, ratio 2.03.
- Cluster 2: LNWC 2, ratio 1.24.
- Cluster 3: LNWC 2, ratio 1.62.
- Cluster 3: LNWC 3, ratio 1.35.
- Cluster 4: LNWC 4, ratio 1.28.
- Cluster 4: LNWC 5, ratio 1.15.

## Interpretation limits

- Cluster numbers are arbitrary labels; compare against the canonical rail-K5(270)/bus-K3 numbers using the combined report, not in isolation.
- Ordinary chi-square/permutation tests here ignore spatial autocorrelation.
- Rail catchments use equal-station weighting as primary; activity weighting is a secondary service-intensity view.
- This is the 800 m catchment-radius sensitivity sidecar of this folder's own 1200 m run -- compare directly against outputs/report/LNWC_ASSOCIATION.md.