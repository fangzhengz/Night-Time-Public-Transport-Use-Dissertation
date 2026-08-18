# fullweek_padded: station maps, profiles and cluster descriptives, K=5-9

Sidecar figures, 2026-08-01. Not an adopted result.

## How to read these

- Profiles: each day block sums to 1 over its OWN bins. MON/TWT/SUN have 28 bins and FRI/SAT have 44, so the shorter days sit ~1.6x higher. The step at a day boundary is the window, not behaviour. Between-day magnitude is exactly what day-type closure removes, so it must be read from `weekend_ratio` in the table, never from the curves.
- Maps: circles are Underground stations, triangles the non-LU stations added by the all-modes merge (DLR, Overground, Elizabeth line, National Rail).
- `night_tube_ext` is the share of a station's activity falling beyond the normal 01:00 close. Under this closure it is the single metric the partition explains best (eta-squared 0.59 at K=5 vs 0.17 under full-week closure), so it is the axis to name clusters on.
- `zero_bin_share` is carried alongside it because the two are mechanically coupled: a station off the Night Tube network has both a near-zero extension share and zeros through the late bins. Any cluster reading has to say which of the two it is claiming.
- Cluster ids are arbitrary GMM component labels; they carry no meaning across K.

## Cluster descriptives

### K=4

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes             | example_stations                                           |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:----------------------|:-----------------------------------------------------------|
| C0        | 220 |    54.455 |               11248.981 |              -0.442 |            0.038 |            0.028 |         0.057 |           0.741 |            0.265 |         13.581 |   70.909 | LU 136, LO 40, EZL 17 | Stratford, Clapham Junction, Wimbledon                     |
| C1        |  15 |     3.713 |               36157.224 |               0.124 |            0.027 |            0.025 |         0.046 |           1.018 |            0.240 |          9.955 |   66.667 | LU 7, EZL,LU 3, LO 2  | Leicester Square, Piccadilly Circus, North Greenwich       |
| C2        |  77 |    19.059 |               18655.958 |              -0.216 |            0.051 |            0.044 |         0.084 |           0.878 |            0.239 |          7.196 |   57.143 | LU 38, DLR 25, LO 6   | Paddington TfL, Brixton LU, Finsbury Park LU               |
| C3        |  92 |    22.772 |               25772.939 |               0.128 |            0.026 |            0.016 |         0.040 |           0.810 |            0.273 |          4.908 |   65.217 | LU 47, LO 26, LO,LU 7 | Liverpool Street LU, King's Cross St. Pancras, Waterloo LU |

### K=5

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes               | example_stations                                           |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:------------------------|:-----------------------------------------------------------|
| C0        | 170 |    42.079 |               17076.790 |              -0.360 |            0.041 |            0.040 |         0.063 |           0.815 |            0.231 |          9.792 |   75.294 | LU 109, LO 15, LO,LU 14 | Stratford, Paddington TfL, Clapham Junction                |
| C1        |  31 |     7.673 |               15564.770 |              -0.121 |            0.065 |            0.043 |         0.110 |           0.930 |            0.253 |          8.146 |   38.710 | DLR 16, LU 11, LO 3     | Brixton LU, Camden Town, Highbury & Islington              |
| C2        |  95 |    23.515 |                7629.715 |              -0.503 |            0.037 |            0.018 |         0.054 |           0.677 |            0.305 |         17.275 |   64.211 | LU 55, LO 26, EZL 5     | Wimbledon, Richmond, Southall                              |
| C3        |  19 |     4.703 |               61907.494 |               0.307 |            0.030 |            0.031 |         0.050 |           1.000 |            0.210 |          5.864 |   84.211 | LU 12, EZL,LU 4, LO 1   | Tottenham Court Road, Oxford Circus, Leicester Square      |
| C4        |  89 |    22.030 |               18238.613 |               0.075 |            0.024 |            0.012 |         0.036 |           0.785 |            0.287 |          5.317 |   59.551 | LU 41, LO 29, DLR 7     | Liverpool Street LU, King's Cross St. Pancras, Waterloo LU |

