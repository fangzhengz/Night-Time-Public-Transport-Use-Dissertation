# daytype_unpadded: station maps, profiles and cluster descriptives, K=5-9

Sidecar figures, 2026-08-01. Not an adopted result.

## How to read these

- Profiles: each day block sums to 1 over its OWN bins. MON/TWT/SUN have 28 bins and FRI/SAT have 44, so the shorter days sit ~1.6x higher. The step at a day boundary is the window, not behaviour. Between-day magnitude is exactly what day-type closure removes, so it must be read from `weekend_ratio` in the table, never from the curves.
- Maps: circles are Underground stations, triangles the non-LU stations added by the all-modes merge (DLR, Overground, Elizabeth line, National Rail).
- `night_tube_ext` is the share of a station's activity falling beyond the normal 01:00 close. Under this closure it is the single metric the partition explains best (eta-squared 0.59 at K=5 vs 0.17 under full-week closure), so it is the axis to name clusters on.
- `zero_bin_share` is carried alongside it because the two are mechanically coupled: a station off the Night Tube network has both a near-zero extension share and zeros through the late bins. Any cluster reading has to say which of the two it is claiming.
- Cluster ids are arbitrary GMM component labels; they carry no meaning across K.

## Cluster descriptives

### K=5

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes                | example_stations                                           |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:-------------------------|:-----------------------------------------------------------|
| C0        |  81 |    20.050 |               19137.807 |              -0.421 |            0.044 |            0.069 |         0.067 |           0.783 |            0.159 |         10.603 |   98.765 | LU 72, LO,LU 4, DLR,LU 2 | Stratford, Finsbury Park LU, Vauxhall LU                   |
| C1        |  35 |     8.663 |               54043.997 |               0.289 |            0.026 |            0.028 |         0.041 |           0.878 |            0.232 |          5.190 |   80.000 | LU 21, LO 5, EZL,LU 5    | Tottenham Court Road, Oxford Circus, Leicester Square      |
| C2        |  86 |    21.287 |               20248.125 |              -0.064 |            0.030 |            0.012 |         0.046 |           0.850 |            0.274 |          5.574 |   63.953 | LU 45, LO 22, DLR 7      | Liverpool Street LU, King's Cross St. Pancras, Waterloo LU |
| C3        |  49 |    12.129 |               14875.293 |              -0.203 |            0.060 |            0.047 |         0.101 |           0.884 |            0.243 |          9.242 |   48.980 | DLR 23, LU 23, LO 2      | Brixton LU, Camden Town, Wembley Park                      |
| C4        | 153 |    37.871 |                8859.164 |              -0.398 |            0.034 |            0.010 |         0.050 |           0.719 |            0.321 |         14.185 |   54.248 | LU 67, LO 44, EZL 17     | Wimbledon, Barking, Woolwich EL                            |

### K=6

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes             | example_stations                                           |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:----------------------|:-----------------------------------------------------------|
| C0        |  42 |    10.396 |                9538.665 |              -0.202 |            0.059 |            0.011 |         0.098 |           0.799 |            0.328 |         12.273 |   21.429 | DLR 28, LU 8, LO 4    | Kentish Town, Woolwich Arsenal, Lewisham DLR               |
| C1        | 140 |    34.653 |                9000.310 |              -0.413 |            0.035 |            0.010 |         0.052 |           0.731 |            0.318 |         14.213 |   52.857 | LU 58, LO 40, EZL 17  | Wimbledon, Barking, Woolwich EL                            |
| C2        |  81 |    20.050 |               19003.345 |              -0.036 |            0.028 |            0.010 |         0.041 |           0.825 |            0.282 |          5.641 |   65.432 | LU 42, LO 24, LO,LU 5 | Liverpool Street LU, King's Cross St. Pancras, Waterloo LU |
| C3        |  29 |     7.178 |               57639.125 |               0.342 |            0.027 |            0.035 |         0.042 |           0.866 |            0.200 |          3.750 |   93.103 | LU 22, EZL,LU 4, LO 2 | Tottenham Court Road, Oxford Circus, Leicester Square      |
| C4        |  75 |    18.564 |               18055.469 |              -0.433 |            0.044 |            0.069 |         0.067 |           0.777 |            0.160 |         11.012 |   98.667 | LU 67, LO,LU 4, LO 1  | Stratford, Vauxhall LU, Ealing Broadway                    |
| C5        |  37 |     9.158 |               27962.242 |              -0.229 |            0.042 |            0.069 |         0.069 |           0.931 |            0.178 |          6.650 |   89.189 | LU 31, LO 3, DLR,LO 1 | Brixton LU, Finsbury Park LU, Camden Town                  |

