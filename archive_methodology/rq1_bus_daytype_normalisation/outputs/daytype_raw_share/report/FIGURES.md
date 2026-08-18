# daytype_raw_share: spatial distribution and temporal profiles, K=3-5

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
| C0        | 1078 |    31.969 |                 332.362 |                 0.068 |              0.043 |              -0.183 |           0.754 |            0.315 |         14.639 |         0.127 |        0.024 |        0.178 |
| C1        | 1742 |    51.661 |                1713.211 |                 0.118 |              0.069 |              -0.096 |           0.804 |            0.021 |         11.029 |         0.153 |        0.097 |        0.207 |
| C2        |  552 |    16.370 |                 414.334 |                 0.151 |              0.096 |              -0.110 |           0.817 |            0.082 |         12.361 |         0.198 |        0.128 |        0.265 |

### K=4

| cluster   |    n |   share_% |   median_total_activity |   post_midnight_share |   deep_night_share |   direction_balance |   weekend_ratio |   zero_bin_share |   km_to_centre |   post00_wkdy |   post00_sat |   post00_sun |
|:----------|-----:|----------:|------------------------:|----------------------:|-------------------:|--------------------:|----------------:|-----------------:|---------------:|--------------:|-------------:|-------------:|
| C0        | 1535 |    45.522 |                1851.708 |                 0.114 |              0.066 |              -0.091 |           0.804 |            0.021 |         10.930 |         0.146 |        0.092 |        0.198 |
| C1        |  323 |     9.579 |                 777.351 |                 0.162 |              0.094 |              -0.023 |           0.861 |            0.050 |          9.619 |         0.154 |        0.122 |        0.208 |
| C2        |  502 |    14.887 |                 423.114 |                 0.134 |              0.090 |              -0.171 |           0.779 |            0.098 |         14.159 |         0.220 |        0.122 |        0.291 |
| C3        | 1012 |    30.012 |                 328.503 |                 0.067 |              0.042 |              -0.191 |           0.752 |            0.320 |         14.648 |         0.128 |        0.023 |        0.178 |

### K=5

| cluster   |    n |   share_% |   median_total_activity |   post_midnight_share |   deep_night_share |   direction_balance |   weekend_ratio |   zero_bin_share |   km_to_centre |   post00_wkdy |   post00_sat |   post00_sun |
|:----------|-----:|----------:|------------------------:|----------------------:|-------------------:|--------------------:|----------------:|-----------------:|---------------:|--------------:|-------------:|-------------:|
| C0        |  324 |     9.609 |                 566.035 |                 0.160 |              0.093 |              -0.045 |           0.858 |            0.054 |          9.826 |         0.160 |        0.125 |        0.214 |
| C1        |  487 |    14.442 |                 525.889 |                 0.136 |              0.092 |              -0.178 |           0.776 |            0.067 |         13.936 |         0.222 |        0.126 |        0.295 |
| C2        |  459 |    13.612 |                 444.081 |                 0.088 |              0.056 |              -0.199 |           0.756 |            0.235 |         14.406 |         0.169 |        0.047 |        0.230 |
| C3        |  709 |    21.026 |                 303.714 |                 0.058 |              0.037 |              -0.179 |           0.754 |            0.346 |         14.708 |         0.108 |        0.016 |        0.154 |
| C4        | 1393 |    41.311 |                2135.110 |                 0.116 |              0.067 |              -0.077 |           0.809 |            0.014 |         10.628 |         0.143 |        0.094 |        0.195 |
