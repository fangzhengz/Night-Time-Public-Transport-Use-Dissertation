# -*- coding: utf-8 -*-
"""05 · Figures (FULL-WEEK) — per modality (rail, bus), uniform style.

For each of rail / bus:
  - BIC grid (BIC vs K, one line per covariance);
  - K-diagnostics 2x3 panel (silhouette, CH, DB, BIC, bootstrap ARI);
  - per candidate K: cluster profiles (rows = clusters; the whole-week vector
    plotted as weekday block then weekend block, separated by a divider) and a
    spatial map (rail = station points, bus = LSOA choropleth).

Column layout is "{direction}_{block}_{minute}" with block in {wd, we}; the
profile x-axis follows BLOCK_ORDER so the weekday-vs-weekend split is visible.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

def tlabel(m):
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def parse_cols(cols, day_order):
    recs = []
    for c in cols:
        direction, day, mins = c.rsplit("_", 2)
        recs.append((c, direction, day, int(mins)))
    df = pd.DataFrame(recs, columns=["col", "direction", "day", "minute"])
    df["order"] = df["day"].map({d: i for i, d in enumerate(day_order)})
    return df.sort_values(["direction", "order", "minute"]).reset_index(drop=True)


def plot_bic_grid(ds):
    grid = pd.read_csv(C.DIAG / f"{ds}_bic_grid.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for cov, mk in zip(C.COVARIANCES, ["o", "s", "^", "D"]):
        sub = grid[grid.covariance == cov]
        ax.plot(sub.K, sub.BIC, "-" + mk, label=cov)
    ax.set_xlabel("K"); ax.set_ylabel("BIC (lower=better)")
    ax.set_title(f"{ds} (full week) — GMM BIC by covariance × K")
    ax.legend(fontsize=8); ax.grid(color="#eee"); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(C.FIG / f"{ds}_bic_grid.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_kdiag(ds):
    d = pd.read_csv(C.DIAG / f"{ds}_kdiag.csv")
    fig, ax = plt.subplots(2, 3, figsize=(14, 8)); K = d.K
    panels = [("silhouette", "Silhouette (higher=better)", C.PURPLE),
              ("calinski_harabasz", "Calinski-Harabasz (higher=better)", C.GREEN),
              ("davies_bouldin", "Davies-Bouldin (lower=better)", C.RED),
              ("BIC", "BIC (lower=better)", C.PURPLE)]
    for a, (col, title, color) in zip(ax.flat[:4], panels):
        a.plot(K, d[col], "-o", color=color); a.set_title(title)
    a = ax.flat[4]; a.errorbar(K, d.ARI, yerr=d.ARI_sd, fmt="-o", color=C.PURPLE, capsize=3)
    a.set_title("Bootstrap stability ARI (higher=better)"); a.set_ylim(0, 1.02)
    ax.flat[5].axis("off")
    for a in ax.flat:
        if a.has_data():
            a.set_xlabel("K"); a.set_xticks(list(C.K_RANGE)); a.grid(color="#eee")
            a.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"{ds} (full week) — K-diagnostics (BtC raw-share, GMM)", fontsize=14, y=1.0)
    fig.tight_layout(); fig.savefig(C.FIG / f"{ds}_kdiag.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_profiles(ds, X, cmap, lab, dirs, K, day_order):
    cls = sorted(pd.unique(lab))
    fig, axs = plt.subplots(len(cls), 1, figsize=(11, max(1.8 * len(cls), 4)), squeeze=False, sharey=True)
    sel0 = cmap[cmap.direction == dirs[0]].reset_index(drop=True)   # x layout (per direction)
    # day boundaries + tick positions/labels from the reference direction
    boundaries, ticks, labels = [], [], []
    start = 0
    for day in day_order:
        idx = sel0.index[sel0.day == day]
        if not len(idx):
            continue
        ticks.append(int(np.mean(idx)))
        labels.append(f"{day}\n{tlabel(sel0.loc[idx[0],'minute'])}-{tlabel(sel0.loc[idx[-1],'minute'])}")
        boundaries.append(int(idx[-1]) + 0.5)
    for a, cl in zip(axs[:, 0], cls):
        m = lab == cl
        for direction, color in zip(dirs, [C.GREEN, C.RED]):
            sel = cmap[cmap.direction == direction].reset_index(drop=True)
            x = np.arange(len(sel))
            sub = X.loc[m, sel.col.tolist()]
            a.plot(x, sub.median(0).values, color=color, lw=1.2, marker="o", ms=1.6, label=direction)
            a.fill_between(x, sub.quantile(.1).values, sub.quantile(.9).values, color=color, alpha=.12, lw=0)
        for b in boundaries[:-1]:
            a.axvline(b, color="#bbb", lw=0.7, ls="--")
        a.set_title(f"C{cl} (n={int(m.sum())})", fontsize=9)
        a.grid(axis="y", color="#eee", lw=.5); a.spines[["top", "right"]].set_visible(False)
        a.set_xticks(ticks); a.set_xticklabels(labels, fontsize=7)
    axs[0, 0].legend(fontsize=8, loc="upper right")
    fig.suptitle(f"{ds} (full week, day-by-day) K={K} — cluster profiles (share over the week)", y=1.0)
    fig.tight_layout(); fig.savefig(C.FIG / f"{ds}_k{K}_profiles.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def rail_map(ds, lab_df, K, base):
    coords = pd.read_csv(C.RAIL_COORDS, dtype={"NLC": str}).set_index("NLC")
    df = lab_df.set_index("unit").join(coords[["easting", "northing"]]).dropna(subset=["easting"])
    cls = sorted(df.cluster.unique()); cm = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
    for i, cl in enumerate(cls):
        s = df[df.cluster == cl]
        ax.scatter(s.easting, s.northing, s=42, color=cm(i), edgecolor="white", linewidth=0.6,
                   label=f"C{cl} (n={len(s)})", zorder=3)
    ax.set_title(f"{ds} (full week) K={K} — station clusters"); ax.legend(loc="lower right", fontsize=9)
    ax.set_axis_off()
    minx, miny, maxx, maxy = df.easting.min(), df.northing.min(), df.easting.max(), df.northing.max()
    ax.set_xlim(minx - 3000, maxx + 3000); ax.set_ylim(miny - 3000, maxy + 3000)
    fig.tight_layout(); fig.savefig(C.FIG / f"{ds}_k{K}_map.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def bus_map(ds, lab_df, K, base, code_col):
    df = lab_df.rename(columns={"unit": code_col})
    g = base.merge(df, on=code_col, how="left")
    cls = sorted(df.cluster.unique()); cm = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    g[g.cluster.isna()].plot(ax=ax, color="#efefef", edgecolor="#e2e2e2", linewidth=0.1)
    handles = []
    for i, cl in enumerate(cls):
        g[g.cluster == cl].plot(ax=ax, color=cm(i), edgecolor="white", linewidth=0.05)
        handles.append(mpatches.Patch(color=cm(i), label=f"C{cl} (n={(df.cluster == cl).sum()})"))
    ax.set_title(f"{ds} (full week) K={K} — LSOA clusters")
    ax.legend(handles=handles, loc="lower right", fontsize=9); ax.set_axis_off()
    fig.tight_layout(); fig.savefig(C.FIG / f"{ds}_k{K}_map.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    base = gpd.read_file(C.LSOA_GEOJSON).to_crs(C.CRS_BNG)
    code_col = next(c for c in base.columns if c.lower() == "lsoa21cd")
    for mod in ["rail", "bus"]:
        ds = mod
        dirs = C.RAIL_DIRECTIONS if mod == "rail" else C.BUS_DIRECTIONS
        day_order = C.RAIL_DAYS if mod == "rail" else C.BUS_DAYS
        plot_bic_grid(ds); plot_kdiag(ds)
        X = pd.read_parquet(C.FEAT / f"X_{ds}.parquet"); X.index = X.index.astype(str)
        cmap = parse_cols(X.columns, day_order)
        for K in C.CAND_K:
            lab_df = pd.read_csv(C.LAB / f"{ds}_k{K}_labels.csv"); lab_df["unit"] = lab_df["unit"].astype(str)
            lab = lab_df.set_index("unit").loc[X.index, "cluster"].values
            plot_profiles(ds, X, cmap, lab, dirs, K, day_order)
            if mod == "rail":
                rail_map(ds, lab_df, K, base)
            else:
                bus_map(ds, lab_df, K, base, code_col)
        print(f"{ds}: figures done")
    print("done")


if __name__ == "__main__":
    main()
