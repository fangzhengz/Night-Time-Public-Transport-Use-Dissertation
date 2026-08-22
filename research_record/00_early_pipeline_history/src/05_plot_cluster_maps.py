"""Spatial distribution of LU night-time station clusters.

Plots the 270-station GMM clusters (weekday K=5, weekend K=6) as coloured
points over the London LSOA boundary basemap. One PNG per day-type group.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import geopandas as gpd
import pandas as pd

ROOT = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
BASEMAP = ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"
OUTD = ROOT / "outputs" / "lu_rail_2000_diag"

JOBS = [
    ("weekday", OUTD / "weekday" / "weekday_k5_labels_xy.csv", 5),
    ("weekend", OUTD / "weekend" / "weekend_k6_labels_xy.csv", 6),
]


def main() -> None:
    base = gpd.read_file(BASEMAP).to_crs(27700)

    for group, csv, k in JOBS:
        df = pd.read_csv(csv)
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["easting"], df["northing"]),
            crs=27700,
        )

        clusters = sorted(gdf["cluster"].unique())
        cmap = cm.get_cmap("tab10", max(len(clusters), 3))

        fig, ax = plt.subplots(figsize=(11, 11))
        base.plot(ax=ax, color="#f2f2f2", edgecolor="#dcdcdc", linewidth=0.2)

        for i, cl in enumerate(clusters):
            sub = gdf[gdf["cluster"] == cl]
            ax.scatter(
                sub.geometry.x, sub.geometry.y,
                s=42, color=cmap(i), edgecolor="white", linewidth=0.6,
                label=f"C{cl} (n={len(sub)})", zorder=3,
            )

        ax.set_title(
            f"LU night-time station clusters — {group} (20:00-start, K={k}, n=270)",
            fontsize=13,
        )
        ax.legend(title="cluster", loc="lower right", framealpha=0.9, fontsize=9)
        ax.set_axis_off()
        # focus on the inner extent where stations sit (a little padding)
        minx, miny, maxx, maxy = gdf.total_bounds
        pad = 3000
        ax.set_xlim(minx - pad, maxx + pad)
        ax.set_ylim(miny - pad, maxy + pad)
        fig.tight_layout()

        dest = csv.with_name(f"{group}_cluster_map.png")
        fig.savefig(dest, dpi=160, bbox_inches="tight")
        plt.close(fig)
        print(f"{group}: K={k}, {len(gdf)} stations -> {dest.name}")


if __name__ == "__main__":
    main()
