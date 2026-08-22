# cluster_clean_version_fullweek

This folder captures the point at which the project moved from separate weekday/weekend solutions toward a single account of the whole observed week. It established many of the conventions that later experiments questioned—especially full-week closure, the treatment of low-activity areas and the use of separate directional compositions. Its importance is historical: later corrections changed both the analytical units and the adopted clusters, but those changes are easier to understand against this baseline.

It is the **full-week variant** of the RQ1 night-time clustering pipeline, built after the
Clara catch-up (2026-06-25). Parallel to `cluster_clean_version` (concatenated)
and `cluster_clean_version_grouped` (separate weekday/weekend clusterings); those
are kept intact for comparison.

## What changed vs. the grouped version

| | grouped (previous) | full-week (this) |
|---|---|---|
| Datasets | 4: rail/bus × weekday/weekend | **2: rail, bus** |
| Feature vector | one day-group profile | **whole week concatenated DAY BY DAY** |
| Day handling | bucketed weekday vs weekend | **no bucketing** — each native day-type a segment |
| Normalisation | each direction block → sum 1 | **each direction over the WHOLE WEEK → sum 1** |
| Low-activity units | dropped (total < 50) | **kept** (only fully-empty dropped) |
| Window / granularity | 18:00–06:00; rail 15-min, bus hourly | 18:00–06:00; **rail 15-min, bus hourly** (native) |
| bus + rail combined? | no | no (deferred) |

**Day segments.** rail: `MON, TWT(=Tue-Thu), FRI, SAT, SUN` (FRI/SAT to 05:00 =
Night Tube, others to 01:00) → 172 bins/direction, **X_rail = 270×344**.
bus: `Weekday, Saturday, Sunday` (18:00–06:00, hourly) → 36 bins/direction,
**X_bus = 4100×72**. BUSTO cannot isolate Friday, so bus "Weekday" pools all weekdays.

**Granularity note.** This folder keeps each modality at its NATIVE slice (rail
15-min, bus hourly). A 15-min bus trial (for cross-mode slice consistency) made
bus clustering markedly noisier (BIC ran away to K=12, singleton clusters), so it
was reverted. The slice-consistent route is pursued at **1-hour for both** in the
sibling folder `cluster_clean_version_1h`.

**Why full week, day by day.** Weekend / Night-Tube behaviour is the key
separating signal (Clara's paper): stations alike on weekdays flip on weekends.
Concatenating the whole week into one (longer) vector and normalising each
direction *over the whole week* preserves the across-day magnitude balance, so
weekend intensity is a discriminating dimension rather than normalised away.
Each segment is a single day-type, so there is no within-segment pooling and no
sum-vs-mean weighting issue. Sunday is simply its own segment (no weekday/weekend
assignment needed).

## Layout

- `src/config.py` — paths + parameters. Rail reads RAW
  `numbat_lu_station_qhr_all_daytypes.parquet` (5 native day-types); bus reuses the
  grouped variant's validated `bus_lsoa_night_long.parquet`. Days, windows,
  normalisation, `MIN_TOTAL`.
- `src/03_build_features.py` — day-by-day concat + whole-week per-direction
  normalisation. → `outputs/features/X_{rail,bus}.parquet`, columns
  `{direction}_{day}_{minute}` (day ∈ rail {MON,TWT,FRI,SAT,SUN} / bus
  {Weekday,Saturday,Sunday}).
- `src/04_cluster.py` — GMM, BIC grid over covariance×K, K-diagnostics
  (silhouette/CH/DB + bootstrap ARI), labels for K=3..8. → `outputs/diagnostics/`,
  `outputs/labels/`.
- `src/05_figures.py` — BIC grid, K-diagnostics, per-K cluster profiles (day by
  day, with a divider between days) and maps. → `outputs/figures/`.

## Run

```bash
cd src
python 03_build_features.py
python 04_cluster.py
python 05_figures.py
```

## Open decisions (config toggles)

- **Sunday**: kept as its own segment for both modes (no weekday/weekend
  assignment). Rail Sunday has no Night Tube (window to 01:00). Change the day set
  via `RAIL_DAYS` / `BUS_DAYS`.
- **Noise floor**: `MIN_TOTAL = 1` keeps low-activity units per Clara. Raise to
  reinstate a floor.
- **K**: not hard-picked — candidates 3..8 written; choose with Clara next meeting
  (BIC favours K=2, which is uninformative; use diagnostics + interpretability).

## Next (RQ2)

Link the full-week cluster labels (rail station points / bus LSOAs) to the London
night-worker LSOA classification — "which station type sits in which night-worker
LSOA type" — rather than building a new LSOA classification from ridership.
