# Bus CLR test: point-in-polygon (pre-StopArea) allocation

## Sample and design

Input long table: frozen local copy of the pre-StopArea point-in-polygon
LSOA allocation (`../input/bus_lsoa_night_long_point_in_polygon.parquet`,
copied 2026-07-29 from `FYP/旧分析归档/cluster_clean_version_grouped/
outputs/preprocessed/bus_lsoa_night_long.parquet`). n_input=4,111
LSOAs with any night demand; n_retained=3,596 after the single retention
rule `min(boardings, alightings) full-week total >= 36`.

Feature transform: centered log-ratio (CLR) within each of the two
independent 36-bin (3 day types x 12 hours) direction compositions,
alpha=1 empirical-prior pseudo-count applied only to avoid log(0). Temporal
profile figures are plotted in raw-share space regardless, per this
project's convention that CLR values are not directly interpretable as
"share of activity in this hour".

## BIC result

| covariance   |   K |     BIC |   min_cluster_n |   min_cluster_share |
|:-------------|----:|--------:|----------------:|--------------------:|
| diag         |  12 |  433254 |             213 |           0.0592325 |
| full         |   3 | -390605 |             938 |           0.260845  |
| spherical    |  12 |  576337 |             150 |           0.041713  |
| tied         |  12 | -267545 |              81 |           0.022525  |

Global BIC minimum family used directly; no override needed.

Reporting family: **full**.

## K diagnostics

|       K |          BIC |   silhouette |   activity_eta2 |   timing_mean_eta2 |   direction_balance_eta2 |   weekend_ratio_eta2 |   min_cluster_share |   bootstrap_ari_mean |   bootstrap_min_cluster_jaccard_mean |
|--------:|-------------:|-------------:|----------------:|-------------------:|-------------------------:|---------------------:|--------------------:|---------------------:|-------------------------------------:|
|  2.0000 | -291832.1641 |       0.2398 |          0.5197 |             0.0832 |                   0.0139 |               0.0390 |              0.4221 |               0.4109 |                               0.6670 |
|  3.0000 | -390605.2391 |       0.1787 |          0.5579 |             0.1608 |                   0.0251 |               0.0603 |              0.2608 |               0.8804 |                               0.8948 |
|  4.0000 | -390485.0552 |       0.1498 |          0.5524 |             0.1648 |                   0.0271 |               0.0648 |              0.0640 |               0.8794 |                               0.6855 |
|  5.0000 | -381735.2955 |       0.1405 |          0.5674 |             0.1743 |                   0.0298 |               0.0645 |              0.0145 |               0.8126 |                               0.2129 |
|  6.0000 | -370538.3599 |       0.1343 |          0.5669 |             0.1715 |                   0.0293 |               0.0691 |              0.0203 |               0.7304 |                               0.0254 |
|  7.0000 | -360112.3353 |       0.1268 |          0.5735 |             0.1680 |                   0.0300 |               0.0671 |              0.0178 |               0.6460 |                               0.0259 |
|  8.0000 | -349671.4747 |       0.0595 |          0.6255 |             0.2034 |                   0.0586 |               0.0719 |              0.0359 |               0.6261 |                               0.0707 |
|  9.0000 | -333596.6568 |       0.0598 |          0.6300 |             0.1904 |                   0.0530 |               0.0682 |              0.0145 |             nan      |                             nan      |
| 10.0000 | -322724.4702 |       0.0560 |          0.6332 |             0.2000 |                   0.0623 |               0.0657 |              0.0103 |             nan      |                             nan      |
| 11.0000 | -300237.1354 |       0.0631 |          0.6143 |             0.2138 |                   0.0591 |               0.0737 |              0.0122 |             nan      |                             nan      |
| 12.0000 | -287732.8846 |       0.0217 |          0.6472 |             0.2396 |                   0.0632 |               0.0792 |              0.0120 |             nan      |                             nan      |

## Comparison across the three allocation methods (CLR, K=3)

| | point-in-polygon (this test) | hub-first (`rq1_bus_clr_transform`) | official StopArea (canonical) |
|---|---:|---:|---:|
| n | 3,596 | 3,365 | 3,372 |
| silhouette | 0.1787 | 0.1932 | 0.1996 |
| activity_eta2 | 0.5579 | 0.5585 | 0.5578 |
| timing_mean_eta2 | 0.1608 | 0.1893 | 0.1885 |
| direction_balance_eta2 | 0.0251 | 0.0473 | 0.0459 |
| weekend_ratio_eta2 | 0.0603 | 0.0512 | 0.0522 |
| bootstrap_ari_mean | 0.8804 | 0.8618 | 0.8742 |
| bootstrap_min_cluster_jaccard_mean | 0.8948 | n/a (not computed) | 0.8830 |

The hub-first and StopArea columns are frozen figures from prior runs, not
recomputed here. If this test's numbers land in the same range, that is
evidence the CLR clustering result is driven by the transform and the
min-direction threshold rather than by the choice of LSOA allocation method.
