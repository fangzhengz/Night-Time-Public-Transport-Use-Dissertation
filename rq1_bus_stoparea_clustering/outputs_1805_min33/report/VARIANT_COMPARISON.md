## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: validate
- Verification Status: ANALYZED
- Version Label: stoparea_variant_comparison_v1

# StopArea raw-share and CLR comparison

| comparison                    |   K |   n_left |   n_right |   n_common |   ARI_common_units |   mean_matched_cluster_jaccard |   min_matched_cluster_jaccard |
|:------------------------------|----:|---------:|----------:|-----------:|-------------------:|-------------------------------:|------------------------------:|
| new_stoparea_raw_share_vs_clr |   3 |     3383 |      3383 |       3383 |           0.336030 |                       0.512148 |                      0.290228 |
| new_stoparea_raw_share_vs_clr |   4 |     3383 |      3383 |       3383 |           0.357863 |                       0.388679 |                      0.025610 |

ARI and matched Jaccard describe partition agreement, not substantive model quality.
Both partitions use exactly the same LSOAs and differ only in the feature transform.