# RQ3 x RQ1 cluster check: does the mismatch score relate to the dissertation's own typology?

The main analysis only interpreted residuals against the external LNWC classification. This checks the same residuals against RQ1's own rail (numbat_all_area_test, all-modes 403-station K=5) and bus (rq1_bus_stoparea_clustering, StopArea CLR K=4) cluster labels, which had been omitted -- a real gap, not a deliberate exclusion. Rail labels and descriptive names are the current 2026-08-07 rerun; names are loaded from the data-derived rail_cluster_names.csv rather than hard-coded here.

## origin

### Bus cluster (n=978 MSOAs)
| bus_cluster                     |   mean |   median |   count |
|:--------------------------------|-------:|---------:|--------:|
| C0 moderate-flow, directional   | -0.288 |   -0.52  |     154 |
| C1 high-flow, night-persistent  |  0.483 |    0.345 |     393 |
| C2 moderate-to-high flow        | -0.154 |   -0.269 |     260 |
| C3 low-flow, peripheral-leaning | -0.599 |   -0.6   |     171 |

### Rail cluster (n=279 MSOAs with a station)
| rail_cluster                                     |   mean |   median |   count |
|:-------------------------------------------------|-------:|---------:|--------:|
| C0 outer arrival-dominant                        |  0.42  |    0.369 |      68 |
| C1 central departure-dominant (night origin)     |  1.197 |    1.293 |      10 |
| C2 central interchange, direction-balanced       |  1.293 |    1.258 |      68 |
| C3 night-persistent inner & DLR                  |  1.298 |    1.088 |      18 |
| C4 inner/mid arrival-dominant, Night-Tube served |  0.923 |    0.804 |     115 |

## destination

### Bus cluster (n=978 MSOAs)
| bus_cluster                     |   mean |   median |   count |
|:--------------------------------|-------:|---------:|--------:|
| C0 moderate-flow, directional   | -0.268 |   -0.433 |     154 |
| C1 high-flow, night-persistent  |  0.458 |    0.342 |     393 |
| C2 moderate-to-high flow        | -0.131 |   -0.354 |     260 |
| C3 low-flow, peripheral-leaning | -0.595 |   -0.677 |     171 |

### Rail cluster (n=279 MSOAs with a station)
| rail_cluster                                     |   mean |   median |   count |
|:-------------------------------------------------|-------:|---------:|--------:|
| C0 outer arrival-dominant                        |  0.912 |    0.989 |      68 |
| C1 central departure-dominant (night origin)     |  0.632 |    0.519 |      10 |
| C2 central interchange, direction-balanced       |  1.12  |    1.179 |      68 |
| C3 night-persistent inner & DLR                  |  1.312 |    1.22  |      18 |
| C4 inner/mid arrival-dominant, Night-Tube served |  1.25  |    1.207 |     115 |
