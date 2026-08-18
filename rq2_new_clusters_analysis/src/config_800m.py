"""Configuration for the area-weighted rail catchment sensitivity variant,
applied on top of this folder's own non-canonical sensitivity clustering
results.

CHANGED MEANING 2026-08-08: config.py's own RAIL_CATCHMENT_METRES moved from
1200 to 800 (user decision, standardising on equal-weight LSOA aggregation
project-wide). This sidecar's radius (800) is therefore now IDENTICAL to
config.py's -- the only remaining difference is that the run_*_800m.py
scripts that import this config still use the original area-weighted LSOA
aggregation (piece_area_m2-weighted), never updated to match the equal-weight
change. This sidecar has consequently flipped from being a *radius*
sensitivity check into an *aggregation-weighting* sensitivity check: does
area-weighting vs equal-weighting change the IMD/LNWC association conclusions
at the same 800 m radius? The output root (outputs -> outputs_800m) still
keeps the two result sets apart.
"""

from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

# --- rail: numbat_all_area_test, all-modes merged, NaPTAN-matched 403-station refit, K=5 ---
RAIL_PREPROCESSED = FYP / "data_processing" / "rail_allmodes" / "outputs"
RAIL_SRC = FYP / "numbat_all_area_test" / "outputs" / "data"
RAIL_LABELS = RAIL_SRC / "rail_allmodes_k5_labels.csv"
RAIL_META = RAIL_SRC / "rail_allmodes_feature_meta.csv"
RAIL_COORDS = RAIL_PREPROCESSED / "data" / "rail_allmodes_coords.csv"
RAIL_RAW_LONG = RAIL_PREPROCESSED / "preprocessed" / "numbat_allmodes_station_qhr_all_daytypes_final.parquet"
RAIL_K = 5
EXPECTED_RAIL_UNITS = 403

# --- bus: rq1_bus_stoparea_clustering, official StopArea allocation, CLR, K=4 ---
BUS_ROOT = FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33"
BUS_SRC = BUS_ROOT / "clr"
BUS_LABELS = BUS_SRC / "labels" / "k4_labels.csv"
BUS_SAMPLE_METRICS = BUS_ROOT / "features" / "sample_metrics.csv"
BUS_RAW_LONG = (
    FYP
    / "data_processing"
    / "bus_stoparea"
    / "outputs_1805_min33"
    / "preprocessed"
    / "bus_lsoa_night_long.parquet"
)
BUS_HOUR_BINS = list(range(1080, 1740, 60))
BUS_K = 4
EXPECTED_BUS_UNITS = 3383

RAIL_CATCHMENT_METRES = 800
RANDOM_SEED = 42
N_PERMUTATIONS = 999

LNWC = FYP / "night_time_work_data" / "london_night_workers_classification_data.csv"
LNWC_PORTRAITS = FYP / "night_time_work_data" / "lnwc_variable_dictionary_pen_portaits.csv"
LSOA_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
IMD_LSOA21 = FYP / "IMDdata_2025" / "imd2025_lsoa21_london.csv"

# Canonical (existing, already-published) results kept only for side-by-side
# comparison in the final combined report -- never written to.
CANON_RAIL_SIGNIFICANCE = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "rail_cluster_metric_significance.csv"
CANON_BUS_SIGNIFICANCE = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_cluster_metric_significance.csv"
CANON_BUS_STATS = FYP / "rq2test analysis" / "outputs" / "data" / "statistical_summary.csv"
CANON_RAIL_DOMINANT_ENRICHMENT = FYP / "rq2test analysis" / "outputs" / "data" / "rail_dominant_lnwc_enrichment.csv"
CANON_IMD_WEAK_LINE = FYP / "rq2test analysis" / "outputs" / "imd_metrics_2025" / "data" / "cluster_vs_imd_kruskal_all.csv"

# Figure-label constants are shared with the 1,200 m configuration rather than
# duplicated, so the two variants cannot drift apart in how they present the
# same classification. Only paths, radius and output root differ between them.
from config import (  # noqa: E402
    BUS_CLUSTER_COLOURS,
    BUS_CLUSTER_NAMES,
    LNWC_SHORT_NAMES,
    RAIL_CLUSTER_NAMES,
)

LNWC_COLOURS = {
    1: "#E78AC3",
    2: "#FFD92F",
    3: "#8DA0CB",
    4: "#66C2A5",
    5: "#FC8D62",
    6: "#A6D854",
    7: "#E5C494",
}

CRS_BNG = "EPSG:27700"
CRS_WGS84 = "EPSG:4326"

OUTPUTS = ROOT / "outputs_800m"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
SPATIAL_OUT = OUTPUTS / "spatial"
REPORT_OUT = OUTPUTS / "report"
WORKBOOK_OUT = OUTPUTS / "workbook"

for directory in (DATA_OUT, FIGURE_OUT, SPATIAL_OUT, REPORT_OUT, WORKBOOK_OUT):
    directory.mkdir(parents=True, exist_ok=True)
