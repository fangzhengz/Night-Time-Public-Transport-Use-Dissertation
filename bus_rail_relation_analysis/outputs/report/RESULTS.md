# Bus x rail spatial relation — results

Answers the question Clara raised on 2026-07-28: how do the bus night-activity
clusters relate to distance from rail stations? Scope is deliberately narrow —
proximity to rail **nodes** only. No interchange claim is made (that needs OD
flows and timetables, which this project does not have), no corridor/along-the-line
structure is tested (that needs rail line geometry), and the night-rail service-gap
question is deferred to the Chapter 6 vulnerability write-up.

Bus: StopArea CLR K=4, 3,383 fitted LSOAs. Rail: all-modes K=5, 403 stations.
Distances measured from each StopArea's own coordinate, then aggregated to LSOA.

## Test A — distance to nearest rail station by bus cluster

| Bus cluster | n | Median dist. to rail (m) | IQR (m) | Median dist. to centre (m) |
|---|---:|---:|---:|---:|
| C1 relatively high activity, stronger night-persistence | 1,134 | 547 | 240–1,122 | 9,649 |
| C2 moderate activity and persistence, transitional | 1,069 | 916 | 492–2,094 | 12,318 |
| C3 moderate activity with destination characteristics | 576 | 1,113 | 586–2,252 | 13,900 |
| C0 low activity, weak night-persistence | 604 | 1,223 | 704–2,573 | 15,794 |

**The gradient is monotone.** C1 relatively high activity, stronger night-persistence sits a median
547 m from the nearest rail station;
C0 low activity, weak night-persistence sits 1,223 m away —
a factor of 2.2. Kruskal-Wallis H=328.3, epsilon-squared = **0.096**.

Robustness across the three StopArea→LSOA aggregations:

| Distance measure | epsilon² | H |
|---|---:|---:|
| activity-weighted mean StopArea distance (primary) | 0.096 | 328.3 |
| minimum StopArea distance | 0.101 | 344.0 |
| unweighted mean StopArea distance | 0.092 | 312.7 |
| CONTROL: activity-weighted distance to Charing Cross *(control)* | 0.118 | 401.5 |

### Why epsilon-squared understates this — read Test A2 instead

Taken alone, Test A looks confounded: bus clusters separate on distance-to-Charing-Cross (epsilon² = 0.118) slightly *more* strongly than on
distance-to-rail (epsilon² = 0.096), and the two correlate at Spearman rho = 0.53.

But epsilon-squared is the wrong instrument here, for two reasons:

1. **Wrong direction.** It asks "given a cluster, how far is it from rail?" The
   claim under test — and what the overlay map actually shows — is the reverse
   conditional: *near a station, what fraction of LSOAs are the high-flow*
   *night-persistent cluster?*
2. **Wrong shape.** The effect is almost entirely a 0–400 m step. A rank test
   spread over a 0–10 km distribution averages that away.

Test A2 below reports the reverse conditional by distance band, and the effect
**does** survive stratification by centrality. Cite Test A2, not Test A's
epsilon-squared, for this finding.

## Test A2 — cluster composition by distance band (the headline result)

Same data, reverse conditional, and binned so the shape is visible.

| band       |   n |   C0 low activity, weak night-persistence |   C1 relatively high activity, stronger night-persistence |   C2 moderate activity and persistence, transitional |   C3 moderate activity with destination characteristics |
|:-----------|----:|------------------------------------------:|----------------------------------------------------------:|-----------------------------------------------------:|--------------------------------------------------------:|
| 0-400m     | 975 |                                       8.9 |                                                      54.3 |                                                 26.2 |                                                    10.7 |
| 400-800m   | 782 |                                      17.3 |                                                      31.3 |                                                 34.1 |                                                    17.3 |
| 800-1200m  | 494 |                                      21.1 |                                                      28.5 |                                                 30   |                                                    20.4 |
| 1200-2000m | 445 |                                      23.4 |                                                      25.4 |                                                 31.2 |                                                    20   |
| >2000m     | 687 |                                      25.3 |                                                      15.4 |                                                 37.8 |                                                    21.4 |

Whole-sample baseline: C0 low activity, weak night-persistence 17.9%, C1 relatively high activity, stronger night-persistence 33.5%, C2 moderate activity and persistence, transitional 31.6%, C3 moderate activity with destination characteristics 17.0%. Chi-square = 337.6, df = 12, p = 5.9e-65 — and this
chi-square **is** valid, unlike Test B's: every LSOA is one independent row, with
no label borrowed from a shared station.

