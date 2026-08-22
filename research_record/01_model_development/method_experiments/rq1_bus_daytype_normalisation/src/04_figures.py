# -*- coding: utf-8 -*-
"""Spatial maps, temporal profiles and a naming table for one variant, K=3..5.

Profiles are drawn in DAY-TYPE SHARE space even for the CLR variants. CLR
coordinates are log-ratio deviations and have no reading as "share of the
night", so plotting them would produce a figure nobody can interpret; the
canonical folder makes the same choice for the same reason. The clustering
itself is unaffected -- only the rendering is translated.

Maps reuse the canonical `map_style` module so the three-state legend
(clustered / low night flow / no stop in LSOA) is identical to the maps already
shown to Clara.
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

# `map_style` does `import config as C`; because this module has already been
# imported under that name, it binds to the sidecar config above.
sys.path.insert(0, str(C.CANONICAL / "src"))
import map_style  # noqa: E402

FIGURE_KS = [3, 4, 5]
HOUR_LABELS = ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"]


def load(variant: str):
    share = pd.read_parquet(C.FEATURES / "X_daytype_raw_share.parquet")
    share.index = pd.Index(share.index.astype(str), name="lsoa")
    metrics = pd.read_csv(C.SAMPLE_METRICS, dtype={"lsoa": str}).set_index("lsoa")
    zeros = pd.read_csv(
        C.FEATURES / "zero_bin_share.csv", dtype={"lsoa": str}
    ).set_index("lsoa")["zero_bin_share"]
    metrics = metrics.join(zeros)
    labels_by_k = {}
    for k in FIGURE_KS:
        frame = pd.read_csv(
            C.OUT / variant / "labels" / f"k{k}_labels.csv", dtype={"lsoa": str}
        ).set_index("lsoa")
        labels_by_k[k] = frame.loc[frame["cluster"] >= 0, "cluster"].astype(int)
    return share, metrics, labels_by_k


def centre_distance(boundaries) -> pd.Series:
    centroids = boundaries.to_crs(C.CRS_BNG).geometry.centroid
    distance = np.hypot(centroids.x - C.CENTRE_EASTING, centroids.y - C.CENTRE_NORTHING)
    return pd.Series(distance.to_numpy() / 1000.0, index=boundaries["lsoa"].astype(str))


def draw_profiles(variant: str, share, labels_by_k, out: Path) -> None:
    for k in FIGURE_KS:
        labels = labels_by_k[k]
        units = labels.index
        sizes = labels.value_counts().reindex(range(k), fill_value=0)
        fig, axes = plt.subplots(
            k, 3, figsize=(12.5, max(4.2, 2.3 * k)), sharex=True, sharey=True
        )
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            members = share.loc[units[labels == cluster]]
            for day_index, day_type in enumerate(C.DAY_TYPES):
                ax = axes[cluster, day_index]
                for direction, colour, marker in [
                    ("boardings", "#0072B2", "o"),
                    ("alightings", "#D55E00", "s"),
                ]:
                    block = members[
                        [f"{direction}_{day_type}_{hour}" for hour in C.HOURS]
                    ]
                    mean = block.mean(axis=0).to_numpy()
                    q1 = block.quantile(0.25).to_numpy()
                    q3 = block.quantile(0.75).to_numpy()
                    ax.fill_between(range(12), q1, q3, color=colour, alpha=0.15, linewidth=0)
                    ax.plot(
                        range(12), mean, marker=marker, markersize=2.6,
                        linewidth=1.4, color=colour, label=direction,
                    )
                ax.axvline(5.5, color="#999999", linewidth=0.7, linestyle=":")
                if cluster == 0:
                    ax.set_title(day_type, fontsize=10)
                if day_index == 0:
                    ax.set_ylabel(
                        f"C{cluster}\nn={int(sizes[cluster]):,} "
                        f"({sizes[cluster]/sizes.sum()*100:.1f}%)",
                        color=map_style.cluster_colour(cluster),
                        fontweight="bold", fontsize=9,
                    )
                ax.grid(alpha=0.18)
        axes[-1, 1].set_xticks(range(12), HOUR_LABELS, rotation=45)
        axes[-1, 1].set_xlabel("hour beginning")
        axes[0, -1].legend(loc="upper right", fontsize=8, framealpha=0.9)
        fig.suptitle(
            f"{variant}, K={k} — temporal profiles\n"
            "mean with interquartile band; each panel is that day type's share of "
            "the direction's OWN day-type total (dotted line = midnight)",
            y=1.005, fontsize=11,
        )
        fig.tight_layout()
        fig.savefig(out / f"profiles_k{k}.png", dpi=180, bbox_inches="tight")
        fig.savefig(out / f"profiles_k{k}.pdf", bbox_inches="tight")
        plt.close(fig)
        print(f"  profiles K={k}")


def draw_maps(variant: str, metrics, labels_by_k, out: Path):
    import geopandas as gpd

    boundaries = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(column for column in boundaries if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(
        columns={code_column: "lsoa"}
    )
    boundaries["lsoa"] = boundaries["lsoa"].astype(str)
    all_units = pd.Index(metrics.index.astype(str))

    for k in FIGURE_KS:
        labels = labels_by_k[k]
        mapped = map_style.build_status_frame(
            boundaries, labels.index, labels.to_numpy(), all_units
        )
        fig, ax = plt.subplots(figsize=(9.2, 9.2))
        map_style.draw_cluster_map(ax, mapped, k)
        ax.set_title(
            f"{variant}, K={k}\n"
            "day-type closure (each direction x day type sums to 1), "
            f"retained if both direction week totals >= {C.MIN_DIRECTION:g}",
            fontsize=11,
        )
        fig.tight_layout()
        fig.savefig(out / f"map_k{k}.png", dpi=200, bbox_inches="tight")
        fig.savefig(out / f"map_k{k}.pdf", bbox_inches="tight")
        plt.close(fig)
        print(f"  map K={k}")

    fig, axes = plt.subplots(1, 3, figsize=(19.5, 7.2))
    for ax, k in zip(axes, FIGURE_KS):
        labels = labels_by_k[k]
        mapped = map_style.build_status_frame(
            boundaries, labels.index, labels.to_numpy(), all_units
        )
        map_style.draw_cluster_map(ax, mapped, k, legend_fontsize=7)
        ax.set_title(f"K={k}", fontsize=12)
    fig.suptitle(
        f"{variant} — spatial distribution across K=3, 4, 5", fontsize=13, y=0.99
    )
    fig.tight_layout()
    fig.savefig(out / "map_k3_k4_k5_panel.png", dpi=200, bbox_inches="tight")
    fig.savefig(out / "map_k3_k4_k5_panel.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  panel K=3,4,5")
    return boundaries


def naming_table(variant: str, share, metrics, labels_by_k, distance, out: Path) -> str:
    """Per-cluster descriptives -- the evidence needed to re-name the clusters.

    Every cluster name in the downstream configs is tied to an arbitrary GMM
    component id and must be rebuilt from scratch for any refit, so this table
    is the deliverable that makes that possible.
    """
    sections: list[str] = []
    for k in FIGURE_KS:
        labels = labels_by_k[k]
        units = labels.index
        rows: list[dict] = []
        for cluster in range(k):
            members = units[labels == cluster]
            sub = metrics.loc[members]
            block = share.loc[members]
            # Deep-night mass in each direction's own day-type block.
            deep = {}
            for day_type in C.DAY_TYPES:
                columns = [
                    f"boardings_{day_type}_{hour}" for hour in C.HOURS if hour >= 1440
                ]
                deep[day_type] = float(block[columns].sum(axis=1).mean())
            rows.append(
                {
                    "cluster": f"C{cluster}",
                    "n": len(members),
                    "share_%": 100 * len(members) / len(units),
                    "median_total_activity": float(sub["total_activity"].median()),
                    "post_midnight_share": float(sub["post_midnight_share"].mean()),
                    "deep_night_share": float(sub["deep_night_share"].mean()),
                    "direction_balance": float(sub["direction_balance"].mean()),
                    "weekend_ratio": float(sub["weekend_ratio"].mean()),
                    "zero_bin_share": float(sub["zero_bin_share"].mean()),
                    "km_to_centre": float(distance.reindex(members).mean()),
                    "post00_wkdy": deep["Weekday"],
                    "post00_sat": deep["Saturday"],
                    "post00_sun": deep["Sunday"],
                }
            )
        frame = pd.DataFrame(rows)
        frame.to_csv(out.parent / "data" / f"cluster_profile_k{k}.csv", index=False)
        sections.extend(
            [f"### K={k}", "", frame.to_markdown(index=False, floatfmt=".3f"), ""]
        )
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="daytype_clr_a1", choices=sorted(C.VARIANTS))
    args = parser.parse_args()
    variant = args.variant

    out = C.OUT / variant / "figures"
    out.mkdir(parents=True, exist_ok=True)
    (C.OUT / variant / "data").mkdir(parents=True, exist_ok=True)

    share, metrics, labels_by_k = load(variant)
    print(f"[{variant}] drawing K={FIGURE_KS}")
    draw_profiles(variant, share, labels_by_k, out)
    boundaries = draw_maps(variant, metrics, labels_by_k, out)
    distance = centre_distance(boundaries)
    table = naming_table(variant, share, metrics, labels_by_k, distance, out)

    report = [
        f"# {variant}: spatial distribution and temporal profiles, K=3-5",
        "",
        "Sidecar figures, 2026-08-01. Not an adopted result.",
        "",
        "## How to read these",
        "",
        "- Profiles are in day-type share space (mean + interquartile band). "
        "Under day-type closure each panel sums to 1 within itself, so the "
        "three panels of a row show SHAPE only -- how much of a cluster's week "
        "falls on Saturday is no longer visible in the curves and must be read "
        "from `weekend_ratio` in the table below.",
        "- Maps carry the canonical three-state legend. Grey is measured but "
        "below-threshold night flow; hatched white is an LSOA with no StopArea "
        "point inside it (a point-in-polygon artefact, not a service gap).",
        "- `post00_*` is the share of that day type's boardings falling after "
        "midnight, i.e. the night-persistence signal, per day type.",
        "- Cluster ids are arbitrary GMM component labels and carry no meaning "
        "across K or across variants.",
        "",
        "## Cluster descriptives",
        "",
        table,
    ]
    (C.OUT / variant / "report" / "FIGURES.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print("Saved:", C.OUT / variant / "report" / "FIGURES.md")


if __name__ == "__main__":
    main()
