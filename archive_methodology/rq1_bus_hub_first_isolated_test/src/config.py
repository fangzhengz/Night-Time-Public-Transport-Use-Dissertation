# -*- coding: utf-8 -*-
"""Central configuration -- single-variable hub-first isolation test, bus only.

Purpose: isolate the effect of the hub-first stop-to-LSOA aggregation
(rq1_bus_hub_first_reorganisation) on its own, against
../cluster_clean_version_fullweek's bus result. Every other setting is copied
verbatim from cluster_clean_version_fullweek/src/config.py -- MIN_TOTAL=1 (Clara's
"drop only empty units" rule, not the official rewrite's 50), no one-direction-
exception exclusion, no weaker-direction floor, no alpha shrinkage, identical
GMM search. The ONLY changed input is BUS_LONG, which now points at the
hub-first long table instead of cluster_clean_version_grouped's point-in-
polygon one. If a result differs from cluster_clean_version_fullweek's bus
run, that difference is attributable to hub-first aggregation alone.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
FYP = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
ROOT = FYP / "rq1_bus_hub_first_isolated_test"
OUT = ROOT / "outputs"
FEAT = OUT / "features"
DIAG = OUT / "diagnostics"
FIG = OUT / "figures"
LAB = OUT / "labels"
REPORT = OUT / "report"
for _d in (OUT, FEAT, DIAG, FIG, LAB, REPORT):
    _d.mkdir(parents=True, exist_ok=True)

# Only line that differs from cluster_clean_version_fullweek/src/config.py's
# BUS_LONG: hub-first output instead of cluster_clean_version_grouped's.
BUS_LONG = FYP / "rq1_bus_hub_first_reorganisation" / "outputs" / "preprocessed" / "bus_lsoa_night_long.parquet"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
CRS_BNG = "EPSG:27700"

# Reference (read-only): the true original this run is compared against.
ORIGINAL_BUS_BIC_GRID = FYP / "cluster_clean_version_fullweek" / "outputs" / "diagnostics" / "bus_bic_grid.csv"
ORIGINAL_BUS_KDIAG = FYP / "cluster_clean_version_fullweek" / "outputs" / "diagnostics" / "bus_kdiag.csv"
ORIGINAL_BUS_META = FYP / "cluster_clean_version_fullweek" / "outputs" / "features" / "bus_meta.csv"
ORIGINAL_BUS_LABELS = FYP / "cluster_clean_version_fullweek" / "outputs" / "labels"

# ---------------------------------------------------------------- full-week DAYS
# Unchanged from cluster_clean_version_fullweek: bus native day-types, hourly,
# 18:00-06:00, no weekday/weekend bucketing.
BUS_DAYS = ["Weekday", "Saturday", "Sunday"]
BUS_DIRECTIONS = ["boardings", "alightings"]

# ---------------------------------------------------------------- filtering
# Unchanged from cluster_clean_version_fullweek: keep low-activity units, only
# drop units with NO activity. NOT the official rewrite's 50.
MIN_TOTAL = 1

# ---------------------------------------------------------------- clustering
# Unchanged from cluster_clean_version_fullweek.
K_RANGE = list(range(2, 13))
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
REG_COVAR = 1e-6
MAX_ITER = 300
RANDOM_STATE = 42
N_BOOTSTRAP = 20
CAND_K = list(range(3, 9))      # 3..8

# ---------------------------------------------------------------- style
PURPLE, GREEN, RED, GOLD = "#500778", "#2F6B4F", "#9A3D3D", "#C89B3C"
