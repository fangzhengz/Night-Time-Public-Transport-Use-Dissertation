# Independent area-context variables — results

Two layers, answering two different questions:

* **Layer 1 (script 02) — which variables matter.** One omnibus
  Kruskal-Wallis per variable per mode, reported as epsilon-squared, so the
  variables can be *ranked*. The reference literature does not do this:
  BtC reports significance stars without effect sizes, and Kimani's MSc
  dissertation reports descriptive profiles with no hypothesis test at all.
* **Layer 2 (script 03) — what each cluster looks like.** Cluster-vs-rest
  Mann-Whitney per cell, BH-corrected, which is the K x V matrix the
  literature does report, and what cluster naming rests on.

Neither replaces the other. Layer 1 without Layer 2 cannot describe a
cluster; Layer 2 without Layer 1 is a wall of asterisks with no ordering.

## Layer 1 — variable ranking (epsilon-squared)

| Variable | Bus | Rail |
|---|---:|---:|
| no_car_household_share | 0.217 | 0.420 |
| age_20_34_share | 0.172 | 0.365 |
| log1p_poi_count | 0.152 | 0.257 |
| private_rented_share | 0.146 | 0.263 |
| accom_food_share | 0.104 | 0.133 |
| dependent_children_share | 0.060 | 0.332 |
| unemployed_share | 0.050 | 0.092 |
| population_density *(control)* | 0.049 | 0.232 |
| shannon_group | 0.047 | 0.071 |
| imd_health | 0.038 | 0.110 |
| social_rented_share | 0.037 | 0.147 |
| black_share | 0.021 | 0.051 |
| deprived_1plus_share | 0.019 | 0.019 |
| transport_storage_share | 0.016 | 0.170 |
| admin_support_share | 0.013 | 0.115 |
| imd_education | 0.013 | 0.027 |
| manufacturing_share | 0.012 | 0.132 |
| health_social_share | 0.010 | 0.118 |
| wholesale_retail_share | 0.010 | 0.093 |
| asian_share | 0.009 | 0.014 |

Conventional epsilon-squared benchmarks: 0.01 small, 0.06 medium, 0.14 large.

For comparison, the composite lenses on the same clusterings — note these are
Cramer's V, a *different* statistic, so they rank among themselves but cannot
be placed on the epsilon-squared scale above:

| Composite | Bus | Rail |
|---|---:|---:|
| LNWC (night-work geography) | V = 0.253 | V = 0.405 |
| LOAC (general neighbourhood type) | V = 0.223 | V = 0.321 |
| IMD overall score | eps² = 0.060 | eps² = 0.059 |

## Layer 2 — cluster profiles

### BUS — 66/80 cells significant after BH (82%)

**C0 low activity, weak night-persistence** — low no_car_household_share (-0.60); low private_rented_share (-0.50); low age_20_34_share (-0.48); low log1p_poi_count (-0.42); low accom_food_share (-0.38)

**C1 relatively high activity, stronger night-persistence** — high no_car_household_share (+0.61); high log1p_poi_count (+0.54); high age_20_34_share (+0.50); high private_rented_share (+0.49); high accom_food_share (+0.43)

**C2 moderate activity and persistence, transitional** — low log1p_poi_count (-0.18); low deprived_1plus_share (-0.16); low admin_support_share (-0.16); low black_share (-0.14); low imd_education (-0.14)

**C3 moderate activity with destination characteristics** — low no_car_household_share (-0.37); low private_rented_share (-0.33); low log1p_poi_count (-0.30); low age_20_34_share (-0.29); low accom_food_share (-0.24)

Strongest 8 cells in the bus matrix:

| Cluster | Variable | z | rank-biserial | BH p |
|---|---|---:|---:|---:|
| C1 relatively high activity, stronger night-persistence | no_car_household_share | +0.61 | +0.532 | 2.28e-139 |
| C0 low activity, weak night-persistence | no_car_household_share | -0.60 | -0.422 | 2.46e-58 |
| C1 relatively high activity, stronger night-persistence | log1p_poi_count | +0.54 | +0.465 | 5.47e-107 |
| C1 relatively high activity, stronger night-persistence | age_20_34_share | +0.50 | +0.478 | 1.46e-112 |
| C0 low activity, weak night-persistence | private_rented_share | -0.50 | -0.354 | 2.41e-41 |
| C1 relatively high activity, stronger night-persistence | private_rented_share | +0.49 | +0.427 | 3.01e-90 |
| C0 low activity, weak night-persistence | age_20_34_share | -0.48 | -0.375 | 2.66e-46 |
| C1 relatively high activity, stronger night-persistence | accom_food_share | +0.43 | +0.378 | 6.17e-71 |

### RAIL — 63/100 cells significant after BH (63%)

**C0 outer arrival-oriented** — low no_car_household_share (-1.11); low age_20_34_share (-0.98); low private_rented_share (-0.93); high dependent_children_share (+0.82); low accom_food_share (-0.68)

**C1 central departure-oriented** — high log1p_poi_count (+2.34); low dependent_children_share (-1.43); high private_rented_share (+1.21); low health_social_share (-1.10); high no_car_household_share (+1.02)

**C2 central interchange, direction-balanced** — high no_car_household_share (+0.64); low dependent_children_share (-0.58); high age_20_34_share (+0.46); low transport_storage_share (-0.44); high log1p_poi_count (+0.42)

**C3 late-night, extended-duration persistent** — high imd_health (+0.75); high age_20_34_share (+0.74); high unemployed_share (+0.74); high social_rented_share (+0.74); high accom_food_share (+0.69)

**C4 inner–middle ring mixed** — low log1p_poi_count (-0.36); high dependent_children_share (+0.18); high admin_support_share (+0.17); high unemployed_share (+0.17); high accom_food_share (+0.14)

Strongest 8 cells in the rail matrix:

| Cluster | Variable | z | rank-biserial | BH p |
|---|---|---:|---:|---:|
| C1 central departure-oriented | log1p_poi_count | +2.34 | +0.790 | 1.86e-10 |
| C1 central departure-oriented | dependent_children_share | -1.43 | -0.740 | 2.69e-09 |
| C1 central departure-oriented | private_rented_share | +1.21 | +0.642 | 2.70e-07 |
| C0 outer arrival-oriented | no_car_household_share | -1.11 | -0.762 | 1.13e-22 |
| C1 central departure-oriented | health_social_share | -1.10 | -0.601 | 1.53e-06 |
| C1 central departure-oriented | no_car_household_share | +1.02 | +0.672 | 8.15e-08 |
| C1 central departure-oriented | age_20_34_share | +1.00 | +0.571 | 5.02e-06 |
| C0 outer arrival-oriented | age_20_34_share | -0.98 | -0.754 | 1.78e-22 |

## Method notes

* **Cluster vs rest, not cluster vs overall.** A one-sample test of a cluster
  mean against the overall mean compares a sample with a population that
  contains it; the two are not independent. Cluster-vs-rest avoids this.
* **Mann-Whitney, not t.** The variables include bounded rates and
  skewed facility counts or employment shares.
* **Benjamini-Hochberg across all cells within a mode.** Bus runs 4 x 20 = 80 tests and rail 5 x 20 = 100; uncorrected, a handful per mode would clear p<0.05 by chance alone.
* **Rail units are 800 m Voronoi-clipped station catchments**, LSOA values
  aggregated as an equal-weight arithmetic mean across distinct intersecting
  LSOAs. This avoids applying one population weight to variables with different
  denominators (households, residents and employed residents). The values
  characterise average LSOA context, not exact catchment population composition.
  Bus units are LSOAs directly — the bus clustering is already at LSOA level.
  POI count and Shannon H are first calculated at LSOA level; Rail then uses
  the same equal-weight catchment aggregation. Count is log1p-transformed
  after Rail aggregation.

## Known limitations

1. **Context, not passenger identity or supply.** The variables describe the
   residential, employment and facility context of an area; none identifies
   passengers or measures what night service is provided. No claim about service
   gaps can rest on this analysis.
2. **Vintage mixing.** Transport data is 2024/25, IoD 2025 is administrative
   data from roughly 2022-24, BRES is 2024, but the Census variables are March
   2021 — taken during a national lockdown and three years before the travel
   data — while OS POI is the June 2026 release.
3. **BRES is the open-access release**, not the secure-access version BtC uses;
   values are rounded to multiples of 5. Job counts per LSOA range 0 to 412,000
   (median 300), so BRES *shares* are unstable in the ~40% of LSOAs with under
   250 jobs. A per-km2 twin of every BRES variable is stored in
   `data/bres2024_industry_sections_lsoa.csv`; which denominator to use is not
   yet settled.
4. **Collinearity.** Some variables are near-duplicates in this data even though
   not by construction — imd_education and deprived_1plus_share (TS011) at
   rho 0.89-0.92, imd_health and social_rented_share at rho 0.81-0.88 — plus the
   TS060 sections are compositionally related shares of the same 18-section total.
   See the correlation matrices (rho > 0.8 flagged); these pairs are the same
   signal counted more than once, not independent evidence. One pair is kept
   deliberately despite rho 0.81-0.89 — no_car_household_share (TS045) and
   age_20_34_share (TS007B) are two independently-sourced Census measures of the
   same young/carless profile; because Layer 1 and Layer 2 test each variable
   separately rather than fitting a joint model, both scoring highly on the same
   clusters is corroborating evidence from two sources, not a violated
   independence assumption (the same logic BtC uses when reporting age and car
   ownership as separate cluster-level indicators).
5. **Bivariate throughout.** Every test here takes one variable at a time. How
   much of cluster membership is explainable in total, and which variables
   contribute uniquely once the others are held constant, would need a
   multivariable model (as in Yang et al. 2023's random-forest importance).
6. **Centrality is not fully controlled.** Facility intensity and several social
   variables follow London's centre-periphery structure. A separate distance-band
   facility sensitivity check is retained in rq2_facility_diversity_analysis,
   but the main bivariate results remain descriptive spatial associations.

## Figures

* `figures/{bus,rail}_cluster_profile_heatmap.png` — Layer 2, the BtC-style figure.
* `figures/{bus,rail}_boxplots_top8.png` — distributions behind the strongest variables.
* `figures/{bus,rail}_correlation_matrix.png` — how much the 20 variables duplicate.