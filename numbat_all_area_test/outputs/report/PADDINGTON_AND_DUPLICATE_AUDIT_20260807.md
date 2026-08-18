# Paddington correction and duplicate-unit audit

## Status

- Date: 2026-08-07
- Verification status: checked against current preprocessing, clustering and downstream outputs
- Current adopted Rail result: all-modes diagonal-GMM, K=5, 403 stations
- Current adopted Bus result: StopArea-to-LSOA CLR, K=4, 3,372 fitted LSOAs

## Rail correction

Paddington NR (NLC 3087) and Paddington TfL (NLC 670) are now treated as one
physical station. Both source rows map to merged NLC 670, named Paddington.
Their activity is summed before feature construction, so Paddington contributes
one observation to the GMM rather than two.

The current station-count chain is:

| Stage | Units |
|---|---:|
| Raw NUMBAT NLCs | 471 |
| After 14 co-located groups merge (29 source NLCs to 14 units) | 456 |
| NaPTAN-matched preprocessing output | 440 |
| After removing 37 zero-night-activity tram units | 403 |

Paddington's current adopted label is C2 (central interchange,
direction-balanced), with maximum posterior probability 0.9999993. Flow
conservation was checked before and after the merge: the maximum absolute
cell difference was 1.46e-11 and the total difference was -7.45e-09, both
floating-point noise.

## Search for similar Rail problems

- No duplicate NLC remains in the merge crosswalk.
- No current labelled station-coordinate pair is within 100 metres.
- The only repeated normalised names are Edgware Road (District/Bakerloo)
  and Hammersmith (District/Hammersmith & City). Their coordinates are about
  185 m and 238 m apart respectively; these are distinct station complexes,
  so they were not merged.

Conclusion: no other Paddington-like duplicated physical observation was
found in the current Rail clustering population.

## Bus audit

The Bus pipeline was checked at source StopPoint, official child StopArea,
LSOA aggregation, feature matrix and label stages:

- 19,589 source stop rows: unique `STOP_CODE`, no duplicate key.
- 12,007 allocated units: 10,768 official child StopAreas plus 1,239
  singleton fallbacks; no duplicate unit key.
- The long LSOA table has no duplicate `(day_type, direction, lsoa,
  hour_bin)` key.
- 3,797 active LSOAs enter the label files; 3,372 pass the fit rule and 425
  are consistently marked excluded (`cluster=-1`).
- Both raw-share and CLR feature matrices contain 3,372 unique LSOAs.
- Matched StopArea activity equals the aggregated long-table total
  (6,930,047.30656). Unmatched activity is separately retained in the audit
  (102,172.09132), not silently duplicated or lost.

Fifteen pairs of child StopAreas share a parent interchange, lie within
100 m, and fall on opposite sides of an LSOA boundary (29 unique units;
61,589.62 activity, 0.889% of matched activity). Four of the retained
cross-boundary pairs receive different CLR cluster labels. This is a boundary
allocation sensitivity, not a duplicate final observation: the adopted Bus
study unit is the LSOA and the official rule intentionally uses child
StopAreas. Merging these pairs would change the spatial unit definition and
was therefore not done silently.

Conclusion: no Paddington-like duplicated fitted row was found in Bus. The
small parent-interchange boundary set should be disclosed as a sensitivity,
not corrected as duplication.

## Regenerated outputs

The following were regenerated from the corrected 403-station labels:

- Rail K=5/6/7 profiles and maps, BIC diagnostics, four-covariance grid and
  equal-budget K-selection panel.
- K=5-vs-K=6 and K=5-vs-K=7 200-bootstrap/20-seed reports and five diagnostic
  figures for each pair.
- RQ2 continuous-context, LNWC and IMD outputs at both 1,200 m and 800 m.
- Bus–Rail link table, association tests, distance-band results, overlay map
  and related figures.

Visual spot checks passed for the K=5 profile plot, K=5 station map and the
Bus-cluster/Rail-station overlay.
