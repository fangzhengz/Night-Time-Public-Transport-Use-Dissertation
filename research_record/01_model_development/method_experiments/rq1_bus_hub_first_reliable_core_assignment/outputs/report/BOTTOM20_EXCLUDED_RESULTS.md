## Material Passport

- Origin: Claude Code
- Verification Status: ANALYZED
- Version Label: bottom20_excluded_bic_v1

# Bottom-20%-excluded, alpha=0, unforced GMM/BIC ("old method") result

## Design

Bottom 20% of the fixed hub-first
3,593-LSOA sample excluded by full-week `total_activity` (cutoff =
243.44); n_total=3593, n_core=2874
(80.0% retained). Features are alpha=0 (no empirical-Bayes
shrinkage) direction-normalised 72-vectors -- exclusion, not shrinkage, is
the only noise-control mechanism tested here. GMM settings match
`rq1_bus_hub_first_reclustering/src/config.py` exactly: 4 covariance
families, K=2..12, n_init=20, reg_covar=1e-6, max_iter=300, seed=42. K is
not forced to any value.

## Global BIC result

Global BIC minimum: **covariance=tied, K=12**.

| covariance   |   K |          BIC |   min_cluster_n |   min_cluster_share |
|:-------------|----:|-------------:|----------------:|--------------------:|
| diag         |  12 | -1.58588e+06 |              77 |         0.0267919   |
| full         |   2 | -1.67786e+06 |            1322 |         0.459986    |
| spherical    |  12 | -1.38653e+06 |             105 |         0.0365344   |
| tied         |  12 | -1.68038e+06 |               1 |         0.000347947 |

## K diagnostics at covariance=tied

|   K |          BIC |   silhouette |   activity_eta2 |   timing_mean_eta2 | gate_activity_below_timing   |   min_cluster_share |   bootstrap_ari_mean |   bootstrap_min_cluster_jaccard_mean |
|----:|-------------:|-------------:|----------------:|-------------------:|:-----------------------------|--------------------:|---------------------:|-------------------------------------:|
|   2 | -1.6745e+06  |    0.226086  |       0.0581862 |          0.0122391 | False                        |         0.0842032   |             0.767429 |                            0.708287  |
|   3 | -1.67401e+06 |    0.0987947 |       0.166215  |          0.163507  | False                        |         0.0883786   |             0.33026  |                            0.353054  |
|   4 | -1.67652e+06 |    0.0739624 |       0.0758129 |          0.211811  | True                         |         0.0142658   |             0.486183 |                            0.108104  |
|   5 | -1.67642e+06 |    0.0677956 |       0.106188  |          0.244654  | True                         |         0.0142658   |             0.487723 |                            0.132245  |
|   6 | -1.67749e+06 |    0.0724303 |       0.107846  |          0.245498  | True                         |         0.0142658   |             0.542721 |                            0.186726  |
|   7 | -1.67776e+06 |    0.0682773 |       0.102649  |          0.318115  | True                         |         0.0205289   |             0.48493  |                            0.0469155 |
|   8 | -1.67849e+06 |    0.0701779 |       0.162215  |          0.26367   | True                         |         0.000347947 |             0.568352 |                            0.012759  |
|   9 | -1.67925e+06 |    0.0733137 |       0.154032  |          0.283503  | True                         |         0.000347947 |           nan        |                          nan         |
|  10 | -1.67898e+06 |    0.051429  |       0.144436  |          0.300717  | True                         |         0.00347947  |           nan        |                          nan         |
|  11 | -1.67935e+06 |    0.0444163 |       0.15058   |          0.345074  | True                         |         0.000347947 |           nan        |                          nan         |
|  12 | -1.68038e+06 |    0.0754432 |       0.1303    |          0.28595   | True                         |         0.000347947 |           nan        |                          nan         |

## Adjacent-K structure

|   K_parent |   K_child |   ARI_adjacent |   weighted_child_to_parent_purity |   smallest_child_share |
|-----------:|----------:|---------------:|----------------------------------:|-----------------------:|
|          2 |         3 |       0.233216 |                          0.995129 |            0.0883786   |
|          3 |         4 |       0.170956 |                          0.555672 |            0.0142658   |
|          4 |         5 |       0.777282 |                          0.98817  |            0.0142658   |
|          5 |         6 |       0.824958 |                          0.974252 |            0.0142658   |
|          6 |         7 |       0.80133  |                          0.955811 |            0.0205289   |
|          7 |         8 |       0.567059 |                          0.869868 |            0.000347947 |
|          8 |         9 |       0.827952 |                          0.951287 |            0.000347947 |
|          9 |        10 |       0.751135 |                          0.940153 |            0.00347947  |
|         10 |        11 |       0.822392 |                          0.933194 |            0.000347947 |
|         11 |        12 |       0.646932 |                          0.864301 |            0.000347947 |

## Comparison to no-exclusion baselines (same hub-first sample, K=3)

| version                                    |   activity_eta2 |   timing_mean_eta2 |
|:-------------------------------------------|----------------:|-------------------:|
| old_nonhubfirst_alpha5_k3 (n=4100)         |          0.518  |           nan      |
| hub_first_alpha5_k3 (n=3593, no exclusion) |          0.518  |             0.2989 |
| hub_first_alpha0_k3 (n=3593, no exclusion) |          0.5222 |             0.284  |

## Reading

The BIC-best K here is **12** under covariance=tied.
At that K, activity_eta2=0.1303 versus
timing_mean_eta2=0.2860
(resolved).
This uses the project's original, unmodified GMM/BIC method (all four
covariance families, full K range, no forced K, no weaker-direction filter,
no shrinkage) on the bottom-20%-excluded sample, so it is a direct test of
whether simple activity-based exclusion alone -- without any of the more
elaborate mechanisms tried earlier (shrinkage grids, weaker-direction
thresholds, BIC-per-threshold search) -- lets the standard method find a
clean structure on its own.

## Warnings and limitations

- BIC values here are only comparable within this sample; they cannot be
  ranked against the no-exclusion baselines' BIC (different n, different
  feature realisation).
- Bootstrap uses K=2..8 only (`PROFILE_K` in the historical config); K=9..12
  are reported for BIC/silhouette only.
- This is a single exclusion quantile (20%). It is not yet a swept threshold
  search like `01_threshold_screen.py`; if this result looks promising, the
  next step is a small quantile sweep (e.g. 10/15/20/25/30%) with the same
  unforced BIC procedure, not a one-shot adoption.

---

Started 2026-07-20T17:00:27.885865+00:00; elapsed 418.3s.
