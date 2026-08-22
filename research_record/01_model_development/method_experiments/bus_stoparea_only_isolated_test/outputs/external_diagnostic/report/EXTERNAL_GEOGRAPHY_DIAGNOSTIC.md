## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Verification Status: ANALYZED
- Version Label: stoparea_only_external_geography_v1

# StopArea-only external geography diagnostic

- Frozen labelled sample: 3,791 LSOAs.
- K=3 is the provisional primary result; K=4 is sensitivity only.
- Permutations: 999; seed: 42.
- No GMM was refitted and no cluster label was changed.

## Definitions

- Distance is straight-line distance from the LSOA BNG representative coordinate to Charing Cross.
- Inner/Outer follows London Plan 2021 Annex 2 (Greenwich and Newham Inner; Haringey Outer).
- Howard check compares Westminster+Camden with Kingston+Richmond.
- Activity adjustment reports the extra linear R2 from cluster dummies after log total activity.

## Association tests

|   k | domain                             |    n | effect_name    |   effect_size | effect_class   | secondary_effect_name         |   secondary_effect_size | test_statistic_name      |   test_statistic |   asymptotic_p |   permutation_p |   expected_cells_lt5 |   permutation_p_bh |
|----:|:-----------------------------------|-----:|:---------------|--------------:|:---------------|:------------------------------|------------------------:|:-------------------------|-----------------:|---------------:|----------------:|---------------------:|-------------------:|
|   3 | distance_to_centre_km              | 3791 | eta_squared    |      0.053731 | small          | kruskal_epsilon_squared       |                0.051006 | kruskal_H                |       195.209402 |       0.000000 |        0.001000 |                    0 |           0.001000 |
|   3 | log_total_activity                 | 3791 | eta_squared    |      0.496596 | large          | kruskal_epsilon_squared       |                0.534957 | kruskal_H                |      2028.415658 |       0.000000 |        0.001000 |                    0 |           0.001000 |
|   3 | london_plan_inner_outer            | 3791 | cramers_v      |      0.170652 | small          | none                          |              nan        | chi_squared              |       110.402194 |       0.000000 |        0.001000 |                    0 |           0.001000 |
|   3 | howard_four_borough_check          |  357 | cramers_v      |      0.241554 | small          | central_outer_total_variation |                0.151420 | chi_squared              |        20.830415 |       0.000030 |        0.001000 |                    0 |           0.001000 |
|   3 | distance_adjusted_for_log_activity | 3791 | incremental_r2 |      0.009880 | negligible     | full_model_r2                 |                0.085214 | reduced_activity_only_r2 |         0.076086 |     nan        |        0.001000 |                    0 |           0.001000 |
|   4 | distance_to_centre_km              | 3791 | eta_squared    |      0.092867 | medium         | kruskal_epsilon_squared       |                0.090218 | kruskal_H                |       344.657357 |       0.000000 |        0.001000 |                    0 |           0.001000 |
|   4 | log_total_activity                 | 3791 | eta_squared    |      0.626744 | large          | kruskal_epsilon_squared       |                0.670509 | kruskal_H                |      2542.218631 |       0.000000 |        0.001000 |                    0 |           0.001000 |
|   4 | london_plan_inner_outer            | 3791 | cramers_v      |      0.238232 | small          | none                          |              nan        | chi_squared              |       215.157019 |       0.000000 |        0.001000 |                    0 |           0.001000 |
|   4 | howard_four_borough_check          |  357 | cramers_v      |      0.430397 | medium         | central_outer_total_variation |                0.420175 | chi_squared              |        66.131136 |       0.000000 |        0.001000 |                    0 |           0.001000 |
|   4 | distance_adjusted_for_log_activity | 3791 | incremental_r2 |      0.027377 | small          | full_model_r2                 |                0.101379 | reduced_activity_only_r2 |         0.076086 |     nan        |        0.001000 |                    0 |           0.001000 |

`permutation_p_bh` controls the false discovery rate across all K=3/K=4 diagnostic tests.
Effect sizes, not p-values alone, determine whether separation is substantively strong.

## Cluster summaries

|   k |   cluster |    n | metric                |    mean |     q25 |   median |     q75 |
|----:|----------:|-----:|:----------------------|--------:|--------:|---------:|--------:|
|   3 |         0 |  290 | distance_to_centre_km | 11.8273 |  6.4741 |  11.3887 | 16.7552 |
|   3 |         0 |  290 | log_total_activity    |  5.6741 |  4.8876 |   5.5123 |  6.2476 |
|   3 |         1 | 2512 | distance_to_centre_km | 11.8961 |  7.4057 |  11.6914 | 16.0114 |
|   3 |         1 | 2512 | log_total_activity    |  7.2113 |  6.4487 |   7.0947 |  7.8373 |
|   3 |         2 |  989 | distance_to_centre_km | 14.9372 | 10.8991 |  15.3441 | 18.9582 |
|   3 |         2 |  989 | log_total_activity    |  4.8501 |  4.3124 |   5.0339 |  5.5460 |
|   4 |         0 |  577 | distance_to_centre_km | 15.3288 | 11.2959 |  15.7670 | 19.5774 |
|   4 |         0 |  577 | log_total_activity    |  4.3798 |  3.7831 |   4.4932 |  5.0709 |
|   4 |         1 | 1692 | distance_to_centre_km | 10.9426 |  6.5195 |  10.5006 | 14.9373 |
|   4 |         1 | 1692 | log_total_activity    |  7.6427 |  6.9900 |   7.5240 |  8.2020 |
|   4 |         2 | 1307 | distance_to_centre_km | 13.9850 | 10.2067 |  14.2821 | 17.5745 |
|   4 |         2 | 1307 | log_total_activity    |  6.0376 |  5.5596 |   6.0468 |  6.4995 |
|   4 |         3 |  215 | distance_to_centre_km | 11.3854 |  6.1220 |  10.6184 | 16.3375 |
|   4 |         3 |  215 | log_total_activity    |  5.6153 |  4.9153 |   5.6273 |  6.2795 |

## London Plan Inner/Outer composition

|   k | inner_outer   |   cluster |    n |   within_area_share |   within_cluster_share |
|----:|:--------------|----------:|-----:|--------------------:|-----------------------:|
|   3 | Inner         |         0 |  142 |              0.0993 |                 0.4897 |
|   3 | Outer         |         0 |  148 |              0.0627 |                 0.5103 |
|   3 | Inner         |         1 | 1049 |              0.7336 |                 0.4176 |
|   3 | Outer         |         1 | 1463 |              0.6197 |                 0.5824 |
|   3 | Inner         |         2 |  239 |              0.1671 |                 0.2417 |
|   3 | Outer         |         2 |  750 |              0.3177 |                 0.7583 |
|   4 | Inner         |         0 |  123 |              0.0860 |                 0.2132 |
|   4 | Outer         |         0 |  454 |              0.1923 |                 0.7868 |
|   4 | Inner         |         1 |  821 |              0.5741 |                 0.4852 |
|   4 | Outer         |         1 |  871 |              0.3689 |                 0.5148 |
|   4 | Inner         |         2 |  374 |              0.2615 |                 0.2862 |
|   4 | Outer         |         2 |  933 |              0.3952 |                 0.7138 |
|   4 | Inner         |         3 |  112 |              0.0783 |                 0.5209 |
|   4 | Outer         |         3 |  103 |              0.0436 |                 0.4791 |

## Howard targeted four-borough check

|      k |   n_target_lsoas |   central_outer_total_variation |   central_outer_same_cluster_probability |   central_outer_cramers_v |
|-------:|-----------------:|--------------------------------:|-----------------------------------------:|--------------------------:|
| 3.0000 |         357.0000 |                          0.1514 |                                   0.5412 |                    0.2416 |
| 4.0000 |         357.0000 |                          0.4202 |                                   0.3023 |                    0.4304 |

|   k | howard_borough       |   cluster |   n |   within_borough_share |
|----:|:---------------------|----------:|----:|-----------------------:|
|   3 | Westminster          |         0 |  18 |                 0.2022 |
|   3 | Camden               |         0 |  11 |                 0.1158 |
|   3 | Kingston upon Thames |         0 |   1 |                 0.0128 |
|   3 | Richmond upon Thames |         0 |   8 |                 0.0842 |
|   3 | Westminster          |         1 |  67 |                 0.7528 |
|   3 | Camden               |         1 |  68 |                 0.7158 |
|   3 | Kingston upon Thames |         1 |  55 |                 0.7051 |
|   3 | Richmond upon Thames |         1 |  64 |                 0.6737 |
|   3 | Westminster          |         2 |   4 |                 0.0449 |
|   3 | Camden               |         2 |  16 |                 0.1684 |
|   3 | Kingston upon Thames |         2 |  22 |                 0.2821 |
|   3 | Richmond upon Thames |         2 |  23 |                 0.2421 |
|   4 | Westminster          |         0 |   1 |                 0.0112 |
|   4 | Camden               |         0 |  12 |                 0.1263 |
|   4 | Kingston upon Thames |         0 |  15 |                 0.1923 |
|   4 | Richmond upon Thames |         0 |  12 |                 0.1263 |
|   4 | Westminster          |         1 |  59 |                 0.6629 |
|   4 | Camden               |         1 |  59 |                 0.6211 |
|   4 | Kingston upon Thames |         1 |  30 |                 0.3846 |
|   4 | Richmond upon Thames |         1 |  24 |                 0.2526 |
|   4 | Westminster          |         2 |  17 |                 0.1910 |
|   4 | Camden               |         2 |  15 |                 0.1579 |
|   4 | Kingston upon Thames |         2 |  33 |                 0.4231 |
|   4 | Richmond upon Thames |         2 |  55 |                 0.5789 |
|   4 | Westminster          |         3 |  12 |                 0.1348 |
|   4 | Camden               |         3 |   9 |                 0.0947 |
|   4 | Kingston upon Thames |         3 |   0 |                 0.0000 |
|   4 | Richmond upon Thames |         3 |   4 |                 0.0421 |

## Interpretation boundary

These are LSOA-level external associations. They do not prove that geographic location
causes a temporal profile, do not identify individual passengers, and do not make the
clusters spatial zones. Mixed geography can be substantively valid for a temporal-shape
typology even when it is unsuitable for a centre-versus-periphery spatial typology.

## Fallacy scan

- Coverage: 11/11 statistical fallacy types checked.
- RED_FLAG if area-level associations are interpreted as passenger-level behaviour (ecological fallacy).
- CAUTION: exploratory K=3/K=4 comparisons create researcher degrees of freedom; both are reported.
- CAUTION: cross-sectional external associations do not support causal or directional claims.
- NOTE: BH adjustment is applied across all reported permutation tests.