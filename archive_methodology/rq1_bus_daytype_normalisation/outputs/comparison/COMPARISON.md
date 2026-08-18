# Day-type closure vs full-week closure: bus

Sidecar result, 2026-08-01. Not an adopted result.

## What differs between the two sides

Only the denominator. Allocation (StopArea), window (18:00-06:00), granularity (hourly), retention (both direction week totals >= 36), GMM grid, seed, n_init and bootstrap protocol are identical. The strict variant additionally requires every one of the six (direction x day type) blocks to clear 36, which is the one place the sample changes.

## BIC selection

| variant                  | bic_covariance   |   bic_K |   bic_min_cluster_n |   runner_up_K |   bic_margin_over_runner_up |
|:-------------------------|:-----------------|--------:|--------------------:|--------------:|----------------------------:|
| daytype_raw_share        | full             |       3 |                 552 |             4 |                      5523.9 |
| daytype_clr_a1           | full             |       5 |                 377 |             6 |                     17401.0 |
| daytype_clr_a033         | full             |       6 |                  64 |             4 |                       728.4 |
| daytype_raw_share_strict | tied             |      12 |                   1 |            11 |                       997.6 |

## Diagnostics at the candidate Ks

| variant                  | closure   |   K |    n |   silhouette |   activity_eta2 |   zero_bin_eta2 |   timing_mean_eta2 |   weekend_ratio_eta2 |   central_outer_tv |   bootstrap_ari_mean |   bootstrap_min_jaccard |   ari_vs_canon_raw_k3 |   ari_vs_canon_clr_k4 |
|:-------------------------|:----------|----:|-----:|-------------:|----------------:|----------------:|-------------------:|---------------------:|-------------------:|---------------------:|------------------------:|----------------------:|----------------------:|
| canon_raw_share          | full-week |   3 | 3372 |       0.0574 |          0.5020 |          0.5395 |             0.2789 |               0.0346 |             0.3756 |               0.6216 |                  0.4221 |              nan      |              nan      |
| canon_raw_share          | full-week |   4 | 3372 |       0.0323 |          0.5401 |          0.5827 |             0.3072 |               0.0664 |             0.4176 |               0.7823 |                  0.5221 |              nan      |              nan      |
| canon_clr                | full-week |   3 | 3372 |       0.1996 |          0.5578 |          0.8304 |             0.1885 |               0.0522 |             0.3527 |               0.8742 |                  0.8827 |              nan      |              nan      |
| canon_clr                | full-week |   4 | 3372 |       0.1519 |          0.5731 |          0.9188 |             0.1950 |               0.0581 |             0.3607 |               0.7861 |                  0.4010 |              nan      |              nan      |
| daytype_raw_share        | day-type  |   3 | 3372 |       0.0748 |          0.4164 |          0.7859 |             0.2613 |               0.0425 |             0.1971 |               0.6388 |                  0.4795 |                0.5835 |                0.3783 |
| daytype_raw_share        | day-type  |   4 | 3372 |       0.0415 |          0.4589 |          0.7659 |             0.2735 |               0.0674 |             0.3023 |               0.7187 |                  0.4500 |                0.5548 |                0.3561 |
| daytype_clr_a1           | day-type  |   3 | 3372 |       0.2419 |          0.4960 |          0.8661 |             0.1853 |               0.0530 |             0.3273 |               0.8555 |                  0.7490 |                0.4275 |                0.5015 |
| daytype_clr_a1           | day-type  |   4 | 3372 |       0.2002 |          0.5168 |          0.9132 |             0.1931 |               0.0557 |             0.3417 |               0.9009 |                  0.7219 |                0.4335 |                0.5597 |
| daytype_clr_a033         | day-type  |   3 | 3372 |       0.3124 |          0.4410 |          0.8891 |             0.1846 |               0.0516 |             0.2623 |               0.9280 |                  0.8369 |                0.4100 |                0.4564 |
| daytype_clr_a033         | day-type  |   4 | 3372 |       0.2654 |          0.4601 |          0.9229 |             0.1816 |               0.0557 |             0.2623 |               0.8307 |                  0.4891 |                0.3768 |                0.5292 |
| daytype_raw_share_strict | day-type  |   3 | 2493 |       0.1000 |          0.1383 |          0.0277 |             0.2494 |               0.0810 |             0.3430 |               0.6839 |                  0.7049 |                0.1388 |                0.0302 |
| daytype_raw_share_strict | day-type  |   4 | 2493 |       0.0380 |          0.4129 |          0.4902 |             0.3490 |               0.0820 |             0.5305 |               0.2580 |                  0.3632 |                0.3128 |                0.2899 |

## Reading notes

- `zero_bin_eta2` is the share of a unit's exactly-zero raw-cell fraction explained by the partition. High values mean the clusters are largely service-continuity tiers rather than shape types. Recomputed here for the canonical labels with the sidecar's own definition.
- `weekend_ratio_eta2` is a VALIDITY indicator that flips meaning between the two sides. Under full-week closure weekend intensity is inside the feature vector, so a high value is partly circular. Under day-type closure it is external to the features, so it measures genuine external agreement.
- `central_outer_tv` is total variation between the Westminster/Camden cluster distribution and the Kingston/Richmond one. Higher = the two geographies are better separated, which is Howard's objection.
- ARI columns are computed on shared units only.