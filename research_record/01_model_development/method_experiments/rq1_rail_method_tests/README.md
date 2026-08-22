# rq1_rail_daytype_normalisation — FROZEN 2026-08-01

Rail raised a different version of the normalisation problem because its day types originally covered unequal night windows. Padding every day to a common 18:00–05:00 window might improve comparability, but it could also add a large block of structural zeros; closing each day separately might amplify Night Tube differences for purely mathematical reasons. This four-cell experiment was designed to disentangle those effects before a seemingly tidy representation was adopted.

This is the Rail counterpart to `rq1_bus_daytype_normalisation`. Read-only:
`numbat_all_area_test` was never modified and remains the adopted result
(all-modes 404-station K=5).

**Outcome: full-week closure retained, and padding rejected.** Appendix material.

## Addendum 2026-08-02 — C2 nested split corrected, then moved

`outputs/c4_substructure/` (script `07_c4_substructure.py`) is **stale**: it
was run before the same-session padded-window adoption and cluster
renumbering, against `X_fullweek_unpadded.parquet` (344-dim) with
`PARENT_CLUSTER=4`. Its core_n=13 predates both changes. Left in place only
as a historical record — do not cite.

The corrected version (core n=16, 10/10 seeds, against the currently
adopted padded matrix and current C2 id) briefly lived here as
`10_c2_substructure_current.py` / `outputs/c2_substructure/`, then was
**relocated to `numbat_all_area_test/cluster_substructure/`** on the same
day — this is active, undecided-scope work (write-up placement not yet
settled), not frozen appendix material, so it belongs alongside the primary
adopted pipeline rather than in this archive. See that folder's README for
the current content.

`config.py` also had a path bug from the archive move (`FYP` resolved one
level too shallow, to this archive folder instead of the real `FYP/`) —
fixed with an existence check rather than a hardcoded path, so it survives
another relocation. This fix stays here since it affects any of this
folder's own scripts (01-09) if rerun.

## Design — a full 2×2, deliberately

The bus sidecar's strict variant changed closure *and* sample together, leaving
its headline numbers unattributable. Rail has the same trap in another form,
because the five day types do not share a window:

```
MON / TWT / SUN   18:00-01:00   28 quarter-hour bins
FRI / SAT         18:00-05:00   44 quarter-hour bins
```

Under full-week closure that is harmless. Under day-type closure a 7-hour Monday
and an 11-hour Friday each receive mass 1.0, so Monday's columns sit ~1.6× higher
for reasons unrelated to behaviour. Rather than guess, all four cells were fitted:

|              | full-week closure   | day-type closure   |
|--------------|---------------------|--------------------|
| native 344   | `fullweek_unpadded` | `daytype_unpadded` |
| padded 440   | `fullweek_padded`   | `daytype_padded`   |

## Anchoring — three independent checks

`fullweek_unpadded` is a re-implementation of the adopted pipeline, and is
asserted against it rather than assumed equal:

| check | result |
|---|---|
| feature matrix vs `X_rail_allmodes.parquet` | max abs diff **0.0** |
| labels vs `rail_allmodes_k5_labels.csv` | **ARI 1.000** |
| seed stability K=5 / K=7 / K=6 | **0.894 / 0.703 / 0.624** (matches the adopted battery) |

`01_prepare_features.py` raises on the first of these, so a future drift fails
loudly instead of producing a plausible table.

## What it found

- **Padding is inert.** At K=5 zero-cell η² moves 0.001; across K=2..12 the solid
  and dashed lines of each colour overlap in every diagnostic panel. Not worth 96
  extra dimensions at n=404. Note the earlier belief that NUMBAT has non-zero
  values everywhere is wrong — the long table stores explicit zeros, and true
  zero-cell share is 10.5% native / 26.1% padded.
- **Closure matters, in both directions at once.** At K=5: night-tube extension
  η² 0.17→0.59, zero-cell η² 0.13→0.43, silhouette 0.102→0.035, smallest cluster
  12→35, bootstrap ARI 0.500→0.612, ARI vs adopted 0.294, BIC-best K 5→9.
  `activity_eta2` does not move — closure does not touch volume domination here.
- **The night-signal gain is not disproportionate.** night-tube η² / zero-cell η²
  is ~1.2-1.4 under *both* closures, so day-type closure amplifies signal and
  zero structure together. η² cannot separate them. The profile plots can, and do
  show real entry-vs-exit asymmetry — see `outputs/figures/04_*`.
- **K=9 does not earn its clusters.** The four extra clusters all sit at
  night-tube extension 0.001-0.017 and subdivide the outer non-Night-Tube mass by
  mode and centrality, not by night behaviour.

## Run order

```bash
python src/01_prepare_features.py
python src/02_run_clustering.py --variant fullweek_unpadded      # and the other three
python src/03_compare.py
python src/04_figures.py --variant daytype_unpadded
python src/05_diagnostic_figures.py
```
