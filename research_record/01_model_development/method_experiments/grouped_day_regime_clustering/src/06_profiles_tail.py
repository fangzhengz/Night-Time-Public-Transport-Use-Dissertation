# -*- coding: utf-8 -*-
"""06 · Tail-visible cluster profiles (rail + bus, all candidate K).

The standard profile plots (step 05) share a y-axis dominated by the evening
peak, so the small overnight share (1-4% of the night) is squashed flat and the
Night-Tube / dawn tail is invisible — even though the clustering uses it.

This produces a 2-column variant per cluster:
  left  = full night window (linear; shows the evening structure)
  right = 00:00 onward, ZOOMED to the overnight magnitude (own shared y-axis;
          shows the Night-Tube / dawn tail that the left panel hides)
Output: figures/{ds}_k{K}_profiles_tail.png  (does not overwrite step-05 plots)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

ZOOM_START = 24 * 60  # 00:00 in extended minutes


def tlabel(m):
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def parse_cols(cols):
    recs = [(c, c.rsplit("_", 1)[0], int(c.rsplit("_", 1)[1])) for c in cols]
    return pd.DataFrame(recs, columns=["col", "direction", "minute"])


def make(ds, dirs):
    X = pd.read_parquet(C.FEAT / f"X_{ds}.parquet"); X.index = X.index.astype(str)
    cmap = parse_cols(X.columns)
    for K in C.CAND_K:
        lab_df = pd.read_csv(C.LAB / f"{ds}_k{K}_labels.csv", dtype={"unit": str}).set_index("unit")
        lab = lab_df.loc[X.index, "cluster"].values
        cls = sorted(pd.unique(lab))

        # shared zoom y-limit: 95th pct of overnight values across all clusters
        zsel = cmap[cmap.minute >= ZOOM_START]
        zmax = float(np.nanpercentile(X[zsel.col].values, 99)) * 1.15 if len(zsel) else 0.02
        zmax = max(zmax, 1e-3)

        fig, axs = plt.subplots(len(cls), 2, figsize=(11, max(1.7 * len(cls), 4)),
                                squeeze=False, gridspec_kw={"width_ratios": [2, 1]})
        for ri, cl in enumerate(cls):
            m = lab == cl
            for ci, (lo, hi, ylim, tag) in enumerate(
                    [(0, 10 ** 9, None, "full night"), (ZOOM_START, 10 ** 9, zmax, "00:00 onward (zoom)")]):
                a = axs[ri][ci]
                for direction, color in zip(dirs, [C.GREEN, C.RED]):
                    sel = cmap[(cmap.direction == direction) & (cmap.minute >= lo) & (cmap.minute < hi)].sort_values("minute")
                    t = sel.minute.values
                    sub = X.loc[m, sel.col.tolist()]
                    a.plot(t, sub.median(0).values, color=color, lw=1.4, marker="o", ms=2.5, label=direction)
                    a.fill_between(t, sub.quantile(.1).values, sub.quantile(.9).values, color=color, alpha=.12, lw=0)
                if ylim:
                    a.set_ylim(0, ylim)
                if ri == 0:
                    a.set_title(tag, fontsize=9)
                if ci == 0:
                    a.set_ylabel(f"C{cl}\n(n={int(m.sum())})", fontsize=8)
                tk = [t[0], t[len(t) // 2], t[-1]]
                a.set_xticks(tk); a.set_xticklabels([tlabel(x) for x in tk], fontsize=7)
                a.grid(axis="y", color="#eee", lw=.5); a.spines[["top", "right"]].set_visible(False)
        axs[0][0].legend(fontsize=7, loc="upper right")
        fig.suptitle(f"{ds} K={K} — profiles with overnight zoom (right column auto-scaled)", y=1.0)
        fig.tight_layout(); fig.savefig(C.FIG / f"{ds}_k{K}_profiles_tail.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    print(f"{ds}: tail-visible profiles done")


def main():
    for grp in C.RAIL_GROUPS:
        make(f"rail_{grp}", C.RAIL_DIRECTIONS)
    for grp in C.BUS_GROUPS:
        make(f"bus_{grp}", C.BUS_DIRECTIONS)
    print("done")


if __name__ == "__main__":
    main()
