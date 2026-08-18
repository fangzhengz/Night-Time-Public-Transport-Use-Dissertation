# First-pass results: hub-first full-week bus reclustering

## Verdict scope

This run fits **one full-week bus GMM**, not separate weekday/weekend models. It
preserves the historical 72-feature structure and GMM/BIC family while changing
the spatial assembly, exception handling, and low-flow treatment. The BIC minimum
reported below is a candidate, not a final substantive choice of K.

## Frozen inputs and sample

- Input LSOAs: 3790
- Full-week activity >= 50.0: 3597
- Union of documented group-level one-direction exception LSOAs: 14
- Exceptions that otherwise met the full-week threshold: 4
- Retained for clustering: **3593**
- Features: 72 (two separately normalised 36-bin full-week directions)
- Empirical shrinkage alpha: 5.0
- Feature row-sum check: 2.000000 to 2.000000 (expected 2)

### Block audit

| direction   |   n_lsoa |   n_raw_zero_total | prior_peak_day   |   prior_peak_hour |   prior_peak_share |   median_raw_total |   p05_raw_total |   median_tv_nonzero |   p95_tv_nonzero |
|:------------|---------:|-------------------:|:-----------------|------------------:|-------------------:|-------------------:|----------------:|--------------------:|-----------------:|
| boardings   |     3593 |                  0 | Weekday          |              1080 |           0.101691 |            300.341 |         36.7693 |          0.00261989 |        0.0351852 |
| alightings  |     3593 |                  0 | Weekday          |              1080 |           0.10602  |            428.038 |         52.434  |          0.00133206 |        0.0190967 |

## GMM/BIC result

Global BIC minimum: **covariance=full, K=3**.

| covariance   |   K |          BIC |   min_cluster_n |   min_cluster_share | converged   |
|:-------------|----:|-------------:|----------------:|--------------------:|:------------|
| diag         |  12 | -1.96578e+06 |              94 |          0.026162   | True        |
| full         |   3 | -2.07951e+06 |             494 |          0.13749    | True        |
| spherical    |  12 | -1.67687e+06 |             151 |          0.0420262  | True        |
| tied         |  12 | -2.04775e+06 |              33 |          0.00918453 | True        |

## K diagnostics at covariance=full

Bootstrap uses 20 full-size resamples. `bootstrap_ari_mean` measures
global agreement; `bootstrap_min_cluster_jaccard_mean` measures recovery of the
weakest matched cluster and is the safeguard against pseudo-reliability.

|   K |          BIC |   silhouette |   davies_bouldin |   min_cluster_n |   min_cluster_share |   median_max_posterior |   bootstrap_ari_mean |   bootstrap_min_cluster_jaccard_mean |
|----:|-------------:|-------------:|-----------------:|----------------:|--------------------:|-----------------------:|---------------------:|-------------------------------------:|
|   2 | -2.06687e+06 |    0.0933211 |          3.85064 |            1597 |           0.444475  |               1        |             0.596535 |                            0.736077  |
|   3 | -2.07951e+06 |    0.0497006 |          6.00326 |             494 |           0.13749   |               1        |             0.696439 |                            0.513036  |
|   4 | -2.07076e+06 |   -0.0137545 |          5.75965 |             337 |           0.0937935 |               0.999999 |             0.537512 |                            0.28742   |
|   5 | -2.05437e+06 |   -0.0263541 |          6.27944 |             230 |           0.0640134 |               0.999998 |             0.572342 |                            0.212719  |
|   6 | -2.03834e+06 |   -0.0342553 |          5.89384 |             156 |           0.0434178 |               0.999997 |             0.500474 |                            0.0663781 |
|   7 | -2.02107e+06 |   -0.0291    |          4.83827 |             135 |           0.0375731 |               0.999997 |             0.518064 |                            0.100252  |
|   8 | -2.00332e+06 |   -0.0235219 |          4.60423 |             115 |           0.0320067 |               0.999998 |             0.532883 |                            0.0328299 |
|   9 | -1.98507e+06 |   -0.0373506 |          5.7068  |              83 |           0.0231005 |               0.999977 |           nan        |                          nan         |
|  10 | -1.96485e+06 |   -0.0320352 |          4.99391 |              91 |           0.025327  |               0.999997 |           nan        |                          nan         |
|  11 | -1.94807e+06 |   -0.0366523 |          4.73166 |              76 |           0.0211522 |               0.999998 |           nan        |                          nan         |
|  12 | -1.92759e+06 |   -0.0287284 |          4.18384 |              69 |           0.019204  |               0.999999 |           nan        |                          nan         |

