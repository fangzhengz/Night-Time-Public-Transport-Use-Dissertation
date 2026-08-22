"""Spatial distribution of bus (BUSTO) night-time LSOA clusters.

The bus clustering is aggregated to LSOA, so each LSOA polygon is filled by its
GMM cluster label. One PNG per day-type group (weekday/weekend, both K=4).

Non-clustered LSOAs are split into two meaningful categories instead of a single
blank background:
  * low service  : has night bus demand but below the MIN_TOTAL=50 cluster cut
  * no service   : no bus stop / zero recorded demand in the 20:00+ night window
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import geopandas as gpd
import pandas as pd

ROOT = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
BASEMAP = ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"
OUTD = ROOT / "outputs" / "busto_lsoa_2000_gmm"
NIGHT = ROOT / "outputs" / "preprocessed_busto" / "busto_lsoa_qhr_night.parquet"

START_MIN = 20 * 60
MIN_TOTAL = 50  # must match the clustering threshold

LOW_COLOR = "#ffe08a"   # low service
NO_COLOR = "#ededed"    # no service

JOBS = [
    ("weekday", OUTD / "weekday" / "weekday_k4_labels.csv", 4, ["Weekday"]),
    ("weekend", OUTD / "weekend" / "weekend_k4_labels.csv", 4, ["Saturday", "Sunday"]),
]


def night_totals(raw: pd.DataFrame, days: list[str]) -> pd.Series:
    """Per-LSOA total night demand (boardings+alightings) for the given days."""
    d = raw[(raw["traffic_minute"] >= START_MIN) & (raw["day_type"].isin(days))]
    return d.groupby("lsoa")[["boardings", "alightings"]].sum().sum(axis=1)


def main() -> None:
    base = gpd.read_file(BASEMAP).to_crs(27700)
    raw = pd.read_parquet(NIGHT)
    raw["lsoa"] = raw["lsoa"].astype(str)

    for group, csv, k, days in JOBS:
        lab = pd.read_csv(csv, dtype={"lsoa": str})
        tot = night_totals(raw, days)

        gdf = base.merge(lab[["lsoa", "cluster"]], left_on="LSOA21CD",
                         right_on="lsoa", how="left")
        gdf["tot"] = gdf["LSOA21CD"].map(tot).fillna(0.0)

        # status: clustered / low / none
        clustered = gdf["cluster"].notna()
        low = (~clustered) & (gdf["tot"] > 0)          # has demand but below cut
        none = (~clustered) & (gdf["tot"] <= 0)        # no stop / no night demand

        clusters = sorted(lab["cluster"].unique())
        cmap = matplotlib.colormaps["tab10"].resampled(max(len(clusters), 3))
        color_of = {cl: cmap(i) for i, cl in enumerate(clusters)}

        fig, ax = plt.subplots(figsize=(11, 11))
        gdf[none].plot(ax=ax, color=NO_COLOR, edgecolor="#e2e2e2", linewidth=0.12)
        gdf[low].plot(ax=ax, color=LOW_COLOR, edgecolor="#e8d488", linewidth=0.12)
        for cl in clusters:
            gdf[gdf["cluster"] == cl].plot(
                ax=ax, color=color_of[cl], edgecolor="white", linewidth=0.1)

        n_clu = int(clustered.sum())
        n_low = int(low.sum())
        n_none = int(none.sum())
        handles = [
            mpatches.Patch(color=color_of[cl],
                           label=f"C{cl} (n={int((lab['cluster'] == cl).sum())})")
            for cl in clusters
        ]
        handles.append(mpatches.Patch(color=LOW_COLOR,
                                      label=f"low service <50 (n={n_low})"))
        handles.append(mpatches.Patch(color=NO_COLOR,
                                      label=f"no night service (n={n_none})"))

        ax.set_title(
            f"Bus night-time LSOA clusters — {group} "
            f"(20:00-start, K={k}, clustered n={n_clu})",
            fontsize=13,
        )
        ax.legend(handles=handles, title="cluster / service",
                  loc="lower right", framealpha=0.9, fontsize=9)
        ax.set_axis_off()
        fig.tight_layout()

        dest = csv.with_name(f"{group}_bus_cluster_map.png")
        fig.savefig(dest, dpi=160, bbox_inches="tight")
        plt.close(fig)
        print(f"{group}: clustered={n_clu}, low={n_low}, none={n_none} -> {dest.name}")


if __name__ == "__main__":
    main()
