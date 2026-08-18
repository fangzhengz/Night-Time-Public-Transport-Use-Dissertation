from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FYP = ROOT.parent

BUS_LABELS = FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "clr" / "labels" / "k4_labels.csv"
BUS_NAMES = FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "data" / "bus_cluster_names.csv"
RAIL_LABELS = FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
RAIL_NAMES = FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_cluster_names.csv"
RAIL_CATCHMENTS = FYP / "rq2_new_clusters_analysis" / "outputs_800m" / "spatial" / "rail_catchments_800m_allmodes.geojson"
LSOA21_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

OUTPUTS = ROOT / "outputs"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
REPORT_OUT = OUTPUTS / "report"

CRS_BNG = "EPSG:27700"
CHARING_CROSS_EASTING = 530134.0
CHARING_CROSS_NORTHING = 180379.0
N_PERMUTATIONS = 999
RANDOM_SEED = 42
TRANSPORT_GROUP_CODE = "10"

for directory in (DATA_OUT, FIGURE_OUT, REPORT_OUT):
    directory.mkdir(parents=True, exist_ok=True)

