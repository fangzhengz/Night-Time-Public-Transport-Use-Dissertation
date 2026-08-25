from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

"""06 - Temporal usage-profile charts + spatial cluster maps for the
all-modes rail clustering.

Reuses the exact plotting logic from
`FYP/analysis/02_mode_specific_clustering/rail/src/05_figures.py`
(`plot_bic_grid`, `plot_kdiag`, `plot_profiles`, `rail_map`), so the figures
are visually and methodologically consistent with the canonical rail_k5
figures already used in the dissertation. The only additions: the map
distinguishes the original 270 Underground stations from the 201 added
non-LU stations (triangle markers), and profiles/maps are produced for
K=5 (direct comparison point with canonical), K=6 and K=7 (the closely-tied
BIC pair identified for the all-modes data -- see rail_allmodes_bic_best.txt).
"""

FYP_ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = Path(os.environ.get("CASA_FYP_SOURCE_ROOT", FYP_ROOT / "authorised_data")).expanduser().resolve()
DATA_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
FIG_DIR = Path(__file__).resolve().parents[1] / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Coordinate matching now lives in data_processing/rail_allmodes/ (moved 2026-07-24).
COORDS_PATH = FYP_ROOT / "analysis" / "01_data_preparation" / "rail" / "outputs" / "data" / "rail_allmodes_coords.csv"
LSOA_GEOJSON = SOURCE_ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"
# Same source the RQ2 results panel (analysis/04_urban_context/src/
# 06_build_cluster_panels.py::rail_profiles) reads. Profiles here are now
# computed the same way -- share recomputed from this raw long table and
# averaged with the cluster MEAN -- rather than read back off the clustering's
# own X matrix with a median, so this diagnostic figure and the adopted
# results figure show the same curve for the same cluster.
RAW_LONG = (
    FYP_ROOT / "analysis" / "01_data_preparation" / "rail" / "outputs" / "preprocessed"
    / "numbat_allmodes_station_qhr_all_daytypes_final.parquet"
)

RAIL_DAYS = ["MON", "TWT", "FRI", "SAT", "SUN"]
RAIL_DIRECTIONS = ["entry", "exit"]
COVARIANCES = ["diag", "full"]
K_RANGE = list(range(2, 13))
PLOT_K = [5, 6, 7]

PURPLE, GREEN, RED = "#500778", "#2F6B4F", "#9A3D3D"
PROFILE_COLORS = {"entry": GREEN, "exit": RED}
DAY_LABELS = {"MON": "Monday", "TWT": "Tue-Thu", "FRI": "Friday", "SAT": "Saturday", "SUN": "Sunday"}


