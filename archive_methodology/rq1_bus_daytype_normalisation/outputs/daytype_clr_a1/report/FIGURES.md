# daytype_clr_a1: spatial distribution and temporal profiles, K=3-5

Sidecar figures, 2026-08-01. Not an adopted result.

## How to read these

- Profiles are in day-type share space (mean + interquartile band). Under day-type closure each panel sums to 1 within itself, so the three panels of a row show SHAPE only -- how much of a cluster's week falls on Saturday is no longer visible in the curves and must be read from `weekend_ratio` in the table below.
- Maps carry the canonical three-state legend. Grey is measured but below-threshold night flow; hatched white is an LSOA with no StopArea point inside it (a point-in-polygon artefact, not a service gap).
- `post00_*` is the share of that day type's boardings falling after midnight, i.e. the night-persistence signal, per day type.
- Cluster ids are arbitrary GMM component labels and carry no meaning across K or across variants.

## Cluster descriptives

### K=3

| cluster   |    n |   share_% |   median_total_activity |   post_midnight_share |   deep_night_share |   direction_balance |   weekend_ratio |   zero_bin_share |   km_to_centre |   post00_wkdy |   post00_sat |   post00_sun |
|:----------|-----:|----------:|------------------------:|----------------------:|-------------------:|--------------------:|----------------:|-----------------:|---------------:|--------------:|-------------:|-------------:|
| C0        |  817 |    24.229 |                 469.705 |                 0.109 |              0.070 |              -0.140 |           0.781 |            0.119 |         13.682 |         0.165 |        0.085 |        0.225 |
| C1        |  947 |    28.084 |                 307.927 |                 0.068 |              0.043 |              -0.186 |           0.751 |            0.335 |         14.659 |         0.127 |        0.022 |        0.180 |
| C2        | 1608 |    47.687 |                1898.518 |                 0.130 |              0.075 |              -0.084 |           0.818 |            0.005 |         10.420 |         0.160 |        0.109 |        0.214 |

### K=4

| cluster   |    n |   share_% |   median_total_activity |   post_midnight_share |   deep_night_share |   direction_balance |   weekend_ratio |   zero_bin_share |   km_to_centre |   post00_wkdy |   post00_sat |   post00_sun |
|:----------|-----:|----------:|------------------------:|----------------------:|-------------------:|--------------------:|----------------:|-----------------:|---------------:|--------------:|-------------:|-------------:|
| C0        |  636 |    18.861 |                 459.062 |                 0.111 |              0.070 |              -0.130 |           0.788 |            0.080 |         13.255 |         0.160 |        0.087 |        0.220 |
| C1        | 1572 |    46.619 |                1944.522 |                 0.130 |              0.076 |              -0.083 |           0.818 |            0.004 |         10.358 |         0.160 |        0.110 |        0.214 |
| C2        |  290 |     8.600 |                 638.531 |                 0.101 |              0.069 |              -0.176 |           0.761 |            0.226 |         14.865 |         0.179 |        0.066 |        0.238 |
| C3        |  874 |    25.919 |                 288.712 |                 0.066 |              0.042 |              -0.186 |           0.751 |            0.342 |         14.635 |         0.123 |        0.021 |        0.175 |

### K=5

| cluster   |    n |   share_% |   median_total_activity |   post_midnight_share |   deep_night_share |   direction_balance |   weekend_ratio |   zero_bin_share |   km_to_centre |   post00_wkdy |   post00_sat |   post00_sun |
|:----------|-----:|----------:|------------------------:|----------------------:|-------------------:|--------------------:|----------------:|-----------------:|---------------:|--------------:|-------------:|-------------:|
| C0        | 1209 |    35.854 |                2521.109 |                 0.134 |              0.077 |              -0.073 |           0.823 |            0.001 |         10.066 |         0.161 |        0.113 |        0.214 |
| C1        |  377 |    11.180 |                 395.838 |                 0.104 |              0.067 |              -0.117 |           0.773 |            0.119 |         13.864 |         0.146 |        0.076 |        0.208 |
| C2        |  739 |    21.916 |                 267.003 |                 0.064 |              0.041 |              -0.195 |           0.746 |            0.356 |         15.016 |         0.122 |        0.019 |        0.174 |
| C3        |  633 |    18.772 |                 705.882 |                 0.119 |              0.072 |              -0.133 |           0.804 |            0.023 |         11.827 |         0.168 |        0.099 |        0.224 |
| C4        |  414 |    12.278 |                 581.195 |                 0.092 |              0.060 |              -0.158 |           0.768 |            0.238 |         14.097 |         0.161 |        0.054 |        0.219 |