**Within 400 m of a rail station, 54.3% of LSOAs are the**
**C1 relatively high activity, stronger night-persistence cluster — 1.6x the 33.5%**
**whole-sample baseline. Beyond 2 km it is 15.4%,**
**under half the baseline.** The step is sharp: by 400–800 m the
composition is already back near baseline, so this is a walking-distance-scale
effect, not a gradual gradient.

### It survives the centrality control

C1 share by band, computed inside each distance-to-centre tercile against that
ring's own baseline:

| Ring | Ring C1 baseline | 0–400 m | vs baseline | ratio |
|---|---:|---:|---:|---:|
| inner | 48.8% | 61.3% | +12.5pp | 1.26x |
| middle | 33.9% | 53.1% | +19.2pp | 1.57x |
| outer | 17.9% | 31.9% | +14.0pp | 1.78x |

The 0–400 m enrichment holds in **all three** rings, and in relative terms it is
*largest in the outer ring* (1.81x) — precisely where the centre-periphery
explanation is weakest. This is what Test A's epsilon-squared could not show.
Per-ring chi-square p-values are all < 1e-6; full table in
`data/test_a2_c1_share_by_band_and_ring.csv`.

## Test B — bus cluster × nearest rail cluster co-occurrence

Bus LSOAs within 800 m of a rail station (1,757, 51.9% of the fitted sample) borrow the
cluster label of the station that the most bus night activity in them sits nearest to.

- **Cramér's V = 0.158** (1200 m sensitivity: 0.154 — stable)
- Station-level permutation p = **0.0001** (9,999 permutations; null V mean 0.059, 95th pct 0.079)
- The naive chi-square p (2.3e-22) is **invalid** and reported
  only for contrast: 1,757 LSOAs share only 368 distinct station labels, so an ordinary chi-square
  massively overstates the evidence. The permutation test shuffles labels across
  stations, preserving that replication under the null.

Within distance-to-centre terciles the association does **not** collapse:

| Centrality tercile | n | Cramér's V |
|---|---:|---:|
| inner | 586 | 0.120 |
| middle | 585 | 0.106 |
| outer | 586 | 0.172 |

Like Test A2, the co-occurrence survives controlling for centrality, so it is not
simply a shared centre-periphery gradient. The effect size is modest in absolute
terms, but it is roughly 2.5x the permutation null mean. Test A2 answers *where*
the night-persistent bus areas are; Test B answers *what kind* of rail node they
sit next to.

### Row % — each bus cluster's split across rail clusters (800 m)

| bus_cluster_name                                        |   C0 outer arrival-oriented |   C1 central departure-oriented |   C2 central interchange, direction-balanced |   C3 late-night, extended-duration persistent |   C4 inner–middle ring mixed |
|:--------------------------------------------------------|----------------------------:|--------------------------------:|---------------------------------------------:|----------------------------------------------:|-----------------------------:|
| C0 low activity, weak night-persistence                 |                        38.3 |                             2.3 |                                         14   |                                           3.6 |                         41.9 |
| C1 relatively high activity, stronger night-persistence |                        12.9 |                             3.9 |                                         24.3 |                                           8.7 |                         50.3 |
| C2 moderate activity and persistence, transitional      |                        18.4 |                             1.1 |                                         15.3 |                                           6.9 |                         58.2 |
| C3 moderate activity with destination characteristics   |                        35.1 |                             1.3 |                                         13.8 |                                           6.7 |                         43.1 |

The substantive pattern: the high-flow, night-persistent bus cluster is the one that
pairs with **inner** rail clusters — it has both the largest share next to inner/near-
suburban residential stations and, at nearly double any other bus cluster, the largest
share next to the departure-dominant inner London stations. The low-flow peripheral
and moderate-flow directional bus clusters instead pair with the outer suburban,
arrival-dominant rail cluster. Bus night persistence and rail night function line up
in the direction the night-time-economy reading would predict.

## Figures

- `figures/overlay_bus_clusters_rail_stations.png` — the formal version of Clara's
  hand-made overlay.
- `figures/cluster_composition_by_distance_band.png` — Test A2, both panels.
- `figures/distance_to_rail_by_cluster.png` — distributions behind Test A.

## What this does not establish

1. **Not interchange.** Nothing here observes a passenger transferring. Proximity and
   co-occurrence are consistent with a feeder relationship but equally consistent with
   both modes independently serving the same night-active places. The 0–400 m
   concentration is *suggestive* of a walking-interchange mechanism — that is a
   Discussion reading, not a Results claim.
2. **Not corridors.** Distance-to-nearest-station treats stations as isolated points.
   If bus activity follows the line *between* stations, this design only partly picks
   that up; testing it properly needs TfL line geometry.
3. **Test A's epsilon-squared understates the effect** and looks confounded with
   centrality. Test A2 and Test B are the citable results; both survive the control.