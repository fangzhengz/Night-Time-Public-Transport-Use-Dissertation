# -*- coding: utf-8 -*-
"""03 · Feature matrices — ONE whole-week vector per unit, per modality.

NO weekday/weekend bucketing. The week is concatenated DAY BY DAY using the
native day-types the data provides:
  rail: MON, TWT(=Tue-Thu avg), FRI, SAT, SUN  (each sliced to its night window;
        FRI/SAT run to 05:00 = Night Tube, the others to 01:00).
  bus : Weekday, Saturday, Sunday              (18:00-06:00 hourly).
Each day is one representative night. Per direction the concatenated weekly
vector is normalised over the WHOLE WEEK to sum 1 (entry across all days' bins
sums to 1; exit likewise), so across-day magnitude (weekend / Night-Tube
intensity) is a discriminating feature. Keep low-activity units (drop only empty).

Output: features/X_{modality}.parquet, features/{modality}_meta.csv
Column names: "{direction}_{day}_{bin}".
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def assemble(per_day, unit, directions, days):
    """per_day: dict[(day,direction)] -> DataFrame[unit x bin counts].
    Concat days (in `days` order) per direction; normalise each direction over
    the whole week to sum 1. Returns X, totals, dropped."""
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
    keep = totals.index[totals["total_activity"] >= C.MIN_TOTAL]
    return X.loc[keep], totals.loc[keep], len(X) - len(keep)


def pivot_day(df, unit, bin_col):
    w = df.pivot_table(index=unit, columns=bin_col, values="count", fill_value=0.0)
    return w.reindex(sorted(w.columns), axis=1)


def main():
    log = []

    # ---- rail: raw all-day-types, slice each day to its night window ----
    raw = pd.read_parquet(C.RAIL_RAW_SRC)
    raw["NLC"] = raw["NLC"].astype(str); raw["day_type"] = raw["day_type"].astype(str)
    per_day = {}
    for day in C.RAIL_DAYS:
        lo, hi = C.RAIL_DAY_WINDOWS[day]
        d = raw[(raw.day_type == day) & (raw.extended_minute >= lo) & (raw.extended_minute < hi)]
        for direction in C.RAIL_DIRECTIONS:
            per_day[(day, direction)] = pivot_day(d[d.direction == direction], "NLC", "extended_minute")
    Xr, mr, dr = assemble(per_day, "NLC", C.RAIL_DIRECTIONS, C.RAIL_DAYS)
    Xr.to_parquet(C.FEAT / "X_rail.parquet"); mr.to_csv(C.FEAT / "rail_meta.csv")
    log.append(f"RAIL full-week (days {C.RAIL_DAYS}): X {Xr.shape} | dropped<{C.MIN_TOTAL}: {dr} | "
               f"per-direction row-sum {Xr.sum(1).min():.2f}/{Xr.sum(1).max():.2f} (expect 2.00)")

    # ---- bus: validated hourly LSOA long table (day_type x hour_bin) ----
    bus = pd.read_parquet(C.BUS_LONG); bus["lsoa"] = bus["lsoa"].astype(str)
    per_day = {}
    for day in C.BUS_DAYS:
        d = bus[bus.day_type == day]
        for direction in C.BUS_DIRECTIONS:
            per_day[(day, direction)] = pivot_day(d[d.direction == direction], "lsoa", "hour_bin")
    Xb, mb, db = assemble(per_day, "lsoa", C.BUS_DIRECTIONS, C.BUS_DAYS)
    Xb.to_parquet(C.FEAT / "X_bus.parquet"); mb.to_csv(C.FEAT / "bus_meta.csv")
    log.append(f"BUS  full-week (days {C.BUS_DAYS}): X {Xb.shape} | dropped<{C.MIN_TOTAL}: {db} | "
               f"per-direction row-sum {Xb.sum(1).min():.2f}/{Xb.sum(1).max():.2f} (<=2.00)")

    (C.FEAT / "feature_audit.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
