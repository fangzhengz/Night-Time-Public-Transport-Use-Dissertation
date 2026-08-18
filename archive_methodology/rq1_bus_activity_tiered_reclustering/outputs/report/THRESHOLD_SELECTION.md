# Bus activity-threshold selection (evidence-based, not a median split)

## Noise mechanism check

|   spearman_r_shape_variance_vs_activity |   spearman_p_shape_variance_vs_activity |   spearman_r_shape_spikiness_vs_activity |   spearman_p_shape_spikiness_vs_activity |
|----------------------------------------:|----------------------------------------:|-----------------------------------------:|-----------------------------------------:|
|                               -0.716457 |                                       0 |                                -0.635604 |                                        0 |

Strong negative correlation confirms low-activity LSOAs have
systematically noisier/spikier share vectors (small-count compositional
noise), not a real absence of rhythm structure.

## Threshold grid (forced K=3 for comparability; BIC-best K for reference)

|   threshold |   n_units |   pct_of_all_units |   bic_best_K_full_cov |   forced_K |   geo_eta2_distance |   eta2_log_total_activity |   eta2_direction_balance |   eta2_post_midnight_share |   eta2_deep_night_share |   eta2_post_midnight_persistence |   eta2_weekend_ratio |
|------------:|----------:|-------------------:|----------------------:|-----------:|--------------------:|--------------------------:|-------------------------:|---------------------------:|------------------------:|---------------------------------:|---------------------:|
|           0 |      4100 |              100   |                     4 |          3 |           0.0486394 |                 0.489659  |                0.0106254 |                   0.257151 |                0.168143 |                         0.226193 |            0.030778  |
|         450 |      2452 |               59.8 |                     2 |          3 |           0.0645788 |                 0.0984008 |                0.0549659 |                   0.279525 |                0.280837 |                         0.261128 |            0.0544314 |
|         650 |      2039 |               49.7 |                     2 |          3 |           0.0687279 |                 0.0663046 |                0.0739335 |                   0.317724 |                0.301441 |                         0.295278 |            0.0742175 |

## Recommendation

Lowest threshold at which activity_eta2 drops below the mean of the three
late-night timing metrics' eta2: **450**