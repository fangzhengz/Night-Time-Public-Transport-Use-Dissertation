from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

"""02 - Build the full-week 440-dim rail feature matrix for ALL NUMBAT modes.

2026-08-01: widened from 344 to 440 dimensions. Every day type now runs a
common 18:00-05:00 window instead of truncating MON/TWT/SUN at 01:00. See the
RAIL_DAY_WINDOWS comment below for the reasoning, the evidence, and what it
changed (ARI 0.885, 16 of the pre-Paddington-correction 404 stations). The
pre-change outputs are archived at
`outputs/archive_native_windows_2026-08-01/`.

Reuses the `assemble()` / `pivot_day()` logic from
`FYP/cluster_clean_version_fullweek/src/03_build_features.py` unchanged (that
code is already generic over a "unit" index -- NLC here, same as the
canonical rail run). The only difference is the input.

2026-07-24: `RAW_LONG` now points at `FYP/data_processing/rail_allmodes/`'s
final preprocessed output (currently 440 NaPTAN-Greater-London-matched stations,
merged co-located sites) instead of a local copy of the same data --
preprocessing/station-filtering now lives entirely in that separate,
self-contained folder (mirroring `data_processing/bus_stoparea/`'s
separation from `rq1_bus_stoparea_clustering/`). This script's own
`MIN_TOTAL=1` filter (in `assemble()`) still independently drops the 37
tram-only, zero-activity stations, arriving at the current clustering
population (403 stations after the 2026-08-07 Paddington co-location fix). See
`data_processing/rail_allmodes/outputs/report/RAIL_ALLMODES_PREPROCESSING.md`
for the full station-count chain. `01`/`01b`/`01c`/`01d`, which used to
live in this folder, have moved there too.

Column schema, day windows, and directions are kept identical to
`cluster_clean_version_fullweek/src/config.py` so the resulting 344 columns
line up one-to-one with the canonical X_rail.parquet columns.
"""

FYP_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
RAW_LONG = (
    FYP_ROOT / "data_processing" / "rail_allmodes" / "outputs" / "preprocessed"
    / "numbat_allmodes_station_qhr_all_daytypes_final.parquet"
)

X_OUTPUT = OUT_DIR / "X_rail_allmodes.parquet"
META_OUTPUT = OUT_DIR / "rail_allmodes_feature_meta.csv"
AUDIT_OUTPUT = OUT_DIR / "rail_allmodes_feature_audit.txt"

# Must match cluster_clean_version_fullweek/src/config.py exactly.
EVENING_START = 18 * 60  # 1080
RAIL_CLOSE = 25 * 60  # 01:00 -> 1500 (no Night Tube)
NIGHT_TUBE_END = 29 * 60  # 05:00 -> 1740 (Night Tube nights)
RAIL_DAYS = ["MON", "TWT", "FRI", "SAT", "SUN"]

# 2026-08-01: every day type now runs the SAME 18:00-05:00 window (440
# features), replacing the former day-type-dependent windows that truncated
# MON/TWT/SUN at 01:00 (344 features).
#
# Why. The 01:00 cut was inherited from an Underground-only design, where the
# network really is closed after 01:00 on non-Night-Tube nights. On the merged
# all-modes population it is not true: National Rail and Elizabeth line services
# run later, and the truncation discarded 0.18-0.24% of MON/TWT/SUN evening
# activity across 368 of the pre-correction 404 stations. A uniform window also removes the
# unequal-window question entirely and matches the bus pipeline, which already
# uses one window for all three of its day types.
#
# What it costs. Tested before adoption in FYP/rq1_rail_method_tests/ (the
# `fullweek_padded` cell, and 06_robustness_padded.py at the converged
# optimum): ARI 0.885 against the native-window result, 16 of the
# pre-correction 404 stations
# (4.0%) change cluster - all outer/mid-ring boundary cases - and the smallest
# cluster is the identical 12 stations. Under full-week closure the added bins
# cannot bias anything: they carry 0.142% of feature mass and rescale the 344
# shared columns by a median factor of 0.9995.
#
# NOTE the retention rule below is still computed on the NATIVE window, so
# window padding itself cannot change the clustering population.
RAIL_DAY_WINDOWS = {day: (EVENING_START, NIGHT_TUBE_END) for day in RAIL_DAYS}
RAIL_DAY_WINDOWS_NATIVE = {
    "MON": (EVENING_START, RAIL_CLOSE),
    "TWT": (EVENING_START, RAIL_CLOSE),
    "FRI": (EVENING_START, NIGHT_TUBE_END),
    "SAT": (EVENING_START, NIGHT_TUBE_END),
    "SUN": (EVENING_START, RAIL_CLOSE),
}
RAIL_DIRECTIONS = ["entry", "exit"]
MIN_TOTAL = 1


