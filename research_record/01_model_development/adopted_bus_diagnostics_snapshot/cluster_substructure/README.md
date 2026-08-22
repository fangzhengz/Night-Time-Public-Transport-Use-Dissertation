# Cluster substructure — exploratory nested split of C1 (bus StopArea CLR K=4)

The adopted four-cluster Bus solution provided a useful city-wide typology, but its largest night-persistent cluster still contained considerable internal variation. This addendum asks whether that variation forms a reproducible nested pattern without reopening or altering the top-level model. It is therefore a closer look inside C1, not a proposal to replace K=4.

This is a second-stage exploratory addendum to the adopted bus StopArea CLR K=4
typology in `rq1_bus_stoparea_clustering/`. Read-only with respect to that
folder: `outputs/clr/labels/k4_labels.csv` (the adopted `cluster` column) is
never modified; this folder only adds a nested `cluster_nested` label.
Mirrors the same protocol used for rail
(`numbat_all_area_test/cluster_substructure/`).

## What this is

Adopted C1 ("high-flow, night-persistent", n=1,145) is the paper's headline
cluster — the one carrying the LNWC/IMD association story. This screens it
for reproducible internal structure the same way rail's C4 was screened:
fit each candidate sub-K at 10 seeds (n_init=100 each, `full` covariance —
the family the adopted CLR K=4 fit itself won on BIC), score stability as
mean pairwise ARI across seed partitions, report the consensus-medoid
partition if stability clears 0.90.

**Both tested sub-Ks are reproducible — sub-K=3 unusually cleanly so:**

| sub-K | seed ARI mean | reproducible |
|---|---|---|
| 2 | 0.917 | yes |
| 3 | **1.000** | yes (perfect agreement across all 10 seeds) |

## sub-K=3 (the emitted nested label)

| sub-cluster | n | direction_balance | post_midnight_share | post_midnight_persistence | weekend_ratio | median_activity | km_to_centre |
|---|---|---|---|---|---|---|---|
| **sub0** | 498 | −0.030 | **0.152** | **0.278** | **0.855** | 5,047 | 8.5 |
| sub1 | 390 | **−0.175** | 0.138 | 0.237 | 0.804 | 1,690 | 11.6 |
| sub2 | 257 | **+0.007** | **0.096** | **0.155** | 0.795 | 2,497 | 10.5 |

Reads as three distinguishable profiles, not just a volume ladder:

- **sub0** is the core of what makes C1 "night-persistent" in the first
  place — highest post-midnight share, highest persistence, highest
  weekend ratio, closest to centre, highest activity. Top LSOAs: City of
  London 001F, Lambeth 011B, Hillingdon 031A, Westminster 018C/023E.
- **sub1** is the most directionally skewed of the three (−0.175, notably
  more one-directional than sub0 or sub2) and the furthest out (11.6km),
  but still meaningfully post-midnight active — reads as an outer-suburban
  arm of the same night-persistent character, not just "the low-volume
  half". Top LSOAs: Ealing 043B, Greenwich 007B, Newham 021C, Lambeth 028D.
- **sub2** is the odd one out: **direction_balance ≈ 0 (balanced flow)**
  combined with the **lowest** post-midnight share and persistence of the
  three — i.e. the *least* night-persistent-acting part of a cluster named
  for night persistence. Mid-range activity and distance. Top LSOAs: Barnet
  039D, Newham 010C, Greenwich 028C, Southwark 006F.

Map: `nested_c1_map.png/.pdf` — sub0 (blue) concentrates in inner/central
London, sub1 (brown) and sub2 (cyan) are more scattered toward outer
boroughs, but the pattern is a fuzzy gradient with substantial LSOA-level
interleaving, not a clean spatial partition (expected — bus demand is far
more locally granular than rail station catchments).

## Caveat: this may be partly re-discovering the activity axis

`eta2_log_total_activity` is the single largest driver at both sub-K=2
(0.383) and sub-K=3 (0.333) — larger than any of the timing/direction
metrics. This project has hit this failure mode before in bus clustering
(see project memory: the pre-StopArea K=3 result was found to be ~49%
volume-noise-driven and had to be re-derived via reliable-core
reclustering). That said, sub-K=3 is not *purely* a volume ladder:
direction_balance (η²=0.173) and post_midnight metrics (η²=0.21–0.23) carry
real, non-redundant signal — sub2's near-zero direction_balance despite
mid-range activity is not explainable by volume alone. Treat sub-K=3 as
a real but volume-entangled structure; if this gets promoted, the volume
confound needs to be addressed explicitly (e.g. partial correlation or an
activity-stratified re-check, the same fix already validated for the
top-level bus clustering) rather than reported as a clean shape-only split.

## Status

**Exploratory only, as of 2026-08-02** — no decision yet on write-up
placement or whether to run downstream LNWC/IMD association checks on
sub0/sub1/sub2. Given C1 is the paper's headline cluster, any promotion
here has more riding on it than the rail splits did; the volume-confound
caveat above should be resolved first.

## Run order

```bash
python src/01_c1_substructure.py   # reproducibility screen, labels, roster, map
```

## Output files

```
c1_screen_table.csv          sub-K=2,3 stability + eta2 characterisation
c1_subcluster_rosters.csv    per-sub-cluster profile + top LSOAs, both sub-Ks
c1_nested_labels.csv         every retained LSOA's cluster + cluster_nested
                              (0/2/3 = other adopted clusters, -1 = excluded,
                              10/11/12 = C1 sub0/sub1/sub2)
c1_summary.json              chosen sub-K, stability, nested-size record
nested_c1_map.png / .pdf     LSOA choropleth of the sub-K=3 split
```
