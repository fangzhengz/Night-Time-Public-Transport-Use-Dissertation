# Bus LSOA coverage tiers (all 4,994 Greater London LSOAs)

Reliable-core threshold: total_activity >= 450.0

IMPORTANT: tier labels describe what was OBSERVED in BUSTO ridership
data. They must not be read as "no bus service" -- BUSTO records
realised boardings/alightings, not timetables or route frequency.
A tier-0 LSOA may simply have no stop that BUSTO's stop-code table
matched to a coordinate, not literally zero buses.

| tier                       |   n_lsoa |   pct_of_all_london_lsoa |
|:---------------------------|---------:|-------------------------:|
| 0_no_recorded_activity     |      813 |                     16.3 |
| 1_matched_stop_no_activity |       88 |                      1.8 |
| 2_below_reliable_threshold |     1644 |                     32.9 |
| 3_reliable_core            |     2449 |                     49   |

## Tier definitions

- **0_no_recorded_activity**: no BUSTO stop matched to this LSOA at all.
- **1_matched_stop_no_activity**: a stop matched, but recorded activity
  is effectively zero -- excluded even under the current MIN_TOTAL=1 rule.
- **2_below_reliable_threshold**: in the 4,100-unit study, but below the
  reliable-core threshold -- report descriptively (volume, IMD/LNWC
  context), do not force into the shape-clustering.
- **3_reliable_core**: enters `03_recluster_reliable_core.py`.