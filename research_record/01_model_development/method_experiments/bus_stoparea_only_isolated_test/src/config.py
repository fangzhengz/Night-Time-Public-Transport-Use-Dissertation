# -*- coding: utf-8 -*-
"""Paths for the StopArea-only single-variable isolation test."""
from pathlib import Path

FYP = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
ROOT = FYP / "rq1_bus_stoparea_only_isolated_test"
OUT = ROOT / "outputs"
PRE = OUT / "preprocessed"
DATA = OUT / "data"
FEAT = OUT / "features"
DIAG = OUT / "diagnostics"
FIG = OUT / "figures"
LAB = OUT / "labels"
REPORT = OUT / "report"
for _d in (OUT, PRE, DATA, FEAT, DIAG, FIG, LAB, REPORT):
    _d.mkdir(parents=True, exist_ok=True)

SOURCE_STOP_CROSSWALK = (
    FYP / "rq1_bus_hub_first_reorganisation" / "outputs" / "preprocessed"
    / "stop_to_logical_hub_crosswalk.csv"
)
STOP_FLOW_PARQUET = FYP / "outputs" / "preprocessed_busto" / "busto_stop_qhr_night.parquet"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
BUS_LONG = PRE / "bus_lsoa_night_long.parquet"
CRS_BNG = "EPSG:27700"
FLOAT_TOLERANCE = 1e-6

ORIGINAL_ROOT = FYP / "cluster_clean_version_fullweek" / "outputs"
ORIGINAL_BUS_BIC_GRID = ORIGINAL_ROOT / "diagnostics" / "bus_bic_grid.csv"
ORIGINAL_BUS_KDIAG = ORIGINAL_ROOT / "diagnostics" / "bus_kdiag.csv"
ORIGINAL_BUS_META = ORIGINAL_ROOT / "features" / "bus_meta.csv"
ORIGINAL_BUS_LABELS = ORIGINAL_ROOT / "labels"

HUBFIRST_ROOT = FYP / "rq1_bus_hub_first_isolated_test" / "outputs"
HUBFIRST_BUS_BIC_GRID = HUBFIRST_ROOT / "diagnostics" / "bus_bic_grid.csv"
HUBFIRST_BUS_KDIAG = HUBFIRST_ROOT / "diagnostics" / "bus_kdiag.csv"
HUBFIRST_BUS_META = HUBFIRST_ROOT / "features" / "bus_meta.csv"
HUBFIRST_BUS_LABELS = HUBFIRST_ROOT / "labels"

BUS_DAYS = ["Weekday", "Saturday", "Sunday"]
BUS_DIRECTIONS = ["boardings", "alightings"]
MIN_TOTAL = 1
K_RANGE = list(range(2, 13))
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
REG_COVAR = 1e-6
MAX_ITER = 300
RANDOM_STATE = 42
N_BOOTSTRAP = 20
CAND_K = list(range(3, 9))
PURPLE, GREEN, RED, GOLD = "#500778", "#2F6B4F", "#9A3D3D", "#C89B3C"