### K=7

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes                | example_stations                                           |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:-------------------------|:-----------------------------------------------------------|
| C0        |  65 |    16.089 |               14931.435 |              -0.459 |            0.044 |            0.067 |         0.067 |           0.763 |            0.160 |         11.937 |  100.000 | LU 60, LO,LU 2, EZL,LU 1 | Stratford, Ealing Broadway, Walthamstow Central            |
| C1        |  27 |     6.683 |               57479.686 |               0.342 |            0.023 |            0.027 |         0.036 |           0.900 |            0.227 |          4.551 |   85.185 | LU 18, EZL,LU 5, LO 4    | Tottenham Court Road, Oxford Circus, Leicester Square      |
| C2        | 145 |    35.891 |                8859.164 |              -0.423 |            0.035 |            0.010 |         0.052 |           0.725 |            0.320 |         14.623 |   53.793 | LU 62, LO 41, EZL 17     | Wimbledon, Barking, Woolwich EL                            |
| C3        |  32 |     7.921 |               12598.799 |              -0.127 |            0.069 |            0.012 |         0.115 |           0.851 |            0.313 |          8.134 |   12.500 | DLR 27, LU 3, DLR,LO 1   | Whitechapel, Shadwell LO, Woolwich Arsenal                 |
| C4        |  40 |     9.901 |               26798.391 |              -0.284 |            0.042 |            0.068 |         0.068 |           0.891 |            0.179 |          6.515 |   92.500 | LU 33, LO 3, LO,LU 3     | Brixton LU, Finsbury Park LU, Vauxhall LU                  |
| C5        |  18 |     4.455 |               23633.543 |              -0.074 |            0.037 |            0.048 |         0.061 |           0.895 |            0.229 |          9.921 |   66.667 | LU 11, LO 3, DLR 2       | North Greenwich, Camden Town, Highbury & Islington         |
| C6        |  77 |    19.059 |               20546.073 |              -0.020 |            0.027 |            0.011 |         0.041 |           0.813 |            0.277 |          5.510 |   66.234 | LU 41, LO 23, LO,LU 5    | Liverpool Street LU, King's Cross St. Pancras, Waterloo LU |

### K=8

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes                | example_stations                                           |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:-------------------------|:-----------------------------------------------------------|
| C0        |  67 |    16.584 |               15808.177 |              -0.448 |            0.044 |            0.068 |         0.067 |           0.769 |            0.160 |         11.598 |  100.000 | LU 62, LO,LU 2, EZL,LU 1 | Stratford, Vauxhall LU, Ealing Broadway                    |
| C1        |  36 |     8.911 |               12331.837 |              -0.139 |            0.066 |            0.012 |         0.110 |           0.820 |            0.308 |          9.332 |   13.889 | DLR 28, LU 5, DLR,LO 1   | Shadwell LO, Kentish Town, Woolwich Arsenal                |
| C2        |  47 |    11.634 |               30748.466 |              -0.036 |            0.032 |            0.025 |         0.049 |           0.907 |            0.228 |          5.126 |   78.723 | LU 30, LO 9, LO,LU 3     | Liverpool Street LU, King's Cross St. Pancras, Waterloo LU |
| C3        |  37 |     9.158 |               24920.269 |              -0.276 |            0.043 |            0.073 |         0.070 |           0.893 |            0.177 |          6.612 |   91.892 | LU 30, LO 3, LO,LU 3     | Brixton LU, Earl's Court, Elephant & Castle LU             |
| C4        |  25 |     6.188 |               61907.494 |               0.370 |            0.028 |            0.034 |         0.045 |           0.879 |            0.197 |          4.038 |   92.000 | LU 18, EZL,LU 4, LO 1    | Tottenham Court Road, Oxford Circus, Leicester Square      |
| C5        |  88 |    21.782 |               11621.745 |              -0.419 |            0.037 |            0.010 |         0.056 |           0.748 |            0.305 |         12.527 |   53.409 | LU 38, LO 19, EZL 12     | Barking, Woolwich EL, Romford                              |
| C6        |  53 |    13.119 |               10361.209 |              -0.024 |            0.018 |            0.003 |         0.026 |           0.778 |            0.335 |          7.219 |   41.509 | LO 31, LU 16, LO,LU 4    | Euston LU, Farringdon, Clapham Junction                    |
| C7        |  51 |    12.624 |                6723.915 |              -0.480 |            0.037 |            0.013 |         0.053 |           0.683 |            0.332 |         18.791 |   68.627 | LU 29, LO 10, EZL 5      | Wimbledon, Richmond, Parsons Green                         |

