# -*- coding: utf-8 -*-
"""03 · Feature matrices — ONE per (modality, day-group), clustered separately.

Day groups (service-regime motivated, see config):
  rail: weekday = MON+TWT (~01:00 close); weekend = Fri+Sat pooled (Night Tube, 05:00).
        Sunday excluded.
  bus : weekday = Weekday; weekend = Sat+Sun pooled.

Within a group the member day-times are POOLED (counts summed -> one night
profile) so the overnight signal reinforces instead of being diluted. Then
per-vector normalise each direction block to sum 1 (BtC; this IS the
standardisation, no StandardScaler). Drop units with total activity < MIN_TOTAL.

Output: features/X_{modality}_{group}.parquet, features/{modality}_{group}_meta.csv
Column names: "{direction}_{bin}".
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def build_group(long, unit, group_col, members, directions, bin_col):
    """Pool member day-times (sum counts), per-vector normalise per direction."""
    sub = long[long[group_col].isin(members)]
    g = sub.groupby([unit, "direction", bin_col], as_index=False)["count"].sum()
    share_parts, total_parts = [], []
    for direction in directions:
        d = g[g.direction == direction]
        wide = d.pivot_table(index=unit, columns=bin_col, values="count", fill_value=0.0)
        wide = wide.reindex(sorted(wide.columns), axis=1)
        blk_total = wide.sum(axis=1)
        share = wide.div(blk_total.replace(0, np.nan), axis=0).fillna(0.0)
        share.columns = [f"{direction}_{int(c)}" for c in share.columns]
        share_parts.append(share)
        total_parts.append(blk_total.rename(f"tot_{direction}"))
    X = pd.concat(share_parts, axis=1).fillna(0.0)
    totals = pd.concat(total_parts, axis=1).fillna(0.0)
    totals["total_activity"] = totals.sum(axis=1)
    X = X.loc[totals.index]
    keep = totals.index[totals["total_activity"] >= C.MIN_TOTAL]
    dropped = len(X) - len(keep)
    return X.loc[keep], totals.loc[keep], dropped


def main():
    log = []
    rail = pd.read_parquet(C.PRE / "rail_station_night_long.parquet"); rail["NLC"] = rail["NLC"].astype(str)
    for grp, members in C.RAIL_GROUPS.items():
        X, m, dr = build_group(rail, "NLC", "daytime", members, C.RAIL_DIRECTIONS, "ext_minute")
        X.to_parquet(C.FEAT / f"X_rail_{grp}.parquet"); m.to_csv(C.FEAT / f"rail_{grp}_meta.csv")
        log.append(f"RAIL {grp} (pool {members}): X {X.shape} | dropped<{C.MIN_TOTAL}: {dr} | "
                   f"row-sum {X.sum(1).min():.2f}/{X.sum(1).max():.2f}")

    bus = pd.read_parquet(C.PRE / "bus_lsoa_night_long.parquet"); bus["lsoa"] = bus["lsoa"].astype(str)
    for grp, members in C.BUS_GROUPS.items():
        X, m, db = build_group(bus, "lsoa", "day_type", members, C.BUS_DIRECTIONS, "hour_bin")
        X.to_parquet(C.FEAT / f"X_bus_{grp}.parquet"); m.to_csv(C.FEAT / f"bus_{grp}_meta.csv")
        log.append(f"BUS {grp} (pool {members}): X {X.shape} | dropped<{C.MIN_TOTAL}: {db} | "
                   f"row-sum {X.sum(1).min():.2f}/{X.sum(1).max():.2f}")

    (C.FEAT / "feature_audit.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
