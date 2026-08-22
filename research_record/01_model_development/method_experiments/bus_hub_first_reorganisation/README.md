# RQ1 bus hub-first reorganisation

This workspace rebuilds the bus spatial preprocessing in the order confirmed
for the revised RQ1 analysis:

```text
BUSTO stopcode
-> official bus StopArea
-> highest available ParentStopArea code (grouping identifier only)
-> aggregate stop demand to a logical bus hub
-> choose a representative point from member BUS StopArea coordinates
-> assign the complete hub to one LSOA21
-> aggregate hubs to LSOA
```

No rail passenger counts, rail temporal features, or rail coordinates are used.
External rail/Underground-style ParentStopArea codes are identifiers that show
which bus StopAreas belong to the same interchange.

## Representative point

- A hub with one official bus StopArea uses that StopArea's official point.
- A parent hub with several bus StopAreas uses the **medoid** of the official
  child bus StopArea points: the actual member point whose total distance to
  the other member points is smallest.
- A BUSTO stop without usable NaPTAN StopArea information falls back to a
  singleton bus-stop point.

The medoid is independent of passenger volume and always remains an observed
bus location. It avoids a mean centroid falling inside a station building,
railway, river, or another LSOA.

## Run

```powershell
python src/run_hub_first_reorganisation.py
```

## Main outputs

- `outputs/preprocessed/stop_to_logical_hub_crosswalk.csv`
- `outputs/preprocessed/logical_hub_lsoa_crosswalk.csv`
- `outputs/preprocessed/bus_hub_night_qhr_all.parquet`
- `outputs/preprocessed/bus_hub_night_qhr_london.parquet`
- `outputs/preprocessed/bus_lsoa_night_long.parquet`
- `outputs/data/lsoa_old_vs_hub_first_totals.csv`
- `outputs/data/lsoa_direction_eligibility.csv`
- `outputs/data/lsoa_group_direction_eligibility.csv`
- `outputs/data/one_direction_exception_areas.csv`
- `outputs/data/movement_decomposition.csv`
- `outputs/data/boundary_inclusion_changes.csv`
- `outputs/data/unresolved_coordinate_stops.csv`
- `outputs/data/remaining_exact_direction_zero_lsoas.csv`
- `outputs/data/reorganisation_summary.csv`
- `outputs/data/input_manifest.csv`
- `outputs/report/RESULTS_SUMMARY.md`

`bus_lsoa_night_long.parquet` has the same schema expected by the existing bus
feature-building stage: `day_type, direction, lsoa, hour_bin, count`.

## Interpretation boundary

This is a spatial-unit reconstruction, not a clustering result. It conserves
all stop-level demand before the London boundary assignment and explicitly
reports demand that moves between LSOAs, is newly included, or is newly
excluded. The complete LSOA data are not silently filtered: exact
one-direction-zero profiles are supplied as separate overall and
weekday/weekend eligibility flags for the clustering stage. Low-flow shrinkage
and GMM fitting belong to the next stage.

The group-level rule is explicit: an LSOA with exactly zero boardings or
alightings after final LSOA aggregation is retained as a
`one_direction_exception` but is not eligible for the core two-direction
clustering. This decision is applied independently of the minimum-total rule.
