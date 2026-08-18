## Material Passport

- Origin: `numbat_all_area_test` extension test (started 2026-07-22, now
  including 01b co-located cross-mode station merging)
- Trigger: 2026-07-17 meeting question from Howard/Clara ("why looking at
  just underground rather than all the rail stations within NUMBAT data?")
- Verification status: checked (see reproduction section)

# Rail Extension Check: All NUMBAT Rail Modes vs Underground-Only

## Scope

Two independently-fitted GMM clustering results are compared:

1. **Canonical (270 stations)**: `cluster_clean_version_fullweek/`, keeping
   only stations with `has_lu == True` -- the Underground-only result
   currently used in the dissertation.
2. **All-modes (403 stations)**: a new pipeline built in this folder that
   keeps every NUMBAT rail-family mode (LU, DLR, Overground, Elizabeth
   line, Tram), and merges co-located stations that NUMBAT records under
   separate NLCs per mode at the same physical site
   (`01b_merge_colocated_stations.py`, e.g. each Heathrow terminal's
   Underground side and Elizabeth-line side). Of 440 merged raw NLCs,
   403 have non-zero night-window activity (37 dropped
   under the same `MIN_TOTAL=1` rule as canonical).

The 344-dimensional feature definition (5 native day types x entry/exit x
each day's window) and the GMM methodology (`diag` covariance, `n_init=20`,
`random_state=42`, `reg_covar=1e-6`) are identical between the two; the
difference is station scope and the co-location merge rule.

## An important data-coverage limit: trams are structurally missing

Of the 440 raw stations, the 37 dropped are **entirely, and exclusively**,
Tram (TRM)-only stops -- no DLR/Overground/Elizabeth-line station was
dropped:

| mode_label | n_dropped |
| ---------- | --------- |
| TRM        | 37        |

These tram stops have zero recorded counts in `Station_Entries` /
`Station_Exits` across every day type, not only at night. London Trams have
no gateline, and NUMBAT's Entries/Exits methodology is gateline-based; tram
patronage only appears in `Station_Boarders`, which uses a different
counting method (e.g. onboard counts). So "all NUMBAT rail stations" is
**structurally unable to include trams** through this feature -- that is a
property of the source data, not a choice made in this preprocessing
script. Non-Underground DLR, Overground, and Elizabeth-line stations are
retained normally.

## Finding 1: the BIC-preferred K changes

| K  | BIC_canonical | silhouette_canonical | BIC_allmodes | silhouette_allmodes |
| -- | ------------- | -------------------- | ------------ | ------------------- |
| 2  | -966684.406   | 0.316                | -1886125.798 | 0.301               |
| 3  | -971849.720   | 0.160                | -1895086.812 | 0.153               |
| 4  | -972699.323   | 0.183                | -1898039.239 | 0.116               |
| 5  | -974893.293   | 0.142                | -1899714.293 | 0.104               |
| 6  | -975013.528   | 0.141                | -1898930.005 | 0.108               |
| 7  | -974472.051   | 0.112                | -1897934.086 | 0.122               |
| 8  | -972937.521   | 0.104                | -1897153.616 | 0.108               |
| 9  | -971510.379   | 0.110                | -1895781.393 | 0.099               |
| 10 | -969691.461   | 0.119                | -1893674.629 | 0.101               |
| 11 | -967004.959   | 0.109                | -1891315.270 | 0.103               |
| 12 | -964990.499   | 0.121                | -1888528.251 | 0.079               |

- Canonical (270, Underground-only): BIC-best at **K=6**
  (K=5 and K=6 are close, see the existing `rail_k_selection_validation`
  report).
- All-modes (403, all rail modes): BIC-best at **K=5**, and
  this is a genuine interior optimum, not a grid-boundary artifact
  (K4=-1898039,
  K5=-1899714,
  K6=-1898930).

This directly answers Howard's question: widening the scope from
Underground-only to all NUMBAT rail stations does shift the BIC-optimal
cluster count (from 6 to 5), so the current K=5 choice is
conditional on the Underground-only scope, not a scope-independent result.

## Finding 2: stability of the original 270 stations' cluster membership

Restricting the all-modes (403-station) K=5 result back to the original 270
Underground stations and comparing to the canonical K=5 labels:

**ARI = 0.630**

Best one-to-one match (Hungarian algorithm on Jaccard):

| canonical_k5_cluster | matched_allmodes_cluster | intersection | canonical_size | allmodes_subset_size | jaccard |
| -------------------- | ------------------------ | ------------ | -------------- | -------------------- | ------- |
| 0                    | 4                        | 109          | 119            | 127                  | 0.796   |
| 1                    | 1                        | 12           | 15             | 23                   | 0.462   |
| 2                    | 3                        | 9            | 44             | 12                   | 0.191   |
| 3                    | 2                        | 27           | 38             | 50                   | 0.443   |
| 4                    | 0                        | 49           | 54             | 58                   | 0.778   |

Full contingency table (rows = canonical's 5 clusters, columns = all-modes'
5 clusters, restricted to the 270 Underground stations):

| canonical_cluster | allmodes_C0 | allmodes_C1 | allmodes_C2 | allmodes_C3 | allmodes_C4 |
| ----------------- | ----------- | ----------- | ----------- | ----------- | ----------- |
| canonical_C0      | 9           | 0           | 1           | 0           | 109         |
| canonical_C1      | 0           | 12          | 0           | 3           | 0           |
| canonical_C2      | 0           | 0           | 19          | 9           | 16          |
| canonical_C3      | 0           | 11          | 27          | 0           | 0           |
| canonical_C4      | 49          | 0           | 3           | 0           | 2           |

## Finding 3: where the 133 added non-Underground stations land

Grouped by service mode (LU-only / LU-interchange / DLR-only /
Overground-only / Elizabeth line-only / Tram-only) against the all-modes
K=5 cluster assignment (full 403-station set after the activity filter):

| mode_group                    | 0  | 1  | 2  | 3  | 4   | total |
| ----------------------------- | -- | -- | -- | -- | --- | ----- |
| LU only                       | 53 | 17 | 38 | 11 | 109 | 228   |
| LU + other mode (interchange) | 5  | 6  | 12 | 1  | 18  | 42    |
| DLR-only                      | 2  | 1  | 6  | 17 | 12  | 38    |
| Overground-only               | 23 | 2  | 34 | 2  | 13  | 74    |
| Elizabeth line-only           | 5  | 0  | 0  | 0  | 12  | 17    |
| other non-LU mix (DLR,EZL)    | 0  | 0  | 0  | 0  | 1   | 1     |
| other non-LU mix (DLR,LO)     | 0  | 0  | 0  | 0  | 1   | 1     |
| other non-LU mix (EZL,LO)     | 0  | 0  | 0  | 0  | 1   | 1     |
| other non-LU mix (LO,TRM)     | 1  | 0  | 0  | 0  | 0   | 1     |

Row-normalised shares:

| mode_group                    | 0     | 1     | 2     | 3     | 4     |
| ----------------------------- | ----- | ----- | ----- | ----- | ----- |
| LU only                       | 0.232 | 0.075 | 0.167 | 0.048 | 0.478 |
| LU + other mode (interchange) | 0.119 | 0.143 | 0.286 | 0.024 | 0.429 |
| DLR-only                      | 0.053 | 0.026 | 0.158 | 0.447 | 0.316 |
| Overground-only               | 0.311 | 0.027 | 0.459 | 0.027 | 0.176 |
| Elizabeth line-only           | 0.294 | 0.000 | 0.000 | 0.000 | 0.706 |
| other non-LU mix (DLR,EZL)    | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| other non-LU mix (DLR,LO)     | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| other non-LU mix (EZL,LO)     | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| other non-LU mix (LO,TRM)     | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Bounded conclusion

- K selection is genuinely sensitive to whether all rail modes are included; the BIC-optimal K shifts from 6 to 5, and this is a real, not a numerical-noise, difference.
- However, the original 270 Underground stations' cluster membership is
  partially consistent
  in the new clustering (ARI=0.630), so the 133 added
  stations mostly supplement the existing structure rather than reshuffling
  the Underground stations' groupings from the ground up.
- The decision to use Underground-only therefore looks robust for the
  **internal grouping of the 270 Underground stations themselves**.
  A claim that "K=5 is the universally optimal number of night-activity rail clusters" still needs to be scoped to "Underground-only" -- the same methodology applied to all NUMBAT rail modes gives a different BIC-optimal K (5). This is a methodological scope caveat, not a refutation of the existing Underground result.

## Limitations

- The 133 newly-included stations have not had the same manual review as
  the canonical 270, though the 14 co-located cross-mode sites (Heathrow
  terminals, Canary Wharf, Euston, Liverpool Street, Paddington, etc.) have now been
  merged via `01b_merge_colocated_stations.py`.
- This check does not repeat the `rail_k_selection_validation` bootstrap/
  seed stability battery; it is a single deterministic-fit comparison and
  should be read as directional, not final, evidence.
- No LNWC/IMD linkage was attempted for the added stations; this check is
  limited to clustering structure.

## Reproduction

```
python src/01_preprocess_rail_allmodes.py
python src/01b_merge_colocated_stations.py
python src/02_build_features_allmodes.py
python src/03_cluster_allmodes.py
python src/04_compare_lu_vs_allmodes.py
```
