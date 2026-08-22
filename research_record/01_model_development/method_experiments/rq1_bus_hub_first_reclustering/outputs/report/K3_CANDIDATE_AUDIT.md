# K=3 candidate interpretation audit

## Direct verdict

K=3 is the BIC-supported candidate and is much more defensible than K>=4, but
it is **not yet a strongly separated three-type solution**. The temporal means
remain close, silhouette is low, and the least stable cluster must be treated
as provisional until the fixed-sample alpha sensitivity is run.

## Size and activity

|   K |   cluster |    n |    share |   median_total_activity |   median_max_posterior |
|----:|----------:|-----:|---------:|------------------------:|-----------------------:|
|   3 |         0 | 1701 | 0.473421 |                1778.01  |                      1 |
|   3 |         1 | 1398 | 0.38909  |                 292.018 |                      1 |
|   3 |         2 |  494 | 0.13749  |                 407.643 |                      1 |

|   cluster |    n |    share |   total_p10 |   total_median |   total_p90 |   median_boarding_alighting_total_ratio |   boardings_Weekday_share |   boardings_Saturday_share |   boardings_Sunday_share |   boardings_00_05_share |   boardings_01_05_share | boardings_peak_day   |   boardings_peak_hour |   alightings_Weekday_share |   alightings_Saturday_share |   alightings_Sunday_share |   alightings_00_05_share |   alightings_01_05_share | alightings_peak_day   |   alightings_peak_hour |
|----------:|-----:|---------:|------------:|---------------:|------------:|----------------------------------------:|--------------------------:|---------------------------:|-------------------------:|------------------------:|------------------------:|:---------------------|----------------------:|---------------------------:|----------------------------:|--------------------------:|-------------------------:|-------------------------:|:----------------------|-----------------------:|
|         0 | 1701 | 0.473421 |    724.257  |       1778.01  |    7391.17  |                                0.805937 |                  0.377488 |                   0.35324  |                 0.269273 |                0.14779  |               0.124786  | Weekday              |                  1080 |                   0.390872 |                    0.348836 |                  0.260292 |                0.100783  |                0.0664605 | Weekday               |                   1080 |
|         1 | 1398 | 0.38909  |     91.5482 |        292.018 |     860.092 |                                0.673727 |                  0.385649 |                   0.354884 |                 0.259467 |                0.105654 |               0.0937284 | Weekday              |                  1080 |                   0.408748 |                    0.354178 |                  0.237074 |                0.0517552 |                0.0220568 | Weekday               |                   1080 |
|         2 |  494 | 0.13749  |    129.491  |        407.643 |    1389.23  |                                0.76682  |                  0.374486 |                   0.347722 |                 0.277792 |                0.199713 |               0.178131  | Weekday              |                  1080 |                   0.388037 |                    0.348277 |                  0.263685 |                0.133887  |                0.0964276 | Weekday               |                   1080 |

## Bootstrap recovery by cluster

|   index |   base_cluster |     mean |       std |      min |   median |      max |
|--------:|---------------:|---------:|----------:|---------:|---------:|---------:|
|       0 |              0 | 0.812126 | 0.0556218 | 0.707993 | 0.815452 | 0.908084 |
|       1 |              1 | 0.860623 | 0.0301311 | 0.809673 | 0.858361 | 0.910508 |
|       2 |              2 | 0.513036 | 0.13206   | 0.320225 | 0.491884 | 0.781879 |

## Spatial adjacency

Across 8290 retained-LSOA neighbour edges, the
observed same-cluster share is 0.481;
the label-frequency expectation is 0.394
(ratio 1.22). This is a compact
spatial-coherence diagnostic, not a formal spatial clustering objective.

|   cluster |   n_lsoa |   incident_edges |   within_cluster_edges |   within_share_of_incident_edges |
|----------:|---------:|-----------------:|-----------------------:|---------------------------------:|
|         0 |     1701 |             5837 |                   2190 |                         0.375193 |
|         1 |     1398 |             4732 |                   1540 |                         0.325444 |
|         2 |      494 |             2021 |                    260 |                         0.128649 |

## Relationship to the historical K=3 labels

ARI on shared LSOAs: 0.266.

Counts:

|   cluster |    0 |   1 |   2 |
|----------:|-----:|----:|----:|
|         0 |   21 |  40 | 189 |
|         1 | 1645 | 650 | 278 |
|         2 |   25 | 691 |  18 |

Old-cluster row shares mapped into the new clusters:

|   cluster |         0 |        1 |         2 |
|----------:|----------:|---------:|----------:|
|         0 | 0.084     | 0.16     | 0.756     |
|         1 | 0.639332  | 0.252623 | 0.108045  |
|         2 | 0.0340599 | 0.941417 | 0.0245232 |

## Largest standardised profile deviations

|   cluster |   rank | feature                 |   standardized_mean_difference |   cluster_mean_share |   global_mean_share |
|----------:|-------:|:------------------------|-------------------------------:|---------------------:|--------------------:|
|         0 |      1 | boardings_Weekday_1440  |                       0.352458 |          0.00827609  |          0.00669115 |
|         0 |      2 | boardings_Sunday_1440   |                       0.352458 |          0.00827609  |          0.00669115 |
|         0 |      3 | alightings_Weekday_1560 |                       0.283378 |          0.00283502  |          0.00208272 |
|         0 |      4 | alightings_Sunday_1560  |                       0.283378 |          0.00283502  |          0.00208272 |
|         0 |      5 | boardings_Saturday_1440 |                       0.274949 |          0.00645179  |          0.00511591 |
|         0 |      6 | boardings_Weekday_1380  |                       0.273666 |          0.0188405   |          0.0164118  |
|         0 |      7 | alightings_Weekday_1080 |                      -0.266433 |          0.111824    |          0.118906   |
|         0 |      8 | alightings_Sunday_1500  |                       0.264375 |          0.00468402  |          0.00377155 |
|         0 |      9 | alightings_Weekday_1500 |                       0.264375 |          0.00468402  |          0.00377155 |
|         0 |     10 | boardings_Weekday_1560  |                       0.262967 |          0.00252286  |          0.00186013 |
|         1 |      1 | boardings_Sunday_1620   |                      -0.588032 |          0.000535619 |          0.00276923 |
|         1 |      2 | boardings_Weekday_1620  |                      -0.588032 |          0.000535619 |          0.00276923 |
|         1 |      3 | alightings_Weekday_1560 |                      -0.587702 |          0.000522504 |          0.00208272 |
|         1 |      4 | alightings_Sunday_1560  |                      -0.587702 |          0.000522504 |          0.00208272 |
|         1 |      5 | boardings_Saturday_1680 |                      -0.575619 |          0.00140724  |          0.00568249 |
|         1 |      6 | boardings_Weekday_1560  |                      -0.56439  |          0.000437748 |          0.00186013 |
|         1 |      7 | boardings_Sunday_1560   |                      -0.56439  |          0.000437748 |          0.00186013 |
|         1 |      8 | alightings_Sunday_1500  |                      -0.563797 |          0.00182565  |          0.00377155 |
|         1 |      9 | alightings_Weekday_1500 |                      -0.563797 |          0.00182565  |          0.00377155 |
|         1 |     10 | boardings_Saturday_1620 |                      -0.536705 |          0.000497637 |          0.00284336 |
|         2 |      1 | boardings_Sunday_1680   |                       0.813248 |          0.0134835   |          0.0069825  |
|         2 |      2 | boardings_Weekday_1680  |                       0.813248 |          0.0134835   |          0.0069825  |
|         2 |      3 | boardings_Saturday_1680 |                       0.804653 |          0.0116588   |          0.00568249 |
|         2 |      4 | boardings_Weekday_1620  |                       0.793429 |          0.00578304  |          0.00276923 |
|         2 |      5 | boardings_Sunday_1620   |                       0.793429 |          0.00578304  |          0.00276923 |
|         2 |      6 | alightings_Weekday_1620 |                       0.786081 |          0.00399946  |          0.0018687  |
|         2 |      7 | alightings_Sunday_1620  |                       0.786081 |          0.00399946  |          0.0018687  |
|         2 |      8 | boardings_Saturday_1620 |                       0.769099 |          0.00620479  |          0.00284336 |
|         2 |      9 | alightings_Weekday_1680 |                       0.740753 |          0.00551252  |          0.00253401 |
|         2 |     10 | alightings_Sunday_1680  |                       0.740753 |          0.00551252  |          0.00253401 |

## Interpretation limit

The new result is a combined consequence of hub-first allocation, the full-week
total>=50 floor, exception exclusion, and alpha=5 shrinkage. The low old-new ARI
therefore proves pipeline sensitivity, not which single change caused it. The
next minimal test is alpha=0 versus alpha=5 on exactly these 3,593 LSOAs.
