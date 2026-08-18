# ILR profiles, maps and geographic validation

## Howard central-versus-outer check

|      K |   n_matched |   central_outer_total_variation |   central_outer_same_cluster_probability |
|-------:|------------:|--------------------------------:|-----------------------------------------:|
| 3.0000 |    330.0000 |                          0.3565 |                                   0.3575 |
| 4.0000 |    330.0000 |                          0.3515 |                                   0.3528 |

## Direct CLR label agreement

|        K |   ARI_ilr_vs_clr |
|---------:|-----------------:|
| 3.000000 |         1.000000 |
| 4.000000 |         1.000000 |

The Howard check is descriptive validation only; geography is not used as an
input feature. Cluster numbers and colours are not aligned across unrelated
models, so ARI rather than numeric label equality is used for comparison.
