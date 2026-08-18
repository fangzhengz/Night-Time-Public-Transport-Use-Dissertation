"""Configuration for the RQ2 LOAC (London Output Area Classification) lens.

Third parallel socio-spatial lens alongside LNWC and IMD (see
``rq2test analysis`` / ``rq2_new_clusters_analysis``). LOAC is used as a
composite categorical label (Supergroup, primary; Group, secondary) --
not decomposed into its raw Census input variables -- reusing the exact
chi-square/Cramer's V/enrichment + Voronoi-catchment-composition pattern
already built for LNWC in ``rq2test analysis/src/run_analysis.py``.

This folder uses the same clusterings as ``rq2_new_clusters_analysis``,
which are the official, adopted RQ1 results (rail promoted 2026-07-30, bus
2026-07-29) -- not the retired canonical Underground-only rail / raw_share
bus specs:
- Rail: ``numbat_all_area_test``'s all-modes (LU+DLR+Overground+Elizabeth
  line), NaPTAN-Greater-London-matched 403-station refit, K=5.
- Bus: ``rq1_bus_stoparea_clustering``'s official StopArea allocation, CLR
  feature transform, K=4 (adopted 2026-07-29 as the bus clustering result;
  see that folder's outputs/clr/diagnostics/kdiag.csv for the K=3 vs K=4
  stability tradeoff -- bootstrap min-cluster Jaccard 0.401 at K=4 vs 0.883
  at K=3, disclosed, not resolved, by this choice).
- Rail catchment radius: 800 m (matching ``rq2_new_clusters_analysis``'s
  own 800 m sidecar, ``config_800m.py``), to keep the same scale as that
  prior analysis rather than the 1200 m canonical default.

This folder never modifies its sources (LOAC files, rq1 label files,
rq2_new_clusters_analysis outputs) -- it only reads them.
"""

from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

# --- LOAC source data (already downloaded, never modified here) ---
LOAC_ROOT = FYP / "此前的尝试分析文件" / "LOAC2021_allfiles"
LOAC_LOOKUP = LOAC_ROOT / "Lookup_Table" / "LOAC_lookup.csv"
LOAC_OA_GPKG = LOAC_ROOT / "GIS_Files" / "LOAC_OA_Geopackages" / "LOAC_OA.gpkg"

# --- OA21 -> LSOA21 lookup (downloaded this session from the ONS Open
# Geography Portal "Output Area (2021) to LSOA to MSOA to LAD (December
# 2021) Exact Fit Lookup in EW (V3)", filtered to Greater London) ---
OA_LSOA_LOOKUP = ROOT / "data" / "oa21_lsoa21_lookup.csv"

# --- rail: numbat_all_area_test, all-modes merged, NaPTAN-matched
# 403-station refit, K=5 -- same clustering as rq2_new_clusters_analysis ---
RAIL_SRC = FYP / "numbat_all_area_test" / "outputs" / "data"
RAIL_LABELS = RAIL_SRC / "rail_allmodes_k5_labels.csv"
RAIL_META = RAIL_SRC / "rail_allmodes_feature_meta.csv"
RAIL_COORDS = FYP / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"
RAIL_K = 5

# --- bus: rq1_bus_stoparea_clustering, official StopArea allocation, CLR,
# K=4 -- same clustering as rq2_new_clusters_analysis ---
BUS_SRC = FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "clr"
BUS_LABELS = BUS_SRC / "labels" / "k4_labels.csv"
BUS_K = 4

# 800 m to match rq2_new_clusters_analysis/src/config_800m.py's scale,
# per explicit user instruction (not the 1200 m canonical default).
RAIL_CATCHMENT_METRES = 800
RANDOM_SEED = 42
N_PERMUTATIONS = 999

LSOA_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

OUTPUTS = ROOT / "outputs"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
SPATIAL_OUT = OUTPUTS / "spatial"
REPORT_OUT = OUTPUTS / "report"

CRS_BNG = "EPSG:27700"
CRS_WGS84 = "EPSG:4326"

# LOAC Supergroups A-G (7 categories, per the data itself -- the technical
# manual's prose says "six" but LOAC_lookup.csv contains 7 distinct SG
# values). Names and colours are LOAC's own official ones, from
# LOAC_Cluster_Descriptions.pdf, so figures/labels are directly
# cross-referenceable against the published classification.
LOAC_SUPERGROUPS = ["A", "B", "C", "D", "E", "F", "G"]
LOAC_SUPERGROUP_NAMES = {
    "A": "Professional Employment and Family Lifecycles",
    "B": "The Greater London Mix",
    "C": "Suburban Asian Communities",
    "D": "Central Connected Professionals and Managers",
    "E": "Social Rented Sector Families with Children",
    "F": "Young Families and Mainstream Employment",
    "G": "Older Residents in Owner-Occupied Suburbs",
}
# Bus cluster palette, copied verbatim from
# rq1_bus_stoparea_clustering/src/config.py (red-cyan-blue family, 2026-08-03)
# so the bus cluster map here matches the RQ1 bus maps instead of tab10.
BUS_CLUSTER_COLOURS = [
    "#4C93D3",  # 0 mid blue
    "#D1284B",  # 1 red
    "#00A6A6",  # 2 teal cyan
    "#1B3A6B",  # 3 deep navy
    "#F2A2AC",  # 4 rose
    "#7FCFCB",  # 5 pale cyan
    "#8C1327",  # 6 dark red
    "#A9C7E8",  # 7 pale blue
]
LOAC_SUPERGROUP_COLOURS = {
    "A": "#66c2a5",
    "B": "#fc8d62",
    "C": "#8da0cb",
    "D": "#e78ac3",
    "E": "#a6d854",
    "F": "#ffd92f",
    "G": "#D9dddf",
}

for directory in (DATA_OUT, FIGURE_OUT, SPATIAL_OUT, REPORT_OUT):
    directory.mkdir(parents=True, exist_ok=True)
