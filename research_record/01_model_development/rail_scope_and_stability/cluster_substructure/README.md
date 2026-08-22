# Current post-Paddington cluster-substructure screen (Rail all-modes K=5)

The five Rail clusters are deliberately broad, and some contain recognisable internal contrasts. This screen asks whether those contrasts recur strongly enough to describe as nested structure while leaving the adopted K=5 partition untouched. It is a diagnostic of heterogeneity within clusters, not permission to promote every stable split into a new headline typology.

**Status: rerun 2026-08-07 on the corrected 403-station Rail result.** This
folder remains exploratory and descriptive: the primary five-cluster labels
are not modified, and no nested label is fed back into RQ2.

- The previous broad central-departure parent is now top-level **C1** (n=26).
  Its anchored West End/night-origin subcore contains 12 stations, with the
  three defining anchors co-clustering in 10/10 seed fits.
- Current C4 (n=167) has a reproducible sub-K=2 split (seed ARI=0.927):
  outer n=108 and inner-hub n=59. Sub-K=3 is not reproducible (ARI=0.551).
- Current outputs are `c1_*`, `c1ab_*`, `c4_*`, `nested_c2_map.*` (the
  filename is retained for compatibility but depicts the current C1 split),
  and `nested_c4_map.*`. The old `c2_*` files dated 2026-08-02 are historical.

## Historical pre-correction documentation

Second-stage addendum to the adopted rail K=5 typology in
`numbat_all_area_test/`. Read-only with respect to that folder: the primary
`cluster` column (`rail_allmodes_k5_labels.csv`) is never modified, this
folder only adds a nested `cluster_nested` label.

## What this is

Within adopted C2 (central departure-dominant, night origin, n=82), there is
a highly reproducible 16-station "West End night-origin core" — Temple,
Knightsbridge, Bond Street, Green Park, Hyde Park Corner, Holborn,
Westminster, Oxford Circus, Leicester Square, Tottenham Court Road,
Piccadilly Circus, Embankment, South Kensington, Charing Cross LU,
Shoreditch High Street, Angel.

It is not recoverable at the full-network level: single-stage GMM finds it
in only 1/8 seeds at K=6 and 2/10 at K=7, because at 16/404 = 3.2% of the
network it barely dents the total log-likelihood and gets absorbed into a
neighbouring cluster almost for free. Conditioning on the parent cluster
removes that competition — at 16/82 = 19.5% of C2 alone, the identical
algorithm at identical settings recovers it at **10/10 seeds, pairwise
ARI = 1.000, 0 stations in the ambiguous partial-support band**. Standard
nested-classification rationale (OAC Supergroup → Group → Subgroup), applied
to a station typology.

## Profile vs. the C2 remainder (n=66)

| | direction_balance | weekend_common_ratio | night_tube_extension_share | total_activity |
|---|---|---|---|---|
| **C2b core (n=16)** | 0.402 | 0.919 | 0.035 | 107,530 |
| C2a remainder (n=66) | 0.108 | 0.799 | 0.013 | 51,746 |
| all 404 stations | −0.249 | 0.794 | 0.028 | 29,603 |

Temporal-shape detail (`02_c2ab_temporal_profile.py`): the two groups' entry
curves look similar through the evening peak; the split is in the tail.
C2a flips from entry/departure-dominant to exit/arrival-dominant by ~21:00–
22:45 on most day types. C2b holds departure-dominance almost to the last
service — 01:00 (Mon/TWT), 04:30 (Fri), never within the window (Sat), 00:15
(Sun). And the gap is concentrated entirely on Fri/Sat: post-01:00 entry
share is ~4x higher in the core than the remainder on those two nights;
on Mon/TWT/Sun (no Night Tube) both groups are near zero, so the "stays busy
past 1am" character is a weekend-nightlife signature, not a general one.

## C4 (n=166): a second, weaker reproducible split

Same protocol (`03_c4_substructure.py`), run generically at sub-K=2 and
sub-K=3 rather than anchor-based, since there is no known landmark group to
target the way West End was for C2. Re-checked against the *current* padded
matrix and current C4 id rather than assumed from the pre-relabel screen
(`08_substructure_screen.py`, archived, which found old-C3 sub-K=2 at seed
ARI = 1.000 exactly — that was on the 344-dim unpadded matrix, old id C3,
n=163).

