"""Map the RQ3 mismatch score across London MSOAs.

Dissolves the LSOA21 boundaries up to MSOA11 (via the same lookup used
throughout this folder) and colours each MSOA by its standardised residual
(mismatch score) from run_mismatch_analysis.py, for both directions. Also
marks which MSOAs have any rail presence, to make the mode-decomposition
finding (the flagged gap MSOAs are pure-bus areas) visible on the map.

Does not touch any RQ1/RQ2 input or output. See ../README.md.
"""

import logging

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def build_msoa_geometry() -> gpd.GeoDataFrame:
    lsoa = gpd.read_file(config.LSOA_BOUNDARIES)[["LSOA21CD", "geometry"]]
    lookup = pd.read_csv(config.MSOA_LOOKUP, usecols=["LSOA21CD", "MSOA11CD"])
    lsoa = lsoa.merge(lookup, on="LSOA21CD", how="left").dropna(subset=["MSOA11CD"])
    msoa = lsoa.dissolve(by="MSOA11CD").reset_index()[["MSOA11CD", "geometry"]]
    log.info("Dissolved %d LSOA21 polygons into %d MSOA11 polygons", len(lsoa), len(msoa))
    return msoa


def main() -> None:
    msoa_geom = build_msoa_geometry()
    scores = pd.read_csv(config.DATA_OUT / "msoa_mismatch_scores.csv")
    pt = pd.read_csv(config.DATA_OUT / "msoa_pt_totals.csv")[["MSOA11CD", "rail_entry_total"]]

    fig, axes = plt.subplots(1, 2, figsize=(15, 8))
    for ax, direction in zip(axes, ("origin", "destination")):
        sub = scores[scores["direction"] == direction][["MSOA11CD", "std_residual"]]
        merged = msoa_geom.merge(sub, on="MSOA11CD", how="left").merge(pt, on="MSOA11CD", how="left")

        merged.plot(
            column="std_residual", cmap="RdBu", vmin=-3, vmax=3,
            legend=True, legend_kwds={"label": "Standardised residual (negative = candidate gap)", "shrink": 0.6},
            ax=ax, edgecolor="white", linewidth=0.1, missing_kwds={"color": "lightgrey"},
        )
        has_rail = merged[merged["rail_entry_total"] > 0]
        has_rail.boundary.plot(ax=ax, edgecolor="black", linewidth=0.6)

        ax.set_title(f"{direction}: mismatch score by MSOA\n(black outline = MSOA has a rail station)")
        ax.set_axis_off()

    fig.tight_layout()
    out_path = config.FIGURE_OUT / "mismatch_score_map.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info("Wrote %s", out_path)


if __name__ == "__main__":
    main()
