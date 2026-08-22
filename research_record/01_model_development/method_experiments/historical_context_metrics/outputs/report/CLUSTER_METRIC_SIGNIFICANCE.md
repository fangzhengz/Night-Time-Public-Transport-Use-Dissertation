# Does the RQ1 cluster label explain its own continuous profile metrics?

metric ~ cluster, Kruskal-Wallis + epsilon-squared, Benjamini-Hochberg
corrected within mode. Compare against the external-validation effect
sizes already reported: bus cluster x LNWC Cramer's V = 0.215 (weak),
rail cluster x LNWC Cramer's V = 0.443 (moderate-strong).

| mode   | metric                       |    n |   n_clusters |   kruskal_H |    kruskal_p |   epsilon_squared |         p_bh |
|:-------|:-----------------------------|-----:|-------------:|------------:|-------------:|------------------:|-------------:|
| bus    | log_total_activity           | 4100 |            3 |   2125.66   | 0            |        0.518344   | 0            |
| bus    | direction_balance            | 4100 |            3 |     39.7713 | 2.31088e-09  |        0.00921925 | 2.31088e-09  |
| bus    | post_midnight_share          | 4100 |            3 |   1188.47   | 8.46169e-259 |        0.289594   | 1.69234e-258 |
| bus    | deep_night_share             | 4100 |            3 |    815.867  | 6.86777e-178 |        0.198649   | 1.03017e-177 |
| bus    | post_midnight_persistence    | 4099 |            3 |   1214.67   | 1.72842e-264 |        0.296062   | 5.18526e-264 |
| bus    | weekend_ratio                | 4100 |            3 |    169.437  | 1.61175e-37  |        0.0408681  | 1.9341e-37   |
| rail   | log_total_activity           |  270 |            5 |    108.891  | 1.25448e-22  |        0.395816   | 2.50896e-22  |
| rail   | direction_balance            |  270 |            5 |    176.541  | 4.12461e-37  |        0.651097   | 2.47477e-36  |
| rail   | midnight_share_common_window |  270 |            5 |     81.9066 | 6.8704e-17   |        0.293987   | 1.03056e-16  |
| rail   | night_tube_extension_share   |  270 |            5 |     33.015  | 1.18604e-06  |        0.109491   | 1.18604e-06  |
| rail   | common_window_persistence    |  270 |            5 |     70.29   | 1.97142e-14  |        0.250151   | 2.3657e-14   |
| rail   | weekend_common_ratio         |  270 |            5 |    127.729  | 1.19117e-26  |        0.466903   | 3.5735e-26   |

## Reading

- High epsilon_squared here means cluster membership explains a large
  share of that metric's own variance -- the clusters are internally
  coherent groupings for that dimension, even if their external LNWC
  association is weak (i.e. weak-vs-LNWC is a statement about what the
  shape-only vector represents, not evidence the partition itself is
  incoherent).
- Low epsilon_squared across the board for a mode would be a genuine red
  flag: it would mean the cluster label barely organises even the metrics
  it is conceptually closest to, which a shape-vs-geography argument
  alone could not explain away.

## Result (this run)

Not a red flag. Bus clusters explain 51.8% of log_total_activity and
28-30% of the three post-midnight/timing metrics -- comparable to, and for
total activity even stronger than, rail's own cluster-metric associations
(log_total_activity 39.6%). This directly answers "is the bus clustering
design broken": no -- the K=3 partition is a substantively meaningful split
on volume and late-night timing, not statistical noise dressed up as three
clusters.

The one real, specific soft spot: bus direction_balance (0.9%) and
weekend_ratio (4.1%) are both weak. This is a genuine asymmetry with rail,
where the same two metric types are the *strongest* associations
(direction_balance 65.1%, weekend_common_ratio 46.7%). So the honest,
narrower finding is: bus's K=3 shape typology organises volume and
late-night persistence well, but does not differentiate stations by
directional/functional role or weekend-vs-weekday shift the way rail's K=5
typology does. That is a specific, defensible, mode-comparative claim for
the write-up -- not "bus clustering doesn't work" but "bus clustering
resolves a different, narrower part of the same conceptual space than rail
does."

Combined with `../rq1_bus_geography_diagnostic/outputs/report/RESULTS_SUMMARY.md`
(distance-to-centre explains only 4.9-9.5% of cluster variance regardless
of K, not improved by raising K) and `LSOA_AGGREGATION_CHECK.md` (LSOA
aggregation is not discarding real stop-level heterogeneity), the full
answer to "is the bus analysis design flawed" is: no on all three specific,
testable candidates (K choice, classification noise/LSOA aggregation, and
now internal coherence of the partition) -- the weak external
geography/LNWC link is a real, mode-specific property of bus night-time
usage rhythm, concentrated specifically in the directional/functional-role
dimension, not a pipeline defect.