# -*- coding: utf-8 -*-
"""Central configuration — FULL-WEEK variant of the clean RQ1 pipeline.

Single source of truth for all paths and parameters.

VERSION: FULL-WEEK (Clara catch-up, 2026-06-25).
  NO weekday/weekend bucketing. Each unit gets ONE feature vector that is the
  whole week concatenated DAY BY DAY using the native day-types the data provides
  (rail: MON, TWT=Tue-Thu, FRI, SAT, SUN; bus: Weekday, Saturday, Sunday), each
  day one representative night. The whole vector is then normalised per direction
  over the FULL WEEK (entry over the full week sums to 1; exit likewise). This
  preserves the across-day MAGNITUDE balance, so weekend / Night-Tube behaviour
  becomes a discriminating dimension and stations that look alike on weekdays but
  flip on weekends are separated (the key finding from Clara's paper). Result:
  TWO classifications only -- rail and bus -- still clustered SEPARATELY. Because
  each segment is a single day-type there is no within-block pooling.

  Window 18:00-06:00. Rail 15-min, bus hourly (the native granularities). A 15-min
  bus variant was trialled (cross-mode slice consistency) but made bus clustering
  markedly noisier (BIC ran away, singleton clusters); the slice-consistent option
  is pursued instead at 1-hour-both in the sibling folder cluster_clean_version_1h.
  Low-activity units are KEPT (per Clara), only fully-empty units dropped.

Preprocessing: rail reads the RAW all-day-types NUMBAT table (5 native day-types
kept separate); bus reuses the grouped variant's validated hourly LSOA long table.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
FYP = Path(r"D:\SDS2025_workspace\CASA_FYP\FYP")
CLEAN = FYP / "cluster_clean_version_fullweek"
OUT = CLEAN / "outputs"
FEAT = OUT / "features"
DIAG = OUT / "diagnostics"
FIG = OUT / "figures"
LAB = OUT / "labels"
for _d in (OUT, FEAT, DIAG, FIG, LAB):
    _d.mkdir(parents=True, exist_ok=True)

PRE = FYP / "cluster_clean_version_grouped" / "outputs" / "preprocessed"
RAIL_RAW_SRC = FYP / "outputs" / "preprocessed_numbat" / "numbat_lu_station_qhr_all_daytypes.parquet"
BUS_LONG = PRE / "bus_lsoa_night_long.parquet"        # [day_type, direction, lsoa, hour_bin, count] (hourly)
RAIL_COORDS = PRE / "rail_coords.csv"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

# ---------------------------------------------------------------- full-week DAYS
# NO weekday/weekend bucketing. Each modality vector = the whole week concatenated
# day-by-day, native day-types in this order. Each day is one representative night;
# the whole vector is normalised per direction over the FULL WEEK (see 03).
# Column tag: "{direction}_{day}_{minute}".
EVENING_START = 18 * 60                 # 1080
RAIL_CLOSE = 25 * 60                    # 01:00 -> 1500  (no Night Tube)
NIGHT_TUBE_END = 29 * 60               # 05:00 -> 1740  (Night Tube nights)
RAIL_DAYS = ["MON", "TWT", "FRI", "SAT", "SUN"]
RAIL_DAY_WINDOWS = {                    # [lo, hi) extended minutes; rail kept at 15-min
    "MON": (EVENING_START, RAIL_CLOSE),    # 18:00-01:00 -> 28 bins
    "TWT": (EVENING_START, RAIL_CLOSE),    # 18:00-01:00 -> 28 bins
    "FRI": (EVENING_START, NIGHT_TUBE_END),# 18:00-05:00 -> 44 bins (Night Tube)
    "SAT": (EVENING_START, NIGHT_TUBE_END),# 18:00-05:00 -> 44 bins (Night Tube)
    "SUN": (EVENING_START, RAIL_CLOSE),    # 18:00-01:00 -> 28 bins
}
BUS_DAYS = ["Weekday", "Saturday", "Sunday"]   # 18:00-06:00 hourly -> 12 bins each

RAIL_DIRECTIONS = ["entry", "exit"]
BUS_DIRECTIONS = ["boardings", "alightings"]

# ---------------------------------------------------------------- filtering
# Keep low-activity units (Clara 2026-06-25): only drop units with NO activity.
MIN_TOTAL = 1

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
