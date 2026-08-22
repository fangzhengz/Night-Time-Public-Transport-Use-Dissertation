# Reliable-core K=3 vs adopted MIN_TOTAL=1 K=3

Adopted solution cluster sizes: {0: 336, 1: 2763, 2: 1001}
Reliable-core K=3 cluster sizes: {0: 723, 1: 1519, 2: 210}

|                           |   adopted_MIN_TOTAL=1_K=3 |   reliable_core_K=3 |
|:--------------------------|--------------------------:|--------------------:|
| distance_to_centre        |                 0.0486394 |           0.0654982 |
| log_total_activity        |                 0.489659  |           0.0977058 |
| direction_balance         |                 0.0106254 |           0.055808  |
| post_midnight_share       |                 0.257151  |           0.283747  |
| deep_night_share          |                 0.168143  |           0.284793  |
| post_midnight_persistence |                 0.226193  |           0.263875  |
| weekend_ratio             |                 0.030778  |           0.0567243 |

## Reading

- eta2 for log_total_activity should be far lower in the reliable-core
  column than the adopted column if the activity-domination problem is
  resolved by threshold-filtering, not by chance.
- eta2 for the late-night timing metrics (post_midnight_share,
  deep_night_share, post_midnight_persistence) should be comparable to or
  higher in the reliable-core column -- evidence the freed-up variance is
  now organised around genuine rhythm, not noise.
- eta2 for distance_to_centre is not expected to jump dramatically; a
  modest, stable value here is itself informative (bus late-night rhythm
  is not strongly tied to simple centre-periphery distance, independent
  of the activity-noise problem).