### K=9

| cluster   |   n |   share_% |   median_total_activity |   direction_balance |   midnight_share |   night_tube_ext |   persistence |   weekend_ratio |   zero_bin_share |   km_to_centre |   pct_LU | top_modes             | example_stations                                           |
|:----------|----:|----------:|------------------------:|--------------------:|-----------------:|-----------------:|--------------:|----------------:|-----------------:|---------------:|---------:|:----------------------|:-----------------------------------------------------------|
| C0        |  49 |    12.129 |                7980.811 |              -0.087 |            0.017 |            0.001 |         0.023 |           0.748 |            0.362 |          8.884 |   34.694 | LO 32, LU 14, LO,LU 2 | Moorgate, Knightsbridge, Sloane Square                     |
| C1        |  31 |     7.673 |               12490.851 |              -0.112 |            0.070 |            0.012 |         0.117 |           0.839 |            0.315 |          8.270 |    6.452 | DLR 27, LU 2, EZL 1   | Shadwell LO, Woolwich Arsenal, Lewisham DLR                |
| C2        |  23 |     5.693 |               28297.058 |              -0.221 |            0.045 |            0.080 |         0.075 |           0.960 |            0.161 |          6.851 |   95.652 | LU 20, LO,LU 2, LO 1  | Brixton LU, Camden Town, Highbury & Islington              |
| C3        |  25 |     6.188 |               61907.494 |               0.367 |            0.028 |            0.034 |         0.045 |           0.874 |            0.197 |          3.970 |   92.000 | LU 18, EZL,LU 4, LO 1 | Tottenham Court Road, Oxford Circus, Leicester Square      |
| C4        |  43 |    10.644 |                5503.927 |              -0.523 |            0.043 |            0.017 |         0.062 |           0.695 |            0.312 |         21.144 |   74.419 | LU 27, LO 8, LO,LU 4  | Wimbledon, Richmond, Crystal Palace                        |
| C5        |  50 |    12.376 |               11795.595 |              -0.396 |            0.034 |            0.009 |         0.051 |           0.747 |            0.324 |         10.026 |   58.000 | LU 23, LO 14, LO,LU 6 | Woolwich EL, Marylebone LU, Harrow-on-the-Hill             |
| C6        |  76 |    18.812 |               19296.329 |              -0.418 |            0.044 |            0.071 |         0.068 |           0.791 |            0.159 |         10.628 |   97.368 | LU 66, LO,LU 4, LO 2  | Stratford, Vauxhall LU, Ealing Broadway                    |
| C7        |  43 |    10.644 |               12751.809 |              -0.467 |            0.040 |            0.017 |         0.059 |           0.718 |            0.271 |         15.341 |   53.488 | LU 20, EZL 11, DLR 4  | Barking, Romford, Abbey Wood                               |
| C8        |  64 |    15.842 |               26357.428 |              -0.039 |            0.029 |            0.016 |         0.045 |           0.872 |            0.251 |          4.946 |   75.000 | LU 38, LO 13, LO,LU 5 | Liverpool Street LU, King's Cross St. Pancras, Waterloo LU |