## Automatic warnings

- The BIC-best silhouette is below 0.05, indicating weak geometric separation.

## Adjacent-K structure

High child-to-parent purity means K+1 is largely splitting clusters already
present at K. A tiny smallest child is evidence against treating the new piece
as a robust new type without substantive support.

|   K_parent |   K_child |   ARI_adjacent |   weighted_child_to_parent_purity |   n_parent_clusters_receiving_multiple_children |   smallest_child_n |   smallest_child_share |
|-----------:|----------:|---------------:|----------------------------------:|------------------------------------------------:|-------------------:|-----------------------:|
|          2 |         3 |       0.640967 |                          0.938492 |                                               1 |                494 |              0.13749   |
|          3 |         4 |       0.508885 |                          0.852213 |                                               1 |                337 |              0.0937935 |
|          4 |         5 |       0.752727 |                          0.891734 |                                               1 |                230 |              0.0640134 |
|          5 |         6 |       0.723595 |                          0.855552 |                                               1 |                156 |              0.0434178 |
|          6 |         7 |       0.782801 |                          0.897579 |                                               1 |                135 |              0.0375731 |
|          7 |         8 |       0.555499 |                          0.728082 |                                               1 |                115 |              0.0320067 |
|          8 |         9 |       0.391215 |                          0.65405  |                                               3 |                 83 |              0.0231005 |
|          9 |        10 |       0.473423 |                          0.64403  |                                               2 |                 91 |              0.025327  |
|         10 |        11 |       0.624576 |                          0.763986 |                                               1 |                 76 |              0.0211522 |
|         11 |        12 |       0.560621 |                          0.712775 |                                               1 |                 69 |              0.019204  |

## Historical full-week comparison

The BIC magnitudes are not directly comparable across the two feature matrices;
the table is included only to document model-selection movement.

| version                            |   n_lsoa |   n_features | BIC_best_covariance   |   BIC_best_K |          BIC |
|:-----------------------------------|---------:|-------------:|:----------------------|-------------:|-------------:|
| old_fullweek_direct_lsoa_raw_share |     4100 |           72 | full                  |            3 | -2.29763e+06 |

The following ARI compares old and new labels for the same K on shared LSOAs.
It measures sensitivity to the combined pipeline changes and cannot attribute
the change separately to hub assembly, exclusion, or shrinkage.

|   K |   n_old |   n_new |   n_common |   old_new_ARI_on_common |
|----:|--------:|--------:|-----------:|------------------------:|
|   3 |    4100 |    3593 |       3557 |                0.266024 |
|   4 |    4100 |    3593 |       3557 |                0.310783 |
|   5 |    4100 |    3593 |       3557 |                0.312528 |
|   6 |    4100 |    3593 |       3557 |                0.29334  |
|   7 |    4100 |    3593 |       3557 |                0.310256 |
|   8 |    4100 |    3593 |       3557 |                0.350728 |

## Interpretation boundary and next decision

This first pass can identify plausible candidate K values and detect tiny or
unstable clusters. It does not yet prove that alpha=5 is uniquely preferable.
The final K should be frozen only after reviewing BIC, small-cluster recovery,
adjacent-K splits, temporal profiles, and spatial maps together. If this result
is materially improved, the minimum sensitivity set is alpha=0 versus alpha=5
on the same retained sample, followed by a fixed-sample bootstrap comparison.
