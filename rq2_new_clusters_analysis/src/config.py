"""Configuration for the RQ2 sensitivity pipeline on the new clustering results.

Two non-canonical RQ1 clustering results:
- Rail: numbat_all_area_test's all-modes (LU+DLR+Overground+Elizabeth line,
  co-located NLCs merged) clustering. As of 2026-07-24, preprocessing
  (extraction, co-located merge, NaPTAN coordinate match, filtering) lives
  in `FYP/data_processing/rail_allmodes/`, and `numbat_all_area_test`'s own
  `02`-`07` pipeline runs directly on that folder's current 403-station,
  NaPTAN-Greater-London-matched output (16 of the original 420 all-modes
  stations excluded for having no NaPTAN Greater-London coordinate match at
  all -- Reading, Slough, Maidenhead, Watford Junction, Shenfield, etc.,
  confirmed genuinely outside Greater London; see
  `data_processing/rail_allmodes/README.md` and
  `numbat_all_area_test/outputs/archive_420station_allmodes/README.md`). This mirrors
  canonical's own scope convention: canonical's 270-station clustering
  already includes several border Underground stations outside the strict
  Greater London boundary (Amersham, Chesham, Epping, etc.) and only
  excludes them downstream from LNWC/IMD, never from the clustering
  itself -- so does this refit. K=5 (this dataset's own BIC-preferred K
  too, confirmed via `03_cluster_allmodes.py`'s BIC grid). All outputs use
  `numbat_all_area_test`'s original, un-suffixed filenames (e.g.
  `rail_allmodes_k5_labels.csv`) -- the pre-filter 420-station versions are
  preserved at `outputs/archive_420station_allmodes/`.
- Bus: rq1_bus_stoparea_clustering's official StopArea allocation, CLR
  feature transform, K=4 -- adopted as the bus clustering result on
  2026-07-29 (BIC-preferred K for CLR; the bootstrap min-cluster Jaccard is
  0.401 at K=4 vs 0.883 at K=3, a known and disclosed stability tradeoff --
  see outputs_1805_min33/clr/diagnostics/kdiag.csv). 3,383 LSOAs
  (18:00-05:00, min_direction>=33, single-condition sample rule). This
  module previously pointed at the
  strict_min72_raw_share sensitivity sample (K=4, 3,009 LSOAs, min
  direction>=72); that sample is still available as a sensitivity check but
  is no longer the adopted result.

This folder never modifies its sources. It mirrors ``rq2test analysis``'s
structure (config.py + run_*.py + outputs/{data,figures,spatial,report,
workbook}) so results are directly comparable script-for-script.
"""

from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

# --- rail: numbat_all_area_test, all-modes merged, NaPTAN-matched 403-station refit, K=5 ---
# Preprocessing (raw extraction, co-located merge, NaPTAN coordinate match)
# lives in FYP/data_processing/rail_allmodes/ (moved there 2026-07-24, mirroring
# data_processing/bus_stoparea/'s separation from rq1_bus_stoparea_clustering/).
# Clustering/labels/features stay in numbat_all_area_test.
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

# Changed 2026-08-08, user decision: standardise on 800 m + equal-weight LSOA
# aggregation project-wide (matching rq2_independent_variables and
# rq2_loac_analysis), replacing the previous 1200 m + area-weighted design.
# The former 800 m variant (config_800m.py) was 800 m but still area-weighted,
# so it is not a duplicate of this -- it is now the area-weighting sensitivity
# check against this folder's own new equal-weight primary result.
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

# Bus cluster palette, copied verbatim from
# rq1_bus_stoparea_clustering/src/config.py (red-cyan-blue family, 2026-08-03)
# so the bus cluster map here matches the RQ1 bus maps instead of falling back
# to matplotlib's tab10. Rail maps are left on their own default; a shared
# palette would wrongly imply bus C1 and rail C1 are the same kind of cluster.
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

# Generated cluster names, read from the two clustering folders rather than
# restated here -- both regenerate them with self-asserting checks, so a refit
# cannot leave a stale label behind (see their 0*_cluster_names.py).
def _load_cluster_names(path, id_column="cluster", name_column="short"):
    import csv
    names = {}
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                names[int(row[id_column])] = f"C{row[id_column]} {row[name_column]}"
    except (OSError, KeyError, ValueError):
        return {}
    return names


BUS_CLUSTER_NAMES = _load_cluster_names(
    FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "data" / "bus_cluster_names.csv"
)
RAIL_CLUSTER_NAMES = _load_cluster_names(
    FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_cluster_names.csv"
)

# Short forms of the LNWC's own group names, for figure axes. The full names
# (in outputs/data/lnwc_group_lookup.csv) run to 70+ characters and cannot be
# used as tick labels; these preserve the distinguishing content of each so a
# heatmap can be read without consulting the source classification.
LNWC_SHORT_NAMES = {
    1: "1 Central\nnight-work hubs",
    2: "2 Inner suburbs,\nhigh night business",
    3: "3 Inner suburbs,\nlow night business",
    4: "4 Suburban business,\naverage activity",
    5: "5 Suburban transport\n& health, low activity",
    6: "6 Low-activity\nsuburban",
    7: "7 Night-worker\nperiphery",
}

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

OUTPUTS = ROOT / "outputs"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
SPATIAL_OUT = OUTPUTS / "spatial"
REPORT_OUT = OUTPUTS / "report"
WORKBOOK_OUT = OUTPUTS / "workbook"

for directory in (DATA_OUT, FIGURE_OUT, SPATIAL_OUT, REPORT_OUT, WORKBOOK_OUT):
    directory.mkdir(parents=True, exist_ok=True)
