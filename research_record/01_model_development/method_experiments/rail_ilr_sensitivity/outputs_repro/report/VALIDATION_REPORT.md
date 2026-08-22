## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run + validate
- Origin Date: 2026-07-21T16:03:45.770017+00:00
- Verification Status: ANALYZED
- Version Label: rail_ilr_sensitivity_v1

# Rail ILR compositional sensitivity

## Verdict

**The current Rail K=5 typology is materially sensitive to the ILR compositional treatment and should not yet be frozen for downstream interpretation.**

This is a bounded sensitivity judgment, not evidence that K=5 is a true natural
number of station types.

## Coordinate audit

The same 270 stations and 344 raw-share columns were used. Entry and exit were
handled as separate 172-part compositions with empirical-prior alpha=1, yielding
342 Helmert ILR coordinates. The centered sample rank is
`269`. The maximum sampled CLR-versus-ILR distance
error is `2.842e-14`.

## Direct raw versus ILR label agreement

| raw_K | ilr_K | ARI   | NMI   | best_match_share | weakest_matched_cluster_jaccard |
| ----- | ----- | ----- | ----- | ---------------- | ------------------------------- |
| 5     | 5     | 0.216 | 0.351 | 0.511            | 0.207                           |
| 6     | 6     | 0.221 | 0.360 | 0.415            | 0.000                           |

### Raw K=5 to ILR K=5 matching

| raw_cluster | ilr_cluster | intersection | reference_size | candidate_size | jaccard | recall | precision |
| ----------- | ----------- | ------------ | -------------- | -------------- | ------- | ------ | --------- |
| 0           | 4           | 46           | 119            | 53             | 0.365   | 0.387  | 0.868     |
| 1           | 2           | 12           | 15             | 39             | 0.286   | 0.800  | 0.308     |
| 2           | 0           | 20           | 44             | 52             | 0.263   | 0.455  | 0.385     |
| 3           | 3           | 17           | 38             | 61             | 0.207   | 0.447  | 0.279     |
| 4           | 1           | 43           | 54             | 65             | 0.566   | 0.796  | 0.662     |

## Internal ILR diagnostics: fixed diagonal family

| K | BIC       | delta_BIC_within_diag | silhouette | davies_bouldin | min_cluster_n | bootstrap_ARI_mean | bootstrap_ARI_q025 | bootstrap_ARI_q975 | bootstrap_weakest_cluster_jaccard | seed_ARI_mean |
| - | --------- | --------------------- | ---------- | -------------- | ------------- | ------------------ | ------------------ | ------------------ | --------------------------------- | ------------- |
| 3 | 76238.151 | 18734.701             | 0.322      | 2.165          | 52            | 0.723              | 0.489              | 0.992              | 0.443                             | 1.000         |
| 4 | 67853.199 | 10349.749             | 0.126      | 2.619          | 52            | 0.753              | 0.525              | 0.953              | 0.722                             | 1.000         |
| 5 | 63478.030 | 5974.580              | 0.082      | 2.862          | 39            | 0.559              | 0.371              | 0.747              | 0.091                             | 0.544         |
| 6 | 58633.800 | 1130.350              | 0.091      | 2.548          | 30            | 0.607              | 0.441              | 0.766              | 0.175                             | 0.808         |
| 7 | 59373.453 | 1870.003              | 0.060      | 2.685          | 25            | 0.563              | 0.433              | 0.705              | 0.310                             | 0.722         |
| 8 | 58580.577 | 1077.127              | 0.063      | 2.463          | 2             | 0.526              | 0.432              | 0.682              | 0.122                             | 0.718         |

Within the ILR diagonal family, BIC is lowest at K=9. Within K=3-8,
silhouette is highest at K=3, and bootstrap mean ARI is highest
at K=4. These metrics answer different questions and are not
collapsed into a claim of one true K.

## ILR K=5 cluster recurrence

| reference_cluster | jaccard_mean | jaccard_q025 | jaccard_q975 | share_jaccard_below_0_50 |
| ----------------- | ------------ | ------------ | ------------ | ------------------------ |
| 0                 | 0.091        | 0.000        | 0.619        | 0.935                    |
| 1                 | 0.665        | 0.405        | 0.929        | 0.240                    |
| 2                 | 0.652        | 0.025        | 0.857        | 0.045                    |
| 3                 | 0.624        | 0.410        | 0.938        | 0.265                    |
| 4                 | 0.558        | 0.000        | 0.761        | 0.185                    |

The ILR K=5 mean global bootstrap ARI is
`0.559` with empirical 95% interval
`[0.371, 0.747]`.

## Secondary covariance-family BIC grid

| covariance | best_K | best_BIC   | min_cluster_n | parameters_per_station | full_covariance_underidentified |
| ---------- | ------ | ---------- | ------------- | ---------------------- | ------------------------------- |
| spherical  | 12     | 176877.613 | 3             | 15.285                 | False                           |
| diag       | 9      | 57503.450  | 1             | 22.830                 | False                           |
| tied       | 12     | -79084.573 | 3             | 232.474                | False                           |
| full       | 2      | -23440.146 | 126           | 437.004                | True                            |

The diagonal family remains primary because it holds the accepted Rail GMM
assumption fixed. Full-covariance fits are structurally under-identified here
when component size does not exceed the 342 fitted dimensions, even though
regularization can return a numerical fit.

## Interpretation boundaries

1. Absolute BIC values are not compared against the 344-column raw-share fit.
2. ILR changes geometry and zero handling but adds no new passenger information.
3. LNWC, IMD, geography, station volume, and service variables were excluded.
4. Stability and label agreement do not establish functional or causal meaning.

## Fallacy scan

- Coverage: 11/11 checked.
- Garden of forking paths and look-elsewhere risk are reduced by the prespecified
  K range, fixed primary covariance, explicit thresholds, and complete K=3-8
  stability reporting.
- Ecological fallacy is not used because no area or individual inference is made.
- No causal or reverse-causal claim is made.
- Simpson's paradox, Berkson's paradox, collider bias, base-rate neglect,
  regression to the mean, and survivorship bias were not triggered by this
  clustering sensitivity design.

## Reproducibility status

The run is seed-controlled and records input hashes, package versions, and all
parameters in `RUN_METADATA.json`. A separate deterministic re-run comparison is
required before changing the Material Passport status from ANALYZED to VERIFIED.
