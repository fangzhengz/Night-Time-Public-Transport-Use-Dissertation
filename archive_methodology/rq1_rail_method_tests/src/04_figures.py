# -*- coding: utf-8 -*-
"""Station maps, day-by-day profiles and a naming table for one rail variant.

House style is copied from `numbat_all_area_test/src/06_profiles_and_maps_
allmodes.py` -- tab10 palette, LU circles vs added non-LU triangles, median
with 10-90 band, dashed day boundaries -- so these sit next to the rail figures
Clara has already seen rather than introducing a second visual language.

ONE READING TRAP, made explicit in every caption: under day-type closure each
day block sums to 1 over its OWN bins, and the blocks are not the same length
(MON/TWT/SUN 28 bins, FRI/SAT 44). A Monday bin therefore averages 1/28 = 3.6%
while a Friday bin averages 1/44 = 2.3%, so MON/TWT/SUN sit visibly higher.
That step at the day boundary is an artefact of the window, NOT more travel on
Mondays. Under the adopted full-week closure the same figure would show real
between-day magnitude, which is exactly the information this closure removes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

GREEN, RED = "#2F6B4F", "#9A3D3D"
DEFAULT_KS = [5, 6, 7, 8, 9]
LSOA_GEOJSON = C.FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
CENTRE = (530034.0, 180381.0)  # Charing Cross, BNG


def tlabel(minute: int) -> str:
    return f"{(minute // 60) % 24:02d}:{minute % 60:02d}"


def parse_columns(columns) -> pd.DataFrame:
    rows = []
    for column in columns:
        direction, day, minute = column.rsplit("_", 2)
        rows.append(
            {"col": column, "direction": direction, "day": day, "minute": int(minute)}
        )
    return pd.DataFrame(rows)


def profile_caption(variant: str) -> str:
    """The y-axis means different things per cell of the 2x2 -- say which."""
    spec = C.VARIANTS[variant]
    if spec["closure"] == "daytype":
        note = (
            "EACH DAY BLOCK SUMS TO 1 OVER ITS OWN BINS, so a step at a day "
            "boundary is the window length, not more travel"
        )
        if not spec["padded"]:
            note += " (MON/TWT/SUN 28 bins vs FRI/SAT 44)"
    else:
        note = (
            "each DIRECTION sums to 1 over the WHOLE WEEK, so between-day height "
            "differences are real differences in how the week's travel is distributed"
        )
    window = (
        "all day types padded to 18:00-05:00"
        if spec["padded"]
        else "native windows (MON/TWT/SUN to 01:00, FRI/SAT to 05:00)"
    )
    closure = "day-type closure" if spec["closure"] == "daytype" else "full-week closure"
    return f"{closure}, {window}\nmedian with 10-90 band; {note}"


def plot_profiles(X, colmap, labels, k, out: Path, variant: str) -> None:
    clusters = sorted(pd.unique(labels))
    fig, axes = plt.subplots(
        len(clusters), 1, figsize=(11.5, max(1.9 * len(clusters), 4)),
        squeeze=False, sharey=True,
    )
    reference = colmap[colmap.direction == C.RAIL_DIRECTIONS[0]].reset_index(drop=True)
    boundaries, ticks, tick_labels = [], [], []
    for day in C.RAIL_DAYS:
        index = reference.index[reference.day == day]
        if not len(index):
            continue
        ticks.append(int(np.mean(index)))
        tick_labels.append(
            f"{day}\n{tlabel(reference.loc[index[0], 'minute'])}-"
            f"{tlabel(reference.loc[index[-1], 'minute'])}\n({len(index)} bins)"
        )
        boundaries.append(int(index[-1]) + 0.5)
    for axis, cluster in zip(axes[:, 0], clusters):
        mask = labels == cluster
        for direction, colour in zip(C.RAIL_DIRECTIONS, [GREEN, RED]):
            selection = colmap[colmap.direction == direction].reset_index(drop=True)
            x = np.arange(len(selection))
            sub = X.loc[mask, selection.col.tolist()]
            axis.plot(x, sub.median(0).values, color=colour, lw=1.2,
                      marker="o", ms=1.6, label=direction)
            axis.fill_between(x, sub.quantile(0.1).values, sub.quantile(0.9).values,
                              color=colour, alpha=0.12, lw=0)
        for boundary in boundaries[:-1]:
            axis.axvline(boundary, color="#bbb", lw=0.7, ls="--")
        axis.set_title(f"C{cluster} (n={int(mask.sum())})", fontsize=9)
        axis.grid(axis="y", color="#eee", lw=0.5)
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_xticks(ticks)
        axis.set_xticklabels(tick_labels, fontsize=7)
    axes[0, 0].legend(fontsize=8, loc="upper right")
    fig.suptitle(
        f"rail all-modes, K={k} — cluster profiles\n{profile_caption(variant)}",
        y=1.0, fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(out / f"profiles_k{k}.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / f"profiles_k{k}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_map(frame, k, base, out: Path, variant: str) -> None:
    clusters = sorted(frame.cluster.unique())
    palette = matplotlib.colormaps["tab10"].resampled(max(len(clusters), 3))
    fig, ax = plt.subplots(figsize=(10, 10))
    base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
    for index, cluster in enumerate(clusters):
        subset = frame[frame.cluster == cluster]
        lu = subset[subset["is_lu"]]
        other = subset[~subset["is_lu"]]
        ax.scatter(lu.easting, lu.northing, s=42, marker="o", color=palette(index),
                   edgecolor="white", linewidth=0.6,
                   label=f"C{cluster} (n={len(subset)})", zorder=3)
        if len(other):
            ax.scatter(other.easting, other.northing, s=52, marker="^",
                       color=palette(index), edgecolor="black", linewidth=0.5, zorder=4)
    ax.scatter([], [], marker="^", color="grey", edgecolor="black",
               label="added non-LU station")
    ax.set_title(
        f"rail all-modes ({len(frame)} stations), K={k}\n"
        + profile_caption(variant).split("\n")[0]
    )
    ax.legend(loc="lower right", fontsize=9)
    ax.set_axis_off()
    ax.set_xlim(frame.easting.min() - 3000, frame.easting.max() + 3000)
    ax.set_ylim(frame.northing.min() - 3000, frame.northing.max() + 3000)
    fig.tight_layout()
    fig.savefig(out / f"map_k{k}.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / f"map_k{k}.pdf", bbox_inches="tight")
    plt.close(fig)


def naming_table(frame, metrics, k) -> pd.DataFrame:
    rows = []
    for cluster in sorted(frame.cluster.unique()):
        members = frame.index[frame.cluster == cluster]
        sub = metrics.loc[members]
        modes = frame.loc[members, "mode_label"].value_counts()
        rows.append(
            {
                "cluster": f"C{cluster}",
                "n": len(members),
                "share_%": 100 * len(members) / len(frame),
                "median_total_activity": float(sub["total_activity"].median()),
                "direction_balance": float(sub["direction_balance"].mean()),
                "midnight_share": float(sub["midnight_share_common_window"].mean()),
                "night_tube_ext": float(sub["night_tube_extension_share"].mean()),
                "persistence": float(sub["common_window_persistence"].mean()),
                "weekend_ratio": float(sub["weekend_common_ratio"].mean()),
                "zero_bin_share": float(sub["zero_bin_share"].mean()),
                "km_to_centre": float(frame.loc[members, "km_to_centre"].mean()),
                "pct_LU": 100 * float(frame.loc[members, "is_lu"].mean()),
                "top_modes": ", ".join(
                    f"{mode} {count}" for mode, count in modes.head(3).items()
                ),
                "example_stations": ", ".join(
                    frame.loc[members]
                    .sort_values("total_activity", ascending=False)["Station"]
                    .head(3).tolist()
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="daytype_unpadded", choices=sorted(C.VARIANTS))
    # The interesting K range differs by variant: day-type closure pushes BIC to
    # 9, whereas the padded full-week variant's stability peak sits at K=4.
    parser.add_argument("--ks", default=None, help="comma-separated K values")
    args = parser.parse_args()
    variant = args.variant
    global FIGURE_KS
    FIGURE_KS = (
        [int(value) for value in args.ks.split(",")] if args.ks else DEFAULT_KS
    )

    root = C.OUT / variant
    figures = root / "figures"
    data = root / "data"
    for directory in [figures, data]:
        directory.mkdir(parents=True, exist_ok=True)

    import geopandas as gpd

    X = pd.read_parquet(C.FEATURES / f"X_{variant}.parquet")
    X.index = X.index.astype(str)
    colmap = parse_columns(X.columns)

    metrics = pd.read_csv(C.RAIL_UNIT_METRICS, dtype={"NLC": str}).set_index("NLC")
    zeros = pd.read_csv(
        C.FEATURES / "zero_bin_share.csv", dtype={"NLC": str}
    ).set_index("NLC")["zero_bin_share"]
    metrics["zero_bin_share"] = zeros

    coords = pd.read_csv(
        C.FYP / "data_processing" / "rail_allmodes" / "outputs" / "data"
        / "rail_allmodes_coords.csv",
        dtype={"unit": str},
    ).set_index("unit")
    base = gpd.read_file(LSOA_GEOJSON).to_crs("EPSG:27700")

    sections = []
    for k in FIGURE_KS:
        labels = pd.read_csv(
            root / "labels" / f"k{k}_labels.csv", dtype={"unit": str}
        ).set_index("unit")["cluster"]
        labels = labels.reindex(X.index)

        plot_profiles(X, colmap, labels.to_numpy(), k, figures, variant)

        frame = coords.loc[
            coords.index.intersection(X.index),
            ["Station", "mode_label", "is_lu", "easting", "northing"],
        ].copy()
        frame["cluster"] = labels.reindex(frame.index)
        frame["total_activity"] = metrics["total_activity"].reindex(frame.index)
        frame["km_to_centre"] = (
            np.hypot(frame.easting - CENTRE[0], frame.northing - CENTRE[1]) / 1000.0
        )
        frame = frame.dropna(subset=["easting", "cluster"])
        frame["cluster"] = frame["cluster"].astype(int)
        plot_map(frame, k, base, figures, variant)

        table = naming_table(frame, metrics, k)
        table.to_csv(data / f"cluster_profile_k{k}.csv", index=False)
        sections += [f"### K={k}", "", table.to_markdown(index=False, floatfmt=".3f"), ""]
        print(f"  K={k}: profile + map + table ({len(frame)} stations mapped)")

    (root / "report").mkdir(parents=True, exist_ok=True)
    (root / "report" / "FIGURES.md").write_text(
        "\n".join(
            [
                f"# {variant}: station maps, profiles and cluster descriptives, K=5-9",
                "",
                "Sidecar figures, 2026-08-01. Not an adopted result.",
                "",
                "## How to read these",
                "",
                "- Profiles: each day block sums to 1 over its OWN bins. MON/TWT/SUN "
                "have 28 bins and FRI/SAT have 44, so the shorter days sit ~1.6x "
                "higher. The step at a day boundary is the window, not behaviour. "
                "Between-day magnitude is exactly what day-type closure removes, so "
                "it must be read from `weekend_ratio` in the table, never from the "
                "curves.",
                "- Maps: circles are Underground stations, triangles the non-LU "
                "stations added by the all-modes merge (DLR, Overground, Elizabeth "
                "line, National Rail).",
                "- `night_tube_ext` is the share of a station's activity falling "
                "beyond the normal 01:00 close. Under this closure it is the single "
                "metric the partition explains best (eta-squared 0.59 at K=5 vs "
                "0.17 under full-week closure), so it is the axis to name clusters on.",
                "- `zero_bin_share` is carried alongside it because the two are "
                "mechanically coupled: a station off the Night Tube network has both "
                "a near-zero extension share and zeros through the late bins. Any "
                "cluster reading has to say which of the two it is claiming.",
                "- Cluster ids are arbitrary GMM component labels; they carry no "
                "meaning across K.",
                "",
                "## Cluster descriptives",
                "",
                *sections,
            ]
        ),
        encoding="utf-8",
    )
    print("Saved:", root / "report" / "FIGURES.md")


if __name__ == "__main__":
    main()
