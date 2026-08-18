from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

"""05 - Canonical-vs-all-modes comparison map.

2026-07-24: this script's coordinate-matching half moved to
`FYP/data_processing/rail_allmodes/src/01c_match_naptan_coords.py` (that
logic depends only on station name/mode, not on clustering, so it now runs
as part of preprocessing, before `02`-`04`). This script keeps only the
plotting half, reading that folder's `rail_allmodes_coords.csv` directly.
"""

FYP_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
FIG_DIR = Path(__file__).resolve().parents[1] / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COORDS_PATH = (
    FYP_ROOT / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"
)
CANON_LABELS_K5 = FYP_ROOT / "cluster_clean_version_fullweek" / "outputs" / "labels" / "rail_k5_labels.csv"
ALLMODES_LABELS_K5 = DATA_DIR / "rail_allmodes_k5_labels.csv"


def main() -> None:
    coords = pd.read_csv(COORDS_PATH, dtype={"unit": str})
    print(f"Coordinate coverage: {coords['easting'].notna().sum()}/{len(coords)} matched")

    canon_lab = pd.read_csv(CANON_LABELS_K5)
    canon_lab["unit"] = canon_lab["unit"].astype(str)
    allmodes_lab = pd.read_csv(ALLMODES_LABELS_K5)
    allmodes_lab["unit"] = allmodes_lab["unit"].astype(str)

    canon_plot = canon_lab.merge(coords[["unit", "easting", "northing", "is_lu"]], on="unit", how="left").dropna(
        subset=["easting"]
    )
    allmodes_plot = allmodes_lab.merge(
        coords[["unit", "easting", "northing", "is_lu"]], on="unit", how="left"
    ).dropna(subset=["easting"])

    cmap = plt.get_cmap("tab10")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.4))

    ax = axes[0]
    for cluster in sorted(canon_plot["cluster"].unique()):
        part = canon_plot[canon_plot["cluster"] == cluster]
        ax.scatter(part["easting"], part["northing"], s=22, color=cmap(cluster % 10), label=f"C{cluster}")
    ax.set_title(f"Canonical: 270 Underground stations, K=5\n(n={len(canon_plot)})")
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_xticks([])
    ax.set_yticks([])

    ax = axes[1]
    for cluster in sorted(allmodes_plot["cluster"].unique()):
        part = allmodes_plot[allmodes_plot["cluster"] == cluster]
        old = part[part["is_lu"]]
        new = part[~part["is_lu"]]
        ax.scatter(old["easting"], old["northing"], s=22, marker="o", color=cmap(cluster % 10), label=f"C{cluster} (LU)")
        if len(new):
            ax.scatter(
                new["easting"], new["northing"], s=34, marker="^",
                color=cmap(cluster % 10), edgecolors="black", linewidths=0.4,
                label=f"C{cluster} (non-LU)",
            )
    ax.set_title(f"All-modes: rail-family stations, K=5\n(n={len(allmodes_plot)}; triangles = added non-LU)")
    ax.set_aspect("equal")
    ax.legend(fontsize=6.5, loc="upper left", ncol=2)
    ax.set_xticks([])
    ax.set_yticks([])

    fig.suptitle("Rail extension check: canonical Underground-only vs all NUMBAT rail modes (K=5)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "canonical_vs_allmodes_k5_map.png", dpi=220)
    plt.close(fig)
    print("Saved map:", FIG_DIR / "canonical_vs_allmodes_k5_map.png")


if __name__ == "__main__":
    main()
