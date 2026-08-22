# -*- coding: utf-8 -*-
"""01 - Feature matrix, bus only -- byte-for-byte the same logic as
../../cluster_clean_version_fullweek/src/03_build_features.py's bus branch
(assemble/pivot_day), reading the hub-first long table instead. See
config.py's module docstring for exactly what is and is not held fixed.

Output: features/X_bus.parquet, features/bus_meta.csv
Column names: "{direction}_{day}_{bin}".
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def assemble(per_day, directions, days):
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
    bus = pd.read_parquet(C.BUS_LONG)
    bus["lsoa"] = bus["lsoa"].astype(str)
    per_day = {}
    for day in C.BUS_DAYS:
        d = bus[bus.day_type == day]
        for direction in C.BUS_DIRECTIONS:
            per_day[(day, direction)] = pivot_day(d[d.direction == direction], "lsoa", "hour_bin")
    Xb, mb, db = assemble(per_day, C.BUS_DIRECTIONS, C.BUS_DAYS)
    Xb.to_parquet(C.FEAT / "X_bus.parquet")
    mb.to_csv(C.FEAT / "bus_meta.csv")
    log = (
        f"BUS full-week, hub-first input (days {C.BUS_DAYS}): X {Xb.shape} | "
        f"dropped<{C.MIN_TOTAL}: {db} | "
        f"per-direction row-sum {Xb.sum(1).min():.2f}/{Xb.sum(1).max():.2f} (<=2.00)"
    )
    (C.FEAT / "feature_audit.txt").write_text(log, encoding="utf-8")
    print(log)


if __name__ == "__main__":
    main()
