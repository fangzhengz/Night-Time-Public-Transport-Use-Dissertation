# RQ2 sensitivity clusters -- continuous variable layer + internal coherence

## Material Passport

- Origin Date: 2026-08-12T21:28:53.994843+00:00
- Verification Status: ANALYZED
- Version Label: rq2_new_clusters_context_v1

## Scope

- Rail: all-modes merged sensitivity clustering, K=5 (403 stations, vs canonical's 270 Underground-only).
- Bus: StopArea CLR sensitivity clustering, K=4 (3383 LSOAs, vs canonical's 3,372 at min36).
- The fixed GMM labels are retained as-is; volume/timing context is added after clustering, not used to refit it.

## Does the cluster label explain its own continuous profile? (Kruskal-Wallis + epsilon-squared, BH-corrected within mode)

| mode   | metric                    |    n |   n_clusters |   kruskal_H |   kruskal_p |   epsilon_squared |        p_bh |
|:-------|:--------------------------|-----:|-------------:|------------:|------------:|------------------:|------------:|
| rail   | log_total_activity        |  403 |            5 |     90.7863 | 8.96305e-19 |         0.218056  | 8.96305e-19 |
| rail   | direction_balance         |  403 |            5 |    256.49   | 2.60205e-54 |         0.634397  | 1.04082e-53 |
| rail   | post_2300_share           |  403 |            5 |    168.168  | 2.58552e-35 |         0.412483  | 5.17105e-35 |
| rail   | weekend_common_ratio      |  403 |            5 |    115.473  | 4.94599e-24 |         0.280083  | 6.59465e-24 |
| bus    | log_total_activity        | 3383 |            4 |   2033.51   | 0           |         0.600921  | 0           |
| bus    | direction_balance         | 3383 |            4 |    207.648  | 9.38851e-45 |         0.0605645 | 9.38851e-45 |
| bus    | post_2300_share           | 3383 |            4 |   1592.36   | 0           |         0.470363  | 0           |
| bus    | deep_night_share          | 3383 |            4 |   1939.72   | 0           |         0.573162  | 0           |
| bus    | post_midnight_persistence | 3383 |            4 |   1928.97   | 0           |         0.569982  | 0           |
| bus    | weekend_ratio             | 3383 |            4 |    260.488  | 3.52534e-56 |         0.0762025 | 4.2304e-56  |

## Interpretation limits

- `post_2300_share` uses 23:00-05:00 over 18:00-05:00 for both modes. The time threshold and window are aligned, but the mode-native activity definitions still preclude a pooled comparison.
- Volume bands are mode-specific tertiles and are not cross-mode equivalents.
- A high volume or late-night share is observed use, not evidence of unmet demand.
- Rail late-night extension partly reflects service availability, not a pure behavioural measure.
- Bus `post_2300_share` is recomputed here from the audited StopArea long table; its other continuous metrics are taken as-is from `rq1_bus_stoparea_clustering`'s feature-preparation audit.