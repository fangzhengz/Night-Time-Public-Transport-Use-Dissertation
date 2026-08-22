# Rail weekend metric: window and day-grouping sensitivity

Read-only sidecar. Does not refit clustering; does not touch
rq2_new_clusters_analysis's canonical outputs.

## Why this was run

Table verification (2026-08-20) found that Rail's `weekend_common_ratio`
restricts to an 18:00-01:00 "common window" and drops Friday from both
the weekday and weekend groups, while Bus's `weekend_ratio` uses the full
18:00-05:00 window and necessarily folds Friday into `Weekday` (BUSTO
cannot separate FRI from Weekday at source). The common-window
restriction was a real constraint pre-padding (MON/TWT/SUN genuinely had
no data past 01:00) but the 2026-08-02 padded-window adoption gave every
day type a full 18:00-05:00 window; the restriction on this one metric
was never revisited afterwards.

## What changes empirically

- Post-01:00 activity is 0.05%/0.07% of the MON/TWT day total but
  0.90% (FRI) and 1.33% (SAT) -- i.e. extending the window mechanically
  adds real Night Tube activity to the weekend group (via SAT) while
  adding almost nothing to the weekday group, so widening the window
  alone is expected to push the ratio up, not just add noise.

## Cluster-coherence result (Kruskal-Wallis epsilon-squared vs. the
existing rail_allmodes K=5 labels)

| variant                              |   n |   k |   kruskal_H |   kruskal_p |   epsilon_squared |
|:-------------------------------------|----:|----:|------------:|------------:|------------------:|
| canonical_common_window_fri_excluded | 403 |   5 |    115.4731 |      0.0000 |            0.2801 |
| full_window_fri_excluded             | 403 |   5 |    118.1264 |      0.0000 |            0.2867 |
| full_window_bus_aligned              | 403 |   5 |    110.9747 |      0.0000 |            0.2688 |

## Per-cluster medians

|   cluster |   canonical_common_window_fri_excluded |   full_window_fri_excluded |   full_window_bus_aligned |
|----------:|---------------------------------------:|---------------------------:|--------------------------:|
|         0 |                                  0.663 |                      0.673 |                     0.665 |
|         1 |                                  0.916 |                      0.943 |                     0.857 |
|         2 |                                  0.826 |                      0.83  |                     0.782 |
|         3 |                                  0.888 |                      0.903 |                     0.848 |
|         4 |                                  0.796 |                      0.823 |                     0.786 |

## Rank stability (Spearman correlation across the 403 stations)

|                                      |   canonical_common_window_fri_excluded |   full_window_fri_excluded |   full_window_bus_aligned |
|:-------------------------------------|---------------------------------------:|---------------------------:|--------------------------:|
| canonical_common_window_fri_excluded |                                  1     |                      0.989 |                     0.978 |
| full_window_fri_excluded             |                                  0.989 |                      1     |                     0.983 |
| full_window_bus_aligned              |                                  0.978 |                      0.983 |                     1     |

## Reading

See `outputs/figures/weekend_window_sensitivity.png` and the CSVs in
`outputs/data/` for the full comparison.