"""Configuration for the RQ2 Spatial Signatures sidecar analysis.

This is an external contextual-characterisation layer.  It reads the adopted
Rail K=5 and Bus K=4 labels and never feeds Spatial Signatures back into either
clustering model.
"""

from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

SOURCE = ROOT / "data" / "source"
SIGNATURE_LSOA11 = SOURCE / "lsoa_estimates.csv"
SIGNATURE_TYPES = SOURCE / "type_code.csv"
SIGNATURE_META = SOURCE / "meta.txt"
FIGSHARE_META = SOURCE / "figshare_article_16691575.json"

LSOA11_LSOA21_LOOKUP = SOURCE / "ons_lsoa11_lsoa21_exact_fit_v3.csv"
LSOA21_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

BUS_LABELS = (
    FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "clr" / "labels" / "k4_labels.csv"
)
BUS_CLUSTER_NAMES = (
    FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "data" / "bus_cluster_names.csv"
)

RAIL_LABELS = FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
RAIL_META = FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_feature_meta.csv"
RAIL_COORDS = (
    FYP / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"
)
RAIL_CLUSTER_NAMES = (
    FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_cluster_names.csv"
)

OUTPUTS = ROOT / "outputs"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
SPATIAL_OUT = OUTPUTS / "spatial"
REPORT_OUT = OUTPUTS / "report"

for directory in (DATA_OUT, FIGURE_OUT, SPATIAL_OUT, REPORT_OUT):
    directory.mkdir(parents=True, exist_ok=True)

CRS_BNG = "EPSG:27700"
CRS_WGS84 = "EPSG:4326"
RAIL_CATCHMENT_METRES = 800
CHARING_CROSS_EASTING = 530134.0
CHARING_CROSS_NORTHING = 180379.0
N_PERMUTATIONS = 999
RANDOM_SEED = 42

# Published Figshare checksums, article 16691575 (version 3 metadata read on
# 2026-08-07).  The analysis fails loudly if a source file is incomplete or is
# silently replaced by a later file with different contents.
EXPECTED_MD5 = {
    "lsoa_estimates.csv": "8be04235026ce44fb5f2f5170eaef6ae",
    "type_code.csv": "db46749d1cc951c78366e9a61187ea8a",
    "meta.txt": "ab8e4a1baf31f3acbd792846c24cb1ac",
    "ons_lsoa11_lsoa21_exact_fit_v3.csv": "78e5d3fac243d5282b653ce6a77c1c4e",
}
