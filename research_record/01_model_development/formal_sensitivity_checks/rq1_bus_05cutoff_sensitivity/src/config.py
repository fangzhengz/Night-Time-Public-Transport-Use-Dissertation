# -*- coding: utf-8 -*-
"""Configuration for the 05:00-cutoff sensitivity sidecar.

Identical to `rq1_bus_stoparea_clustering/src/config.py` except:
  - LONG_INPUT points at this sidecar's own bus_stoparea_05cutoff output
    (built from a BUSTO preprocessing run with --end-min 1740, i.e. an
    18:00-05:00 night window instead of the canonical 18:00-06:00).
  - HOURS drops the 05:00 hour bin (11 hours instead of 12).
  - OUT points at this sidecar's own outputs/ tree; canonical outputs under
    rq1_bus_stoparea_clustering/outputs/ are never read or written.
All fitting hyperparameters (K_RANGE, CANDIDATE_KS, COVARIANCES, N_INIT,
N_INIT_FINAL, FINAL_SEEDS, BOOTSTRAP_KS, BOOTSTRAP_N_INIT, SEED,
MIN_DIRECTION, CLR_PSEUDOCOUNT_ALPHA) are unchanged from canonical so this is
a controlled comparison that varies only the night-window cutoff.
"""
from pathlib import Path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent

LONG_INPUT = (
    ROOT / "bus_stoparea_05cutoff" / "outputs" / "preprocessed" / "bus_lsoa_night_long.parquet"
)
STOPAREA_SUMMARY = (
    ROOT / "bus_stoparea_05cutoff" / "outputs" / "data" / "preprocessing_summary.csv"
)
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LSOA_LAD_LOOKUP = FYP / "IMDdata" / "ons_lsoa11_lsoa21_lad22_london_lookup.csv"

OUT = ROOT / "clustering_05cutoff" / "outputs"
FEATURES = OUT / "features"
COMPARISON = OUT / "comparison"
REPORT = OUT / "report"
for directory in [OUT, FEATURES, COMPARISON, REPORT]:
    directory.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
# 18:00-05:00 (was 18:00-06:00): drops the 05:00 hour bin. 11 bins instead of 12.
HOURS = list(range(1080, 1740, 60))

# Corrected 2026-08-08: MIN_DIRECTION is derived from the Mariñas-Collado et
# al. (2022) "average >=1 passenger per hourly interval" rule -- canonical is
# 36 because 12 hours x 3 day types = 36 intervals per direction. With the
# window truncated to 18:00-05:00 (11 hours), the equivalent threshold is
# 11 x 3 = 33, not the canonical 36 (36 would over-tighten the reliability
# floor to ~1.09/interval instead of the intended >=1/interval).
MIN_DIRECTION = 33.0
CLR_PSEUDOCOUNT_ALPHA = 1.0

K_RANGE = list(range(2, 13))
CANDIDATE_KS = [3, 4]
FIGURE_KS = [3, 4, 5, 6, 7, 8]
BOOTSTRAP_KS = [2, 3, 4, 5, 6, 7, 8]
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
BOOTSTRAP_N_INIT = 3

N_INIT_FINAL = 100
FINAL_SEEDS = [42, 7, 123, 2026, 999]
REG_COVAR = 1e-6
MAX_ITER = 300
SEED = 42

TIMING_METRICS = [
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
]

CLUSTER_COLOURS = [
    "#4C93D3",  # 0 mid blue
    "#D1284B",  # 1 red
    "#00A6A6",  # 2 teal cyan
    "#1B3A6B",  # 3 deep navy
    "#F2A2AC",  # 4 rose
    "#7FCFCB",  # 5 pale cyan
    "#8C1327",  # 6 dark red
    "#A9C7E8",  # 7 pale blue
]

LOW_FLOW_FACE = "#6e6e6e"
NO_STOP_FACE = "#ffffff"
NO_STOP_HATCH = "///"
NO_STOP_EDGE = "#000000"
NO_STOP_EDGE_WIDTH = 0.15
LOW_FLOW_LABEL = "Low night flow, excluded"
NO_STOP_LABEL = "No stop point within LSOA"

TARGET_LADS = {
    "E09000033": "Westminster",
    "E09000007": "Camden",
    "E09000021": "Kingston upon Thames",
    "E09000027": "Richmond upon Thames",
}
