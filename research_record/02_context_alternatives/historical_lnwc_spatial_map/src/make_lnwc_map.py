"""Standalone LNWC spatial distribution map (LSOA-level choropleth).

Reads the raw LNWC classification data and the London LSOA 2021 boundaries,
joins them, and produces a categorical choropleth coloured by the official
LNWC pen-portrait colours (7 clusters).

Source data:
- FYP/night_time_work_data/london_night_workers_classification_data.csv
- FYP/night_time_work_data/lnwc_variable_dictionary_pen_portaits.csv
- FYP/map/London_LSOA_2021_Boundaries.geojson
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
LNWC_DATA = ROOT / "night_time_work_data" / "london_night_workers_classification_data.csv"
LNWC_PEN_PORTRAITS = ROOT / "night_time_work_data" / "lnwc_variable_dictionary_pen_portaits.csv"
LSOA_GEOJSON = ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"
OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- load ---
lnwc = pd.read_csv(LNWC_DATA, dtype={"lsoa21cd": "string", "lad22cd": "string"})

pen = pd.read_csv(LNWC_PEN_PORTRAITS, encoding="cp1252")
pen = pen.rename(columns={"Cluster Group": "lnc_grp", "Name": "cluster_name", "Colour": "cluster_colour"})
pen["cluster_colour"] = pen["cluster_colour"].str.strip().str.strip('"')
pen["cluster_name"] = pen["cluster_name"].str.strip()
pen = pen[["lnc_grp", "cluster_name", "cluster_colour"]]

lnwc = lnwc.merge(pen, on="lnc_grp", how="left")

lsoa_gdf = gpd.read_file(LSOA_GEOJSON)
lsoa_gdf.columns = [str(c).strip() for c in lsoa_gdf.columns]
lsoa_gdf["lsoa21cd"] = lsoa_gdf["LSOA21CD"].astype("string").str.strip()

lnwc_map = lsoa_gdf.merge(
    lnwc[["lsoa21cd", "lnc_grp", "cluster_name", "cluster_colour"]],
    on="lsoa21cd",
    how="left",
    validate="one_to_one",
)

missing = int(lnwc_map["lnc_grp"].isna().sum())
print(f"LSOAs in boundary file with no LNWC match: {missing} / {len(lnwc_map)}")

lnwc_map["cluster_colour"] = lnwc_map["cluster_colour"].fillna("#DDDDDD")

# --- plot ---
fig, ax = plt.subplots(figsize=(10, 10))
lnwc_map.plot(ax=ax, color=lnwc_map["cluster_colour"], linewidth=0.05, edgecolor="#f6f6f6")
ax.set_title("London Night Workers Classification (LNWC) by LSOA", fontsize=13)
ax.set_axis_off()

legend_df = pen.sort_values("lnc_grp")
legend_handles = [
    Patch(facecolor=row["cluster_colour"], edgecolor="#333333", label=f"{row['lnc_grp']}. {row['cluster_name']}")
    for _, row in legend_df.iterrows()
]
if missing:
    legend_handles.append(Patch(facecolor="#DDDDDD", edgecolor="#333333", label="No LNWC data"))

ax.legend(
    handles=legend_handles,
    title="LNWC cluster",
    loc="lower left",
    bbox_to_anchor=(0.0, -0.02),
    fontsize=7,
    title_fontsize=8.5,
    frameon=True,
    ncol=2,
    columnspacing=1.0,
    handletextpad=0.5,
    labelspacing=0.3,
)

fig.tight_layout()
out_path = OUT_DIR / "lnwc_lsoa_spatial_distribution_map.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
print(f"Saved: {out_path}")
