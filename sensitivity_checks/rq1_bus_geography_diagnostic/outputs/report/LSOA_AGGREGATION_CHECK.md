# Bus stop-to-LSOA aggregation variance decomposition

Tests whether LSOA-level aggregation (used before bus clustering) discards
real stop-to-stop heterogeneity. High eta_squared_lsoa means most of the
stop-to-stop variance sits BETWEEN LSOAs, i.e. stops inside the same LSOA
already behave similarly -- aggregation is not hiding real structure.

| item                          |   value |
|:------------------------------|--------:|
| n_stops_matched_to_lsoa       |   18449 |
| n_lsoa_with_at_least_one_stop |    4110 |
| median_stops_per_lsoa         |       4 |
| n_lsoa_with_exactly_1_stop    |     593 |

| metric              |   n_stops |   eta_squared_lsoa |
|:--------------------|----------:|-------------------:|
| log_total_activity  |     18449 |           0.633677 |
| post_midnight_share |     18379 |           0.42949  |
| weekend_ratio       |     18362 |           0.800832 |