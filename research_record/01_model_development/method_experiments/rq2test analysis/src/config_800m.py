"""Configuration for the 800 m rail catchment sensitivity variant.

Non-destructive sidecar to config.py: identical in every respect except
RAIL_CATCHMENT_METRES (1200 -> 800) and the output root (outputs ->
outputs_800m), so the 1200 m canonical results are never overwritten.
Follows the same pattern already used for the IMD2025 refresh
(run_imd2025_analysis.py) and the bus strict_min72_raw_share sensitivity
test. This was flagged as an open validation-gate item in the original
outputs/report/RESULTS_SUMMARY.md ("Repeat rail analysis with 800 m Voronoi
and station-containing LSOA definitions.") and is being run for the first
time on 2026-07-24.
"""

from pathlib import Path


HERE = Path(__file__).resolve()
TEST_ROOT = HERE.parents[1]
FYP = HERE.parents[2]

RQ1_ROOT = FYP / "cluster_clean_version_fullweek"

RAIL_K = 5
BUS_K = 3
RAIL_CATCHMENT_METRES = 800
RANDOM_SEED = 42
N_PERMUTATIONS = 999

RAIL_LABELS = RQ1_ROOT / "outputs" / "labels" / f"rail_k{RAIL_K}_labels.csv"
BUS_LABELS = RQ1_ROOT / "outputs" / "labels" / f"bus_k{BUS_K}_labels.csv"
RAIL_META = RQ1_ROOT / "outputs" / "features" / "rail_meta.csv"
BUS_META = RQ1_ROOT / "outputs" / "features" / "bus_meta.csv"
# Same local snapshot config.py now uses -- see config.py's comment.
RAIL_COORDS = TEST_ROOT / "data" / "rail_coords.csv"

LNWC = FYP / "night_time_work_data" / "london_night_workers_classification_data.csv"
LNWC_PORTRAITS = FYP / "night_time_work_data" / "lnwc_variable_dictionary_pen_portaits.csv"
LSOA_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

OUTPUTS = TEST_ROOT / "outputs_800m"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
SPATIAL_OUT = OUTPUTS / "spatial"
REPORT_OUT = OUTPUTS / "report"
WORKBOOK_OUT = OUTPUTS / "workbook"

CRS_BNG = "EPSG:27700"
CRS_WGS84 = "EPSG:4326"

LNWC_COLOURS = {
    1: "#E78AC3",
    2: "#FFD92F",
    3: "#8DA0CB",
    4: "#66C2A5",
    5: "#FC8D62",
    6: "#A6D854",
    7: "#E5C494",
}

for directory in (DATA_OUT, FIGURE_OUT, SPATIAL_OUT, REPORT_OUT, WORKBOOK_OUT):
    directory.mkdir(parents=True, exist_ok=True)
