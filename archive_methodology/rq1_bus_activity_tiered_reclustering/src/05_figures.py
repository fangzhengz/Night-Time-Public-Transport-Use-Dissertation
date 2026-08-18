"""Figures for the reliable-core K=3 bus reclustering, matching the exact
plotting conventions already used by the adopted pipeline
(`cluster_clean_version_fullweek/src/05_figures.py`): per-cluster temporal
profile curves (median + 10-90th percentile band, day-by-day) and an LSOA
choropleth map. Also adds a coverage-tier map (all 4,994 London LSOAs),
which has no equivalent in the adopted pipeline since that concept is new
here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

sys.path.insert(0, str(FYP / "cluster_clean_version_fullweek" / "src"))
import config as C  # noqa: E402  (reuse GREEN/RED/PURPLE, LSOA_GEOJSON, CRS_BNG, BUS_DAYS, BUS_DIRECTIONS)

X_BUS = FYP / "cluster_clean_version_fullweek" / "outputs" / "features" / "X_bus.parquet"
LABELS = ROOT / "outputs" / "labels"
DATA = ROOT / "outputs" / "data"
FIG = ROOT / "outputs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

K = 3  # the adopted reliable-core K, per 03_recluster_reliable_core.py's bootstrap result


def tlabel(m: int) -> str:
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def parse_cols(cols, day_order) -> pd.DataFrame:
    recs = []
    for c in cols:
        direction, day, mins = c.rsplit("_", 2)
        recs.append((c, direction, day, int(mins)))
    df = pd.DataFrame(recs, columns=["col", "direction", "day", "minute"])
    df["order"] = df["day"].map({d: i for i, d in enumerate(day_order)})
    return df.sort_values(["direction", "order", "minute"]).reset_index(drop=True)


def plot_profiles(X: pd.DataFrame, cmap: pd.DataFrame, lab: np.ndarray, dirs, day_order) -> None:
    cls = sorted(pd.unique(lab))
    fig, axs = plt.subplots(len(cls), 1, figsize=(11, max(1.8 * len(cls), 4)), squeeze=False, sharey=True)
    sel0 = cmap[cmap.direction == dirs[0]].reset_index(drop=True)
    boundaries, ticks, labels = [], [], []
    for day in day_order:
        idx = sel0.index[sel0.day == day]
        if not len(idx):
            continue
        ticks.append(int(np.mean(idx)))
        labels.append(f"{day}\n{tlabel(sel0.loc[idx[0], 'minute'])}-{tlabel(sel0.loc[idx[-1], 'minute'])}")
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
        a.grid(axis="y", color="#eee", lw=.5)
        a.spines[["top", "right"]].set_visible(False)
        a.set_xticks(ticks)
        a.set_xticklabels(labels, fontsize=7)
    axs[0, 0].legend(fontsize=8, loc="upper right")
    fig.suptitle(f"bus reliable-core (activity>=450, day-by-day) K={K} — cluster profiles (share over the week)", y=1.0)
    fig.tight_layout()
    fig.savefig(FIG / f"reliable_core_k{K}_profiles.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cluster_map(lab_df: pd.DataFrame, base: gpd.GeoDataFrame, code_col: str) -> None:
    df = lab_df.rename(columns={"unit": code_col})
    g = base.merge(df, on=code_col, how="left")
    cls = sorted(df.cluster.dropna().unique())
    cm = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    # LSOAs outside the reliable core (excluded or below threshold) shown grey, same convention as the adopted pipeline
    g[g.cluster.isna()].plot(ax=ax, color="#efefef", edgecolor="#e2e2e2", linewidth=0.1)
    handles = []
    for i, cl in enumerate(cls):
        g[g.cluster == cl].plot(ax=ax, color=cm(i), edgecolor="white", linewidth=0.05)
        handles.append(mpatches.Patch(color=cm(i), label=f"C{int(cl)} (n={(df.cluster == cl).sum()})"))
    handles.append(mpatches.Patch(color="#efefef", label="below reliable threshold / no data"))
    ax.set_title(f"bus reliable-core (activity>=450) K={K} — LSOA clusters\n"
                 f"(grey = below threshold, reported descriptively, not shape-clustered)")
    ax.legend(handles=handles, loc="lower right", fontsize=9)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(FIG / f"reliable_core_k{K}_map.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_coverage_tier_map(base: gpd.GeoDataFrame, code_col: str) -> None:
    tiers = pd.read_csv(DATA / "lsoa_coverage_tiers.csv")
    tiers["lsoa"] = tiers["lsoa"].astype(str)
    g = base.merge(tiers, left_on=code_col, right_on="lsoa", how="left")
    tier_colors = {
        "0_no_recorded_activity": "#d9d9d9",
        "1_matched_stop_no_activity": "#a6a6a6",
        "2_below_reliable_threshold": "#f2b134",
        "3_reliable_core": C.GREEN,
    }
    fig, ax = plt.subplots(figsize=(10, 10))
    handles = []
    for tier, color in tier_colors.items():
        sub = g[g.tier == tier]
        sub.plot(ax=ax, color=color, edgecolor="white", linewidth=0.05)
        handles.append(mpatches.Patch(color=color, label=f"{tier} (n={len(sub)})"))
    ax.set_title("Bus LSOA coverage tiers — all 4,994 Greater London LSOAs\n"
                 "(labels describe OBSERVED BUSTO activity, not service provision)")
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(FIG / "coverage_tiers_map.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    base = gpd.read_file(C.LSOA_GEOJSON).to_crs(C.CRS_BNG)
    code_col = next(c for c in base.columns if c.lower() == "lsoa21cd")

    X = pd.read_parquet(X_BUS)
    X.index = X.index.astype(str)
    cmap = parse_cols(X.columns, C.BUS_DAYS)

    lab_df = pd.read_csv(LABELS / f"reliable_core_k{K}_labels.csv")
    lab_df["unit"] = lab_df["unit"].astype(str)
    lab_lookup = lab_df.set_index("unit")["cluster"]
    # Profile plot only over the reliable-core units actually clustered
    core_idx = X.index.intersection(lab_lookup.index)
    lab = lab_lookup.loc[core_idx].values
    plot_profiles(X.loc[core_idx], cmap, lab, C.BUS_DIRECTIONS, C.BUS_DAYS)

    plot_cluster_map(lab_df, base, code_col)
    plot_coverage_tier_map(base, code_col)
    print("figures done:", [p.name for p in FIG.glob("*.png")])


if __name__ == "__main__":
    main()
