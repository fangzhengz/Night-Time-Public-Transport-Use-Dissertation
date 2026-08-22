# Bus StopArea-only isolation test

This sidecar isolates a single upstream choice: use each NaPTAN child
`StopAreaCode` as the bus spatial unit and ignore `ParentStopAreaRef` when
grouping demand. It is designed alongside `rq1_bus_hub_first_isolated_test`.

## Single changed variable

```text
parent-hub-first: StopPoint -> child StopArea -> highest ParentStopArea -> LSOA
StopArea-only:    StopPoint -> child StopArea -----------------------> LSOA
```

Stops without a usable child StopArea remain singleton `STOP::<STOP_CODE>`
units. A child StopArea uses its official NaPTAN coordinate; if that coordinate
is missing, the unit falls back to the medoid of its member bus-stop points.

The validated stop/NaPTAN crosswalk from
`rq1_bus_hub_first_reorganisation` is reused read-only. Parent fields remain in
that audit table but are not used to form StopArea-only units.

## Downstream analysis held fixed

The feature and GMM stages execute the exact source modules from
`rq1_bus_hub_first_isolated_test` with only output/input paths rebound to this
sidecar:

- `MIN_TOTAL = 1`
- no one-direction exclusion
- no weaker-direction floor
- alpha=0 raw direction shares
- the same 72 full-week features
- K=2..12 and the same four covariance families
- `n_init=20`, `reg_covar=1e-6`, `max_iter=300`, seed=42
- the same 20-resample bootstrap ARI implementation

This makes the spatial preprocessing the only analytical change.

## Run

```powershell
python src\00_build_stoparea_only_long.py
python src\01_build_features.py
python src\02_cluster.py
python src\03_compare.py
python src\04_figures.py
```

## Main outputs

- `outputs/preprocessed/bus_lsoa_night_long.parquet`
- `outputs/features/X_bus.parquet`
- `outputs/diagnostics/bus_bic_grid.csv`, `bus_kdiag.csv`
- `outputs/labels/bus_k{3..8}_labels.csv`
- `outputs/report/STOPAREA_ONLY_PREPROCESSING.md`
- `outputs/report/STOPAREA_ONLY_ISOLATED_COMPARISON.md`