def tlabel(m: int) -> str:
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def plot_bic_grid():
    grid = pd.read_csv(DATA_DIR / "rail_allmodes_bic_grid.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for cov, mk in zip(COVARIANCES, ["o", "s"]):
        sub = grid[grid.covariance == cov]
        ax.plot(sub.K, sub.BIC, "-" + mk, label=cov)
    ax.set_xlabel("K")
    ax.set_ylabel("BIC (lower=better)")
    ax.set_title("rail all-modes (full week) — GMM BIC by covariance x K")
    ax.legend(fontsize=8)
    ax.grid(color="#eee")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "rail_allmodes_bic_grid.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_kdiag():
    d = pd.read_csv(DATA_DIR / "rail_allmodes_kdiag.csv")
    fig, ax = plt.subplots(2, 3, figsize=(14, 8))
    K = d.K
    panels = [
        ("silhouette", "Silhouette (higher=better)", PURPLE),
        ("calinski_harabasz", "Calinski-Harabasz (higher=better)", GREEN),
        ("davies_bouldin", "Davies-Bouldin (lower=better)", RED),
        ("BIC", "BIC (lower=better)", PURPLE),
    ]
    for a, (col, title, color) in zip(ax.flat[:4], panels):
        a.plot(K, d[col], "-o", color=color)
        a.set_title(title)
    a = ax.flat[4]
    a.errorbar(K, d.ARI, yerr=d.ARI_sd, fmt="-o", color=PURPLE, capsize=3)
    a.set_title("Bootstrap stability ARI (higher=better)")
    a.set_ylim(0, 1.02)
    ax.flat[5].axis("off")
    for a in ax.flat:
        if a.has_data():
            a.set_xlabel("K")
            a.set_xticks(K_RANGE)
            a.grid(color="#eee")
            a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("rail all-modes (full week) — K-diagnostics (diag GMM)", fontsize=14, y=1.0)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "rail_allmodes_kdiag.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def build_hourly_shares(lab_df: pd.DataFrame) -> pd.DataFrame:
    """Mean hourly share per cluster x day x direction, normalised over the week.

    Mirrors analysis/04_urban_context/src/06_build_cluster_panels.py::
    profile_from_long exactly (share = count / that station's own week-long
    total for that direction, then cluster MEAN), just recomputed from the raw
    long table instead of read off the clustering's X matrix. This is so the
    diagnostic figure here and the adopted RQ2 results figure show the same
    curve for the same cluster.
    """
    long = pd.read_parquet(RAW_LONG)
    long["NLC"] = long["NLC"].astype(str).str.strip()
    windows = {day: (18 * 60, 29 * 60) for day in RAIL_DAYS}  # uniform 18:00-05:00
    keep = np.zeros(len(long), dtype=bool)
    for day, (start, end) in windows.items():
        keep |= (long["day_type"] == day) & long["extended_minute"].between(start, end - 1)
    long = long.loc[keep].copy()
    long["hour_bin"] = (long["extended_minute"] // 60) * 60

    frame = long.groupby(["NLC", "day_type", "direction", "hour_bin"], observed=True)["count"].sum().reset_index()
    week_total = frame.groupby(["NLC", "direction"], observed=True)["count"].transform("sum")
    frame["share"] = frame["count"] / week_total.replace(0, np.nan)

    labels = lab_df.rename(columns={"unit": "NLC"})[["NLC", "cluster"]].copy()
    labels["NLC"] = labels["NLC"].astype(str).str.strip()
    frame = frame.merge(labels, on="NLC", how="inner")
    return (
        frame.groupby(["cluster", "day_type", "direction", "hour_bin"], observed=True)["share"]
        .mean()
        .reset_index()
    )


def plot_profiles(profiles: pd.DataFrame, lab_df: pd.DataFrame, K, n_stations):
    counts = lab_df.groupby("cluster")["unit"].count()
    cls = sorted(profiles["cluster"].unique())
    fig, axs = plt.subplots(
        len(cls), len(RAIL_DAYS),
        figsize=(3.7 * len(RAIL_DAYS), max(2.2 * len(cls), 5.5)),
        sharey=True,
        squeeze=False,
    )
    hour_bins = sorted(profiles["hour_bin"].unique())
    ymax = profiles["share"].max() * 1.08

    for row, cl in enumerate(cls):
        for col, day in enumerate(RAIL_DAYS):
            a = axs[row, col]
            for direction in RAIL_DIRECTIONS:
                piece = profiles[
                    (profiles.cluster == cl) & (profiles.day_type == day) & (profiles.direction == direction)
                ].sort_values("hour_bin")
                a.plot(
                    piece["hour_bin"].to_numpy(),
                    piece["share"].to_numpy(),
                    color=PROFILE_COLORS[direction],
                    lw=1.8,
                    marker="o",
                    ms=3.2,
                    label="entries" if direction == "entry" else "exits",
                )

            if row == 0:
                a.set_title(DAY_LABELS[day], fontsize=11, pad=6)
            if col == 0:
                a.set_ylabel(f"C{cl} (n={int(counts.get(cl, 0))})", fontsize=10)
            if row == len(cls) - 1:
                tick_minutes = np.arange(18 * 60, hour_bins[-1] + 1, 2 * 60)
                a.set_xticks(tick_minutes)
                a.set_xticklabels([tlabel(t) for t in tick_minutes], rotation=35, ha="right")
            else:
                a.tick_params(labelbottom=False)

            a.set_ylim(0, ymax)
            a.grid(True, color="#d9d9d9", alpha=0.38, lw=0.7)
            a.spines[["top", "right"]].set_visible(False)

    handles, labels = axs[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(0.992, 0.955), frameon=False, fontsize=9)
    fig.suptitle(
        f"Rail all-modes clusters ({n_stations} stations), K={K}\n"
        "profiles shown as mean station shares over the full week, aggregated hourly",
        fontsize=14,
        y=0.995,
    )
    fig.supxlabel("Time of day", y=0.02, fontsize=10)
    fig.supylabel("Mean hourly share of each direction's weekly activity", x=0.002, fontsize=10)
    fig.subplots_adjust(left=0.065, right=0.98, top=0.89, bottom=0.08, wspace=0.10, hspace=0.22)
    fig.savefig(FIG_DIR / f"rail_allmodes_k{K}_profiles.png", dpi=150, bbox_inches="tight")
    fig.savefig(FIG_DIR / f"rail_allmodes_k{K}_profiles.pdf", bbox_inches="tight")
    plt.close(fig)


def rail_map(lab_df, coords, K, base):
    # The LU vs added-non-LU marker split (circle vs triangle) dated from when
    # this was a comparison point against the LU-only canonical clustering.
    # Now that the all-modes population is the analysis itself rather than a
    # specification check against it, that distinction no longer describes
    # anything the reader needs -- every station is just a station.
    df = lab_df.set_index("unit").join(coords.set_index("unit")[["easting", "northing"]]).dropna(
        subset=["easting"]
    )
    cls = sorted(df.cluster.unique())
    cm = matplotlib.colormaps["tab10"].resampled(max(len(cls), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
    for i, cl in enumerate(cls):
        s = df[df.cluster == cl]
        ax.scatter(
            s.easting, s.northing, s=42, marker="o", color=cm(i),
            edgecolor="white", linewidth=0.6, label=f"C{cl} (n={len(s)})", zorder=3,
        )
    ax.set_title(f"rail all-modes ({len(df)} stations) K={K} — station clusters")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_axis_off()
    minx, miny, maxx, maxy = df.easting.min(), df.northing.min(), df.easting.max(), df.northing.max()
    ax.set_xlim(minx - 3000, maxx + 3000)
    ax.set_ylim(miny - 3000, maxy + 3000)
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"rail_allmodes_k{K}_map.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    plot_bic_grid()
    plot_kdiag()

    coords = pd.read_csv(COORDS_PATH, dtype={"unit": str})
    base = gpd.read_file(LSOA_GEOJSON).to_crs("EPSG:27700")

    for K in PLOT_K:
        lab_df = pd.read_csv(DATA_DIR / f"rail_allmodes_k{K}_labels.csv")
        lab_df["unit"] = lab_df["unit"].astype(str)
        profiles = build_hourly_shares(lab_df)
        plot_profiles(profiles, lab_df, K, len(lab_df))
        rail_map(lab_df, coords, K, base)
        print(f"K={K}: profile + map done")

    print("done")


if __name__ == "__main__":
    main()
