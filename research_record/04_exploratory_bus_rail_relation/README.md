# bus_rail_relation_analysis

The starting point for this analysis was visual rather than statistical. When the Underground network was overlaid on the Bus cluster map, the more persistent night-bus areas appeared to gather around Rail nodes. That observation led to a focused question: does the spatial pattern remain when proximity is measured explicitly, and does it survive the strong centre–periphery structure of London?

The analysis follows that question from map to measurement. It first describes distance to the nearest Rail station, then reverses the comparison to ask what kinds of Bus areas occur within walking distance, and finally examines which mode-specific cluster types co-occur. It remains an exploratory spatial relationship, not evidence of passenger interchange or a causal network effect.

**Origin.** Clara, 2026-07-28 supervision: she overlaid the Underground network
on the bus cluster map by hand, saw bus clusters appearing to sit along tube
lines, and asked for "some sort of analysis of how do the bus clusters link to
… distance to underground stations or something like that". This folder answers
that and nothing more.

## Scope (agreed 2026-07-30)

**In:** proximity of bus night-activity clusters to rail **nodes**, and whether
bus cluster types co-occur with rail cluster types.

**Out, deliberately:**

| Not tested | Why |
|---|---|
| Interchange / "last-mile" feeding | Needs OD flows + timetables. Neither exists in this project. Any interchange reading belongs in Discussion as interpretation, never in Results as a claim. |
| Corridor / along-the-line structure | Needs TfL line geometry. The user's claim is about nodes, not corridors. Distance-to-nearest-*station* cannot stand in for distance-to-nearest-*line*. |
| Night-rail service gaps ("test C") | Deferred to the Chapter 6 vulnerability write-up. It asks a different question (service provision, not spatial alignment) and mixing it in blurs the aim. |

## Inputs (all read-only, nothing here modifies its sources)

- Bus: `rq1_bus_stoparea_clustering/outputs/clr/labels/k4_labels.csv` — StopArea
  allocation, CLR transform, K=4, adopted 2026-07-29. 3,372 fitted LSOAs.
- Rail: `numbat_all_area_test`'s all-modes K=5, **403 stations after the
  2026-08-07 Paddington NR/TfL merge correction**;
  coordinates from `data_processing/rail_allmodes/`, per-station night metrics
  reused from `rq2_new_clusters_analysis` rather than recomputed.
- StopArea geometry + night counts: `data_processing/bus_stoparea/outputs/preprocessed/`.
- LSOA boundaries: `map/London_LSOA_2021_Boundaries.geojson`.

## Run order

```bash
python src/01_build_link_table.py
python src/02_run_tests.py
python src/03_distance_band_profile.py
python src/04_build_report.py
```

## Design decisions worth knowing

**Distances are measured from StopArea points, not LSOA centroids.** Outer-London
LSOAs are large enough that their centroid is a poor stand-in for where the bus
stops are. Distances are computed per StopArea, then aggregated to LSOA under
three rules — minimum, unweighted mean, and activity-weighted mean. The
activity-weighted mean is the headline (the claim is about where the bus
*activity* sits, not the stop points); the other two are reported alongside so
the result cannot be an artefact of that choice. Current values are in
`outputs/report/RESULTS.md`; activity-weighted epsilon² is 0.097.

**Radius: 800 m primary, 1,200 m sensitivity** (user decision 2026-07-30). Both
are pre-existing project conventions. The radius only caps Test B — beyond it a
bus LSOA has no plausible rail node and must not borrow a distant station's
label. Test A's distances are uncapped.

**Two confounds are handled, not hidden:**

1. *Centre-periphery gradient.* Both clusterings track centrality, so some
   association is nearly guaranteed. Distance to Charing Cross is carried
   through every output. This matters — see the finding below.
2. *Pseudo-replication.* 3,372 bus LSOAs share only 403 rail labels, so an
   ordinary chi-square on n=3,372 is meaningless (effective n is nearer 403).
   Cramér's V is descriptive; significance comes from a permutation test that
   shuffles labels **across stations**, preserving replication under the null.

## Headline results

**Test A2 — the headline. Within 400 m of a rail station, 54.3% of LSOAs are
the high-flow night-persistent cluster, against a 33.5% whole-sample baseline;
beyond 2 km it is 15.4%.** The step is sharp — by 400–800 m composition is
already back near baseline — so this is a walking-distance-scale effect, not a
gradual gradient. It survives the centrality control in **all three** rings
(inner 62.0% vs 49.1% baseline, middle 53.2% vs 34.3%, outer 32.5% vs 18.1%),
and in relative terms is *largest in the outer ring*, precisely where
the centre-periphery explanation is weakest.

**Test A — the same finding, measured badly.** Kruskal-Wallis on distance gives
epsilon² = 0.097, versus 0.115 for the distance-to-centre control, which makes
the effect look confounded. It is not — epsilon-squared is simply the wrong
instrument: it asks the reverse of the question (given a cluster, how far from
rail?) and it averages a sharp 0–400 m step across a 0–10 km distribution.
Kept in the folder as the diagnostic that motivated Test A2, **not** as a
citable result. This was caught by the user looking at the overlay map and
saying the visual looked stronger than the statistic — it did, and it was.

**Test B — what kind of rail node.** Cramér's V = 0.159 at 800 m (0.155 at
1,200 m — stable), station-level permutation p = 0.0001 against a null whose
mean V is 0.059. V does not collapse inside distance-to-centre terciles
(0.121 / 0.101 / 0.186). Test A2 answers *where* the night-persistent bus areas
are; Test B answers *what kind* of rail node they sit next to.

Substantively: the high-flow, night-persistent bus cluster is the one that pairs
with **inner** rail clusters — highest share next to inner/near-suburban
residential stations, and at nearly double any other bus cluster the highest
share next to the departure-dominant inner London stations. The low-flow
peripheral and moderate-flow directional bus clusters pair instead with the
outer suburban, arrival-dominant rail cluster. Bus night persistence and rail
night function line up in the direction a night-time-economy reading predicts.

Full numbers and caveats: `outputs/report/RESULTS.md`.

## Outputs

```
outputs/data/     bus_rail_link_table.csv        one row per fitted bus LSOA
                  stoparea_nearest_rail.csv      one row per StopArea (10,879)
                  test_a_*.csv, test_a2_*.csv, test_b_*.csv, test_results.json
outputs/figures/  overlay_bus_clusters_rail_stations.png   Clara's overlay, formalised
                  cluster_composition_by_distance_band.png Test A2, both panels
                  distance_to_rail_by_cluster.png          Test A distributions
outputs/report/   RESULTS.md
```
