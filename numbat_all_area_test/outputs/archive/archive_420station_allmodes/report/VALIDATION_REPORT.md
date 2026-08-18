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
2. **All-modes (420 stations)**: a new pipeline built in this folder that
   keeps every NUMBAT rail-family mode (LU, DLR, Overground, Elizabeth
   line, Tram), and merges co-located stations that NUMBAT records under
   separate NLCs per mode at the same physical site
   (`01b_merge_colocated_stations.py`, e.g. each Heathrow terminal's
   Underground side and Elizabeth-line side). Of 457 merged raw NLCs,
   420 have non-zero night-window activity (37 dropped
   under the same `MIN_TOTAL=1` rule as canonical).

The 344-dimensional feature definition (5 native day types x entry/exit x
each day's window) and the GMM methodology (`diag` covariance, `n_init=20`,
`random_state=42`, `reg_covar=1e-6`) are identical between the two; the
difference is station scope and the co-location merge rule.

## An important data-coverage limit: trams are structurally missing

Of the 457 raw stations, the 37 dropped are **entirely, and exclusively**,
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

## Finding 1: the BIC-preferred K agrees once co-located stations are merged

| K  | BIC_canonical | silhouette_canonical | BIC_allmodes | silhouette_allmodes |
| -- | ------------- | -------------------- | ------------ | ------------------- |
| 2  | -966684.406   | 0.316                | -1480613.702 | 0.316               |
| 3  | -971849.720   | 0.160                | -1490429.361 | 0.149               |
| 4  | -972699.323   | 0.183                | -1496338.960 | 0.130               |
| 5  | -974893.293   | 0.142                | -1499102.374 | 0.116               |
| 6  | -975013.528   | 0.141                | -1501451.394 | 0.087               |
| 7  | -974472.051   | 0.112                | -1499670.261 | 0.113               |
| 8  | -972937.521   | 0.104                | -1501283.843 | 0.092               |
| 9  | -971510.379   | 0.110                | -1499155.465 | 0.095               |
| 10 | -969691.461   | 0.119                | -1498731.701 | 0.060               |
| 11 | -967004.959   | 0.109                | -1496826.636 | 0.067               |
| 12 | -964990.499   | 0.121                | -1495004.701 | 0.083               |

- Canonical (270, Underground-only): BIC-best at **K=6**
  (K=5 and K=6 are close, see the existing `rail_k_selection_validation`
  report).
- All-modes (420, all rail modes): BIC-best at **K=6**, and
  this is a genuine interior optimum, not a grid-boundary artifact
  (K5=-1499102,
  K6=-1501451,
  K7=-1499670).