### K=6

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes                | example_stations                                                    |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:-------------------------|:--------------------------------------------------------------------|
| C0        |  29 |     7.178 |               14875.293 |              -0.138 |            0.068 |            0.044 |         0.116 |           0.939 |            0.264 |          8.653 |   34.483 | DLR 17, LU 10, LO 2      | Brixton LU, Camden Town, Wembley Park                               |
| C1        |  13 |     3.218 |               36157.224 |               0.175 |            0.028 |            0.022 |         0.048 |           1.036 |            0.216 |          9.276 |   69.231 | LU 6, EZL,LU 3, DLR 2    | Leicester Square, Piccadilly Circus, North Greenwich                |
| C2        |  70 |    17.327 |                6709.919 |              -0.542 |            0.041 |            0.022 |         0.060 |           0.667 |            0.294 |         18.310 |   74.286 | LU 47, LO 16, LO,LU 4    | Wimbledon, Richmond, Parsons Green                                  |
| C3        |  85 |    21.040 |                9977.840 |              -0.224 |            0.027 |            0.009 |         0.040 |           0.795 |            0.309 |         10.647 |   42.353 | LO 38, LU 30, EZL 6      | Victoria LU, Stratford, Euston LU                                   |
| C4        |  52 |    12.871 |               33026.772 |               0.233 |            0.027 |            0.023 |         0.041 |           0.745 |            0.245 |          3.383 |   84.615 | LU 34, LO 6, LO,LU 4     | Liverpool Street LU, King's Cross St. Pancras, Tottenham Court Road |
| C5        | 155 |    38.366 |               17610.581 |              -0.346 |            0.041 |            0.041 |         0.063 |           0.819 |            0.229 |          9.089 |   76.774 | LU 101, LO,LU 13, DLR 13 | Waterloo LU, Paddington TfL, Finsbury Park LU                       |

### K=7

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes                | example_stations                                          |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:-------------------------|:----------------------------------------------------------|
| C0        | 148 |    36.634 |               17687.752 |              -0.334 |            0.042 |            0.043 |         0.066 |           0.818 |            0.221 |          9.115 |   77.703 | LU 97, DLR 15, LO,LU 12  | Stratford, Paddington TfL, Finsbury Park LU               |
| C1        |  14 |     3.465 |               67513.804 |               0.223 |            0.030 |            0.034 |         0.051 |           1.108 |            0.182 |          7.477 |   92.857 | LU 9, EZL,LU 4, DLR 1    | Tottenham Court Road, Leicester Square, Piccadilly Circus |
| C2        |  22 |     5.446 |               17803.687 |              -0.168 |            0.070 |            0.051 |         0.119 |           0.913 |            0.245 |          8.701 |   40.909 | DLR 11, LU 9, EZL 1      | Brixton LU, Wembley Park, Tottenham Hale LU               |
| C3        |  67 |    16.584 |                9018.059 |              -0.378 |            0.030 |            0.013 |         0.044 |           0.707 |            0.304 |         14.405 |   49.254 | LU 29, LO 23, EZL 7      | Upton Park, East Ham, Ilford                              |
| C4        |  54 |    13.366 |               20538.536 |               0.030 |            0.029 |            0.012 |         0.045 |           0.933 |            0.286 |          5.167 |   50.000 | LU 23, LO 21, DLR 6      | King's Cross St. Pancras, Waterloo LU, Victoria LU        |
| C5        |  68 |    16.832 |                7480.372 |              -0.522 |            0.040 |            0.017 |         0.058 |           0.700 |            0.314 |         16.960 |   64.706 | LU 39, LO 18, EZL 5      | Wimbledon, Abbey Wood, Richmond                           |
| C6        |  31 |     7.673 |               28149.393 |               0.290 |            0.025 |            0.022 |         0.036 |           0.597 |            0.251 |          3.238 |   93.548 | LU 22, EZL,LU 2, LO,LU 2 | Liverpool Street LU, Canary Wharf LU, Oxford Circus       |
