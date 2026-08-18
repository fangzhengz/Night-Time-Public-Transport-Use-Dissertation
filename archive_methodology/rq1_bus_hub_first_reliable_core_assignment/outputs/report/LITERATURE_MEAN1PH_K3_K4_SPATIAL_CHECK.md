# Literature mean-1-per-hour analogue: K=3/K=4 spatial check

- Rule: retain only `min(tot_boardings, tot_alightings) >= 36`.
- Retained: 3,365/3,593 (93.65%).
- Excluded: 228/3,593 (6.35%).
- Models: alpha=0 hub-first features, full-covariance GMM, seed=42, n_init=20.

## Central-versus-outer diagnostic

|   k |   n_retained |   n_excluded |   pct_excluded | cluster_sizes     |   central_outer_total_variation |   central_outer_same_cluster_probability |
|----:|-------------:|-------------:|---------------:|:------------------|--------------------------------:|-----------------------------------------:|
|   3 |         3365 |          228 |         6.3457 | 1283;1621;461     |                          0.3690 |                                   0.3179 |
|   4 |         3365 |          228 |         6.3457 | 1147;1062;311;845 |                          0.4254 |                                   0.2344 |

`central_outer_total_variation` is 0 for identical cluster distributions and 1 for no overlap.
`central_outer_same_cluster_probability` is the probability that one random central and one random outer LSOA receive the same cluster label.

## Borough cluster composition

|   k | borough              |   cluster |   n |   within_borough_share |
|----:|:---------------------|----------:|----:|-----------------------:|
|   3 | Westminster          |         0 |  10 |                 0.1149 |
|   3 | Camden               |         0 |  18 |                 0.2045 |
|   3 | Kingston upon Thames |         0 |  33 |                 0.4714 |
|   3 | Richmond upon Thames |         0 |  49 |                 0.5765 |
|   3 | Westminster          |         1 |  44 |                 0.5057 |
|   3 | Camden               |         1 |  57 |                 0.6477 |
|   3 | Kingston upon Thames |         1 |  28 |                 0.4000 |
|   3 | Richmond upon Thames |         1 |  26 |                 0.3059 |
|   3 | Westminster          |         2 |  33 |                 0.3793 |
|   3 | Camden               |         2 |  13 |                 0.1477 |
|   3 | Kingston upon Thames |         2 |   9 |                 0.1286 |
|   3 | Richmond upon Thames |         2 |  10 |                 0.1176 |
|   4 | Westminster          |         0 |   7 |                 0.0805 |
|   4 | Camden               |         0 |  18 |                 0.2045 |
|   4 | Kingston upon Thames |         0 |  30 |                 0.4286 |
|   4 | Richmond upon Thames |         0 |  44 |                 0.5176 |
|   4 | Westminster          |         1 |  49 |                 0.5632 |
|   4 | Camden               |         1 |  46 |                 0.5227 |
|   4 | Kingston upon Thames |         1 |  15 |                 0.2143 |
|   4 | Richmond upon Thames |         1 |  19 |                 0.2235 |
|   4 | Westminster          |         2 |  21 |                 0.2414 |
|   4 | Camden               |         2 |   7 |                 0.0795 |
|   4 | Kingston upon Thames |         2 |   3 |                 0.0429 |
|   4 | Richmond upon Thames |         2 |   6 |                 0.0706 |
|   4 | Westminster          |         3 |  10 |                 0.1149 |
|   4 | Camden               |         3 |  17 |                 0.1932 |
|   4 | Kingston upon Thames |         3 |  22 |                 0.3143 |
|   4 | Richmond upon Thames |         3 |  16 |                 0.1882 |

This is a targeted diagnostic of Howard's central/outer mixing concern, not evidence that geographic distance was used in the GMM.