This also answers Howard's question, but in the opposite direction from an
earlier run of this check (before co-located cross-mode stations were
merged): with all NUMBAT rail modes included **and** the 13 co-located
cross-mode sites (Heathrow terminals, Canary Wharf, Euston, etc.) properly
merged into single stations, the BIC-optimal K does **not** change -- both
scopes agree on K=6. Before merging, the all-modes BIC-optimal K was 7
(see this folder's earlier run history), so that earlier shift was **partly
an artefact of one physical station being split across multiple NLC rows**,
not a genuine structural consequence of widening station scope. Once merged,
the two independent station scopes agree on BIC.

## Finding 2: stability of the original 270 stations' cluster membership

Restricting the all-modes (420-station) K=5 result back to the original 270
Underground stations and comparing to the canonical K=5 labels:

**ARI = 0.570**

Best one-to-one match (Hungarian algorithm on Jaccard):

| canonical_k5_cluster | matched_allmodes_cluster | intersection | canonical_size | allmodes_subset_size | jaccard |
| -------------------- | ------------------------ | ------------ | -------------- | -------------------- | ------- |
| 0                    | 0                        | 118          | 119            | 153                  | 0.766   |
| 1                    | 3                        | 9            | 15             | 9                    | 0.600   |
| 2                    | 1                        | 15           | 44             | 16                   | 0.333   |
| 3                    | 2                        | 38           | 38             | 61                   | 0.623   |
| 4                    | 4                        | 30           | 54             | 31                   | 0.545   |

Full contingency table (rows = canonical's 5 clusters, columns = all-modes'
5 clusters, restricted to the 270 Underground stations):

| canonical_cluster | allmodes_C0 | allmodes_C1 | allmodes_C2 | allmodes_C3 | allmodes_C4 |
| ----------------- | ----------- | ----------- | ----------- | ----------- | ----------- |
| canonical_C0      | 118         | 0           | 0           | 0           | 1           |
| canonical_C1      | 0           | 1           | 5           | 9           | 0           |
| canonical_C2      | 13          | 15          | 16          | 0           | 0           |
| canonical_C3      | 0           | 0           | 38          | 0           | 0           |
| canonical_C4      | 22          | 0           | 2           | 0           | 30          |

## Finding 3: where the 150 added non-Underground stations land

Grouped by service mode (LU-only / LU-interchange / DLR-only /
Overground-only / Elizabeth line-only / Tram-only) against the all-modes
K=5 cluster assignment (full 420-station set after the activity filter):

| mode_group                    | 0   | 1  | 2  | 3 | 4  | total |
| ----------------------------- | --- | -- | -- | - | -- | ----- |
| LU only                       | 133 | 15 | 47 | 6 | 27 | 228   |
| LU + other mode (interchange) | 20  | 1  | 14 | 3 | 4  | 42    |
| DLR-only                      | 10  | 18 | 6  | 2 | 2  | 38    |
| Overground-only               | 27  | 1  | 27 | 1 | 24 | 80    |
| Elizabeth line-only           | 14  | 0  | 1  | 3 | 10 | 28    |
| other non-LU mix (DLR,EZL)    | 1   | 0  | 0  | 0 | 0  | 1     |
| other non-LU mix (DLR,LO)     | 0   | 1  | 0  | 0 | 0  | 1     |
| other non-LU mix (EZL,LO)     | 1   | 0  | 0  | 0 | 0  | 1     |
| other non-LU mix (LO,TRM)     | 0   | 0  | 0  | 0 | 1  | 1     |

Row-normalised shares:

| mode_group                    | 0     | 1     | 2     | 3     | 4     |
| ----------------------------- | ----- | ----- | ----- | ----- | ----- |
| LU only                       | 0.583 | 0.066 | 0.206 | 0.026 | 0.118 |
| LU + other mode (interchange) | 0.476 | 0.024 | 0.333 | 0.071 | 0.095 |
| DLR-only                      | 0.263 | 0.474 | 0.158 | 0.053 | 0.053 |
| Overground-only               | 0.338 | 0.013 | 0.338 | 0.013 | 0.300 |
| Elizabeth line-only           | 0.500 | 0.000 | 0.036 | 0.107 | 0.357 |
| other non-LU mix (DLR,EZL)    | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| other non-LU mix (DLR,LO)     | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| other non-LU mix (EZL,LO)     | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| other non-LU mix (LO,TRM)     | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |

## Bounded conclusion

- Once co-located cross-mode stations are properly merged, the BIC-optimal K **agrees** across both station scopes (K=6 either way) -- K selection is not as scope-sensitive as an earlier, unmerged version of this check suggested; that earlier shift traced mainly to station-accounting granularity, not station scope itself.
- However, the original 270 Underground stations' cluster membership is
  partially consistent
  in the new clustering (ARI=0.570), so the 150 added
  stations mostly supplement the existing structure rather than reshuffling
  the Underground stations' groupings from the ground up.
- The decision to use Underground-only therefore looks robust for the
  **internal grouping of the 270 Underground stations themselves**, and, once co-located stations are merged, for K selection itself too.
  The BIC-optimal K itself (K=6) is no longer a point of difference between scopes, though the finer-grained cluster membership (Finding 2) still shows only partial, not full, agreement.

## Limitations

- The 150 newly-included stations have not had the same manual review as
  the canonical 270, though the 13 co-located cross-mode sites (Heathrow
  terminals, Canary Wharf, Euston, Liverpool Street, etc.) have now been
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