**sub-K=2 is reproducible: seed ARI mean = 0.905** (>= 0.90 threshold, but
noticeably less clean than C2's 1.000 — this split has more seed-to-seed
wobble, so treat it as real but softer evidence than the C2 core).
**sub-K=3 is not** (0.781).

| sub-cluster | n | dir_balance | weekend_common_ratio | median_activity | km_to_centre | %LU | top stations |
|---|---|---|---|---|---|---|---|
| C4 sub0 (outer) | 101 | −0.426 | 0.789 | 17,141 | 11.1 | 79.2% | Barking, Ealing Broadway, Woolwich EL, Romford, Tooting Broadway, Seven Sisters |
| C4 sub1 (inner hub) | 65 | −0.201 | 0.873 | 19,465 | 6.1 | 67.7% | Waterloo LU, Stratford, Paddington TfL, Clapham Junction, Finsbury Park LU, Vauxhall LU |

Reads as an outer-suburban / inner-interchange-hub split within C4: sub1 is
closer to centre, more multi-modal (lower %LU — more National Rail/
Elizabeth line mix), less arrival-skewed, and more weekend-leaning than
sub0. No temporal-curve comparison built yet for this pair (unlike C2a/
C2b) — worth doing if this gets promoted, since the scalar gap here is
narrower than C2's and the curves might clarify whether it's a real second
mode or a shading of the same one.

## Status

**Not yet decided how deep either split goes into the write-up** (as of
2026-08-02):
RQ1 descriptive/appendix note only, vs. also splitting C2 into C2a/C2b for
RQ2's LNWC/IMD association re-run. The latter reopens frozen RQ2 downstream
outputs and — per the caveat below — the core is thin for anything beyond
descriptive effect sizes.

**Supersedes** an earlier attempt in `FYP/旧分析归档/rq1_rail_method_tests/
outputs/c4_substructure/`, which ran before the same-day padded-window
adoption and cluster renumbering (old cluster id 4, old 344-dim unpadded
matrix) and got a stale core of n=13. That folder now carries a pointer back
here.

**Caveat to carry**: 16 stations is ample for description and narrative, but
thin for catchment-based association tests. Report effect sizes
descriptively; do not lean on significance.

**Nested id scheme is shared across both split files, do not reuse ids**:
0-4 = adopted K=5 clusters (untouched), 5 = C2 night-origin core, 6 =
reserved, 7/8 = C4 sub0 (outer) / sub1 (inner hub). Keep this registry
updated if a third parent gets screened.

## Run order

```bash
python src/01_c2_substructure.py         # C2 nested labels, roster, split metrics, map
python src/02_c2ab_temporal_profile.py   # C2a/C2b entry/exit curve comparison, crossover timing
python src/03_c4_substructure.py         # C4 reproducibility screen (sub-K=2,3), labels, roster, map
```

## Output files

```
rail_allmodes_k5_nested_labels.csv   C2: per-station cluster + cluster_nested (5=core)
c2_split_metrics.csv                  C2a / C2b / all-404 scalar comparison
c2b_core_roster.csv                   16-station roster with seed support
nested_c2_map.png / .pdf              C2 spatial plot, core starred
summary.json                          C2 split parameters + reproducibility record
c2ab_temporal_profile.png / .pdf      entry/exit curves, C2a vs C2b, all 5 day types
c2ab_exit_over_entry_crossover.csv    per-day-type departure->arrival flip time
c2ab_post0100_by_daytype.csv          post-01:00 share, by day type and direction

c4_screen_table.csv                   C4: sub-K=2 and sub-K=3 stability + eta2 table
c4_subcluster_rosters.csv             C4 sub-cluster characterisation (both sub-Ks tested)
c4_nested_labels.csv                  C4: per-station cluster + cluster_nested (7/8=sub0/sub1)
c4_summary.json                       C4 split parameters + reproducibility record
nested_c4_map.png / .pdf              C4 spatial plot
```
