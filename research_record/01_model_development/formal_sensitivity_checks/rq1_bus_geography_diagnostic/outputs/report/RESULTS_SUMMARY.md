# Bus cluster geography diagnostic

Reproduces (as a saved, citable script) the 17 July 2026 ad-hoc check of
whether the bus K=3 LSOA cluster map's inner/outer London mixing is a real
feature of the data or an artifact of K choice / classification noise.
Centrality reference: Charing Cross, BNG (530134, 180379) -- same point
used by the RQ2 centrality-adjusted LNWC/IMD tests.

## 1. Does distance-to-centre organise cluster membership, and does raising K help?

|   k |   n_units |   n_missing_coords |   eta_squared_distance |   kruskal_H |   kruskal_p |   kruskal_epsilon_squared |
|----:|----------:|-------------------:|-----------------------:|------------:|------------:|--------------------------:|
|   3 |      4100 |                  0 |              0.0486394 |     188.686 | 1.0648e-41  |                 0.0455666 |
|   4 |      4100 |                  0 |              0.0952995 |     384.545 | 4.92867e-83 |                 0.0931505 |
|   5 |      4100 |                  0 |              0.090719  |     366.655 | 4.44042e-78 |                 0.0885605 |
|   6 |      4100 |                  0 |              0.0951931 |     387.612 | 1.38628e-81 |                 0.0934568 |

## 2. Is the mixing caused by uncertain (low-confidence) classification?

| pair                                |   spearman_r |
|:------------------------------------|-------------:|
| max_posterior vs distance_to_centre |    -0.134276 |
| max_posterior vs total_activity     |     0.230215 |
| entropy vs distance_to_centre       |     0.104955 |

| volume_band   |   median |     mean |   count |
|:--------------|---------:|---------:|--------:|
| low           |        1 | 0.993167 |    1359 |
| medium        |        1 | 0.993449 |    1370 |
| high          |        1 | 0.999849 |    1371 |

## Reading

- If eta_squared_distance stays low and roughly flat across K=3..6, raising K
  does not resolve the inner/outer mixing -- it is not a coarse-K artifact.
- If max_posterior correlations with distance/activity are close to zero and
  medians are high across all volume tertiles, the mixing is not driven by
  low-confidence/uncertain assignment.