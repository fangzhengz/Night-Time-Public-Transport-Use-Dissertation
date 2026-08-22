# -*- coding: utf-8 -*-
"""Central configuration — GROUPED variant of the clean RQ1 pipeline.

Single source of truth for all paths and parameters.

VERSION: GROUPED — separate clustering per day-group (service-regime split):
  rail  weekday = MON+TWT (~01:00 close)   |  weekend = Fri+Sat pooled (Night Tube, to 05:00); Sunday EXCLUDED
  bus   weekday = Weekday                  |  weekend = Sat+Sun pooled
Within a group the member day-times are POOLED (counts summed -> one profile),
so the Night-Tube overnight signal reinforces instead of being diluted by the
early-closing weekday/Sunday envelope (the dilution seen in the concatenated
version). Parallel folder cluster_clean_version/ holds the BtC concatenated
variant. Everything else identical: BtC raw-share, per-vector normalisation,
GMM, 4-covariance BIC selection, K not hard-picked.

Preprocessing (steps 01/02 and their outputs in outputs/preprocessed/) is reused
unchanged from the concatenated version; only 03/04/05 differ.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
FYP = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
CLEAN = FYP / "cluster_clean_version_grouped"
OUT = CLEAN / "outputs"
PRE = OUT / "preprocessed"
FEAT = OUT / "features"
DIAG = OUT / "diagnostics"
FIG = OUT / "figures"
LAB = OUT / "labels"
for _d in (OUT, PRE, FEAT, DIAG, FIG, LAB):
    _d.mkdir(parents=True, exist_ok=True)

# Reused validated inputs.
RAIL_LONG_SRC = FYP / "outputs" / "preprocessed_numbat" / "numbat_lu_station_qhr_all_daytypes.parquet"
BUS_STOP_SRC = FYP / "outputs" / "preprocessed_busto" / "busto_stop_qhr_night.parquet"
RAIL_COORDS_CSV = FYP / "地铁进出站数据" / "地铁车站空间数据" / "Underground_Stations.csv"
BUS_STOPS_CSV = FYP / "巴士数据" / "Bus_Stops.csv"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

# ---------------------------------------------------------------- night window (steps 01/02)
EVENING_START = 18 * 60
RAIL_WINDOWS = {
    "weekday": (EVENING_START, 25 * 60),   # 18:00 - 01:00  -> 28 bins
    "Friday":  (EVENING_START, 29 * 60),   # 18:00 - 05:00  -> 44 bins
    "Saturday": (EVENING_START, 29 * 60),  # 18:00 - 05:00  -> 44 bins
    "Sunday":  (EVENING_START, 25 * 60),   # 18:00 - 01:00  -> 28 bins
}
RAIL_DAYTIME_SOURCES = {
    "weekday": ["MON", "TWT"], "Friday": ["FRI"], "Saturday": ["SAT"], "Sunday": ["SUN"],
}
RAIL_DAYTIME_ORDER = ["weekday", "Friday", "Saturday", "Sunday"]
BUS_START = 18 * 60
BUS_END = 30 * 60
BUS_BIN = 60
BUS_DAYTYPE_ORDER = ["Weekday", "Saturday", "Sunday"]

# ---------------------------------------------------------------- DAY GROUPS (separate clusterings)
# Member labels refer to the day-time labels in the step-01 rail long table and
# the day_type values in the step-02 bus long table. Members are POOLED.
RAIL_GROUPS = {
    "weekday": ["weekday"],             # MON+TWT (already averaged in step 01)
    "weekend": ["Friday", "Saturday"],  # Night-Tube days, pooled; Sunday EXCLUDED
}
BUS_GROUPS = {
    "weekday": ["Weekday"],
    "weekend": ["Saturday", "Sunday"],
}

RAIL_DIRECTIONS = ["entry", "exit"]
BUS_DIRECTIONS = ["boardings", "alightings"]

# ---------------------------------------------------------------- filtering
MIN_TOTAL = 50

# ---------------------------------------------------------------- clustering
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
CRS_BNG = "EPSG:27700"