def pivot_day(df: pd.DataFrame, unit: str, bin_col: str) -> pd.DataFrame:
    w = df.pivot_table(index=unit, columns=bin_col, values="count", fill_value=0.0)
    return w.reindex(sorted(w.columns), axis=1)


def assemble(per_day: dict, directions: list[str], days: list[str], keep_units=None):
    """Concat days per direction; normalise each direction over the whole
    week to sum 1. Returns X, totals, dropped-row-count -- identical logic to
    cluster_clean_version_fullweek/src/03_build_features.py::assemble.
    """
    raw_parts, total_parts = [], []
    all_units = sorted({u for df in per_day.values() for u in df.index})
    for direction in directions:
        blocks = []
        for day in days:
            wide = per_day[(day, direction)].reindex(all_units).fillna(0.0)
            wide.columns = [f"{direction}_{day}_{int(c)}" for c in wide.columns]
            blocks.append(wide)
        counts = pd.concat(blocks, axis=1).fillna(0.0)
        dir_total = counts.sum(axis=1)
        share = counts.div(dir_total.replace(0, np.nan), axis=0).fillna(0.0)
        raw_parts.append(share)
        total_parts.append(dir_total.rename(f"tot_{direction}"))
    X = pd.concat(raw_parts, axis=1).fillna(0.0)
    totals = pd.concat(total_parts, axis=1).fillna(0.0)
    totals["total_activity"] = totals.sum(axis=1)
    if keep_units is None:
        keep = totals.index[totals["total_activity"] >= MIN_TOTAL]
    else:
        # Retention decided on the NATIVE window so that widening the window
        # cannot change which stations are clustered. Without this, padding
        # could admit a station that only clears MIN_TOTAL on the newly added
        # 01:00-05:00 bins, silently changing the population as a side effect
        # of a window edit.
        keep = totals.index.intersection(pd.Index(keep_units))
    return X.loc[keep], totals.loc[keep], len(X) - len(keep)


def main() -> None:
    log = []

    raw = pd.read_parquet(RAW_LONG)
    raw["NLC"] = raw["NLC"].astype(str)
    raw["day_type"] = raw["day_type"].astype(str)

    # Retention is decided on the NATIVE window first, so the station
    # population is a property of the data and not of the window edit.
    native = {}
    for day in RAIL_DAYS:
        lo, hi = RAIL_DAY_WINDOWS_NATIVE[day]
        d = raw[(raw.day_type == day) & (raw.extended_minute >= lo) & (raw.extended_minute < hi)]
        for direction in RAIL_DIRECTIONS:
            native[(day, direction)] = pivot_day(d[d.direction == direction], "NLC", "extended_minute")
    _, native_totals, native_dropped = assemble(native, RAIL_DIRECTIONS, RAIL_DAYS)
    keep_units = native_totals.index

    per_day = {}
    for day in RAIL_DAYS:
        lo, hi = RAIL_DAY_WINDOWS[day]
        d = raw[(raw.day_type == day) & (raw.extended_minute >= lo) & (raw.extended_minute < hi)]
        for direction in RAIL_DIRECTIONS:
            per_day[(day, direction)] = pivot_day(d[d.direction == direction], "NLC", "extended_minute")

    X, totals, dropped = assemble(per_day, RAIL_DIRECTIONS, RAIL_DAYS, keep_units=keep_units)
    dropped = native_dropped

    # carry mode_label + a few identifiers onto the meta table for downstream comparison
    station_id = (
        raw[["NLC", "ASC", "Station", "Fare Zone", "mode_label"]]
        .drop_duplicates("NLC")
        .set_index("NLC")
    )
    meta = totals.join(station_id, how="left")

    X.to_parquet(X_OUTPUT)
    meta.to_csv(META_OUTPUT)

    log.append(
        f"RAIL all-modes full-week (days {RAIL_DAYS}): X {X.shape} | "
        f"dropped<{MIN_TOTAL}: {dropped} | "
        f"per-direction row-sum {X.sum(1).min():.2f}/{X.sum(1).max():.2f} (expect 2.00)"
    )
    AUDIT_OUTPUT.write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))
    print("Saved:", X_OUTPUT)
    print("Saved:", META_OUTPUT)


if __name__ == "__main__":
    main()
