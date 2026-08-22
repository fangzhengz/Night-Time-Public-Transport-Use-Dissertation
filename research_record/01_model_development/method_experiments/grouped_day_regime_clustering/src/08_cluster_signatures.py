# -*- coding: utf-8 -*-
"""08 · Cluster signatures for interpretation (additive, isolated).

For the chosen K per dataset (rail_weekday=5, rail_weekend=4, bus=4), quantify
each cluster on the interpretable dimensions so it can be named functionally:
  - size, share of units, mean total night volume;
  - net directionality A_net = (in-out)/(in+out): >0 origin (people depart),
    <0 destination (people arrive);  [rail entry/exit, bus boardings/alightings]
  - timing: median time of total activity; evening (18-20h), late (00:00+),
    nightlife hump (22-23h) shares of the TRUE total temporal profile
    (reconstructed from per-direction shares x direction volumes);
  - assignment confidence (mean max_posterior, entropy);
  - representative units (top by total night volume) with names.

Reads features/labels/meta read-only; writes ONLY to outputs/interpretation/.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

INTERP = C.OUT / "interpretation"
INTERP.mkdir(parents=True, exist_ok=True)

JOBS = {"rail_weekday": 5, "rail_weekend": 4, "bus_weekday": 4, "bus_weekend": 4}
EV = (18 * 60, 20 * 60)        # evening
LATE = 24 * 60                  # 00:00+
HUMP = (22 * 60, 23 * 60)       # nightlife hump


def minute_of(c):
    return int(c.rsplit("_", 1)[1])


def hhmm(m):
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def load(ds):
    mod, grp = ds.split("_")
    X = pd.read_parquet(C.FEAT / f"X_{ds}.parquet"); X.index = X.index.astype(str)
    meta = pd.read_csv(C.FEAT / f"{mod}_{grp}_meta.csv", index_col=0); meta.index = meta.index.astype(str)
    dirs = C.RAIL_DIRECTIONS if mod == "rail" else C.BUS_DIRECTIONS
    if mod == "rail":
        names = pd.read_csv(C.PRE / "rail_coords.csv", dtype={"NLC": str}).set_index("NLC")
        name_col, ecol, ncol = "Station", "easting", "northing"
    else:
        names = pd.read_csv(C.PRE / "bus_lsoa_meta.csv", dtype={"lsoa": str}).set_index("lsoa")
        name_col, ecol, ncol = "rep_stop", None, None
    return X, meta, names, dirs, name_col, ecol, ncol, mod


def total_profile(X, meta, dirs):
    """Reconstruct each unit's TRUE total temporal share over bins."""
    bins = sorted({minute_of(c) for c in X.columns})
    tot = np.zeros((len(X), len(bins)))
    for j, b in enumerate(bins):
        for d in dirs:
            col = f"{d}_{b}"
            if col in X.columns:
                tot[:, j] += X[col].values * meta[f"tot_{d}"].reindex(X.index).fillna(0).values
    denom = tot.sum(1, keepdims=True); denom[denom == 0] = 1
    return pd.DataFrame(tot / denom, index=X.index, columns=bins), np.array(bins)


def main():
    big = []
    for ds, K in JOBS.items():
        X, meta, names, dirs, name_col, ecol, ncol, mod = load(ds)
        lab = pd.read_csv(C.LAB / f"{ds}_k{K}_labels.csv", dtype={"unit": str}).set_index("unit")
        lab = lab.reindex(X.index)
        prof, bins = total_profile(X, meta, dirs)
        din, dout = dirs  # in (entry/boardings), out (exit/alightings)
        net = (meta[f"tot_{din}"] - meta[f"tot_{dout}"]) / (meta[f"tot_{din}"] + meta[f"tot_{dout}"]).replace(0, np.nan)
        ev = prof.loc[:, (bins >= EV[0]) & (bins < EV[1])].sum(1)
        late = prof.loc[:, bins >= LATE].sum(1)
        hump = prof.loc[:, (bins >= HUMP[0]) & (bins < HUMP[1])].sum(1)
        tmed = bins[(np.cumsum(prof.values, 1) >= 0.5).argmax(1)]

        rows, reps = [], []
        total_vol = meta["total_activity"].reindex(X.index)
        for cl in sorted(lab["cluster"].dropna().unique()):
            m = lab["cluster"] == cl
            idx = X.index[m.values]
            top = total_vol.loc[idx].sort_values(ascending=False).head(5).index
            topnames = [str(names[name_col].get(u, u)) for u in top]
            rows.append({
                "dataset": ds, "K": K, "cluster": int(cl), "n": int(m.sum()),
                "pct_units": round(100 * m.sum() / len(lab), 1),
                "vol_mean": round(float(total_vol[m.values].mean()), 1),
                "net_dir": round(float(net[m.values].mean()), 3),
                "t_median": hhmm(int(np.median(tmed[m.values]))),
                "evening_18_20": round(float(ev[m.values].mean()), 3),
                "late_00plus": round(float(late[m.values].mean()), 3),
                "hump_22_23": round(float(hump[m.values].mean()), 3),
                "max_post": round(float(lab.loc[m.values, "max_posterior"].mean()), 2),
                "entropy": round(float(lab.loc[m.values, "entropy"].mean()), 2),
                "rep_units": " | ".join(topnames),
            })
            reps.append({"dataset": ds, "cluster": int(cl), "rep_units": "; ".join(topnames)})
        sig = pd.DataFrame(rows)
        sig.to_csv(INTERP / f"{ds}_k{K}_signature.csv", index=False)
        big.append(sig)
        print(f"\n===== {ds} (K={K}, cov={'tied' if mod=='rail' else 'full'}) =====")
        print(sig[["cluster", "n", "pct_units", "vol_mean", "net_dir", "t_median",
                   "evening_18_20", "late_00plus", "hump_22_23"]].to_string(index=False))
        for _, r in sig.iterrows():
            print(f"  C{r['cluster']}: {r['rep_units']}")
    pd.concat(big, ignore_index=True).to_csv(INTERP / "all_signatures.csv", index=False)
    print("\nsaved -> outputs/interpretation/")


if __name__ == "__main__":
    main()
