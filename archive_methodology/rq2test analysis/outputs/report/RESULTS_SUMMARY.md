# RQ2 LNWC baseline — provisional results

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-07-24T01:23:57.858540+00:00
- Verification Status: ANALYZED
- Version Label: rq2_lnwc_baseline_v1

## Scope

- Rail: provisional K=5; 1200 m Voronoi-clipped catchments.
- Bus: provisional K=3; direct LSOA-to-LNWC join.
- LNWC is treated as area context, not as passenger-level characteristics.

## Coverage

- Bus LNWC match: 4100/4100 (100.0%).
- Rail stations eligible for LNWC analysis: 254/270; 16 station points are outside the LNWC extent.
- Mean rail catchment LNWC coverage ratio: 0.980.
- Eligibility is uneven: rail Cluster 4 has the lowest inclusion rate (72.2%), so its LNWC composition does not represent the full RQ1 cluster.

## Exploratory association statistics

- Bus cluster × LNWC: chi-square=380.30, Cramer's V=0.215, n=4100.
- Rail dominant-LNWC cross-tab: chi-square=199.01, Cramer's V=0.443, n=254.
- Rail seven-part composition: permutation R²=0.311, p=0.0010 (999 permutations).

These tests are exploratory. The bus chi-square test does not account for spatial autocorrelation, and the rail dominant-category test discards composition detail.

## Highest enrichment ratios by cluster

### Bus

- Cluster 0: LNWC 1, ratio 1.31.
- Cluster 0: LNWC 3, ratio 1.17.
- Cluster 1: LNWC 1, ratio 1.21.
- Cluster 1: LNWC 2, ratio 1.16.
- Cluster 2: LNWC 7, ratio 2.53.
- Cluster 2: LNWC 6, ratio 1.41.

### Rail

- Cluster 0: LNWC 4, ratio 1.38.
- Cluster 0: LNWC 5, ratio 1.34.
- Cluster 1: LNWC 1, ratio 2.17.
- Cluster 1: LNWC 3, ratio 2.15.
- Cluster 2: LNWC 1, ratio 1.60.
- Cluster 2: LNWC 2, ratio 1.50.
- Cluster 3: LNWC 1, ratio 3.21.
- Cluster 3: LNWC 2, ratio 0.70.
- Cluster 4: LNWC 7, ratio 3.70.
- Cluster 4: LNWC 6, ratio 2.69.

## Interpretation limits and next validation gate

1. Cluster numbers are arbitrary labels and need profile-based names before substantive interpretation.
2. Repeat rail analysis with 800 m Voronoi and station-containing LSOA definitions.
3. Repeat for plausible neighbouring K values before treating any enrichment as stable.
4. Retain equal-station weighting as primary and activity weighting as a secondary service-intensity view.