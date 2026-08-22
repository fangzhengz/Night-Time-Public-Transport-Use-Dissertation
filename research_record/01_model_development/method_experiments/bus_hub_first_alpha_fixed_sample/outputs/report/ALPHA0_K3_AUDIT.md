# alpha=0 K=3 candidate audit

## Figure index

- Selected K=3 temporal profiles: `../figures/alpha0_k3_temporal_profiles.png`
- Covariance x K BIC grid: `../figures/alpha0_bic_grid.png`
- Multi-criterion K diagnostics: `../figures/alpha0_k_selection_diagnostics.png`
- Adjacent-K temporal profiles: `../figures/alpha0_profiles_k2.png` and
  `../figures/alpha0_profiles_k4.png` through `../figures/alpha0_profiles_k8.png`

The plotted profiles are mean shares of each direction's own full-week total,
not raw passenger totals and not within-day-normalised shares.

## Cluster signatures

|   cluster |    n |    share |   total_p10 |   total_median |   total_p90 |   median_boarding_alighting_total_ratio |   boardings_Weekday_share |   boardings_Saturday_share |   boardings_Sunday_share |   boardings_00_05_share |   boardings_01_05_share | boardings_peak_day   |   boardings_peak_hour |   alightings_Weekday_share |   alightings_Saturday_share |   alightings_Sunday_share |   alightings_00_05_share |   alightings_01_05_share | alightings_peak_day   |   alightings_peak_hour |
|----------:|-----:|---------:|------------:|---------------:|------------:|----------------------------------------:|--------------------------:|---------------------------:|-------------------------:|------------------------:|------------------------:|:---------------------|----------------------:|---------------------------:|----------------------------:|--------------------------:|-------------------------:|-------------------------:|:----------------------|-----------------------:|
|         0 | 1882 | 0.523796 |    634.342  |       1650.5   |    6822.35  |                                0.791779 |                  0.377742 |                   0.352876 |                 0.269381 |               0.147562  |               0.125357  | Weekday              |                  1080 |                   0.392208 |                    0.349081 |                  0.258711 |                0.097724  |                0.0634718 | Weekday               |                   1080 |
|         1 |  494 | 0.13749  |    126.666  |        384.719 |    1096.78  |                                0.764494 |                  0.375143 |                   0.348677 |                 0.27618  |               0.197817  |               0.17744   | Weekday              |                  1080 |                   0.388793 |                    0.348655 |                  0.262552 |                0.13191   |                0.0943718 | Weekday               |                   1080 |
|         2 | 1217 | 0.338714 |     85.2979 |        256.003 |     680.092 |                                0.670072 |                  0.387463 |                   0.355125 |                 0.257412 |               0.0979432 |               0.0879198 | Weekday              |                  1080 |                   0.410925 |                    0.354201 |                  0.234874 |                0.0456596 |                0.0167567 | Weekday               |                   1080 |

## Spatial adjacency

Observed same-cluster neighbour share:
0.490; random label-frequency
expectation: 0.408; ratio:
1.20.

|   cluster |   n_lsoa |   incident_edges |   within_cluster_edges |   within_share_of_incident_edges |
|----------:|---------:|-----------------:|-----------------------:|---------------------------------:|
|         0 |     1882 |             6289 |                   2615 |                         0.415805 |
|         1 |      494 |             2045 |                    235 |                         0.114914 |
|         2 |     1217 |             4187 |                   1209 |                         0.288751 |

## alpha=5 rows mapped to alpha=0 columns

|   cluster |    0 |   1 |    2 |
|----------:|-----:|----:|-----:|
|         0 | 1701 |   0 |    0 |
|         1 |  140 |  42 | 1216 |
|         2 |   41 | 452 |    1 |

Row shares:

|   cluster |        0 |         1 |          2 |
|----------:|---------:|----------:|-----------:|
|         0 | 1        | 0         | 0          |
|         1 | 0.100143 | 0.0300429 | 0.869814   |
|         2 | 0.082996 | 0.91498   | 0.00202429 |

## Reading

The high-activity/intermediate-late cluster is alpha=0 C0. The low-activity,
early-fading cluster is alpha=0 C2. The smaller late-persistent cluster is
alpha=0 C1. Cluster numbers are arbitrary and should be replaced with descriptive
names in writing.
