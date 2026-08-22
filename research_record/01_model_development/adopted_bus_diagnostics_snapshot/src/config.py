# -*- coding: utf-8 -*-
"""Configuration for StopArea-allocated bus clustering variants."""
from pathlib import Path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent

# 2026-08-08: night window changed from 18:00-06:00/min-direction=36 to
# 18:00-05:00/min-direction=33. The superseded pipeline's outputs are left
# untouched at rq1_bus_stoparea_clustering/outputs_archive_1806_min36_2026-08-08/
# and data_processing/bus_stoparea/outputs_archive_1806_min36_2026-08-08/ for
# rollback/audit; nothing there was moved or deleted.
LONG_INPUT = (
    FYP
    / "data_processing"
    / "bus_stoparea"
    / "outputs_1805_min33"
    / "preprocessed"
    / "bus_lsoa_night_long.parquet"
)
STOPAREA_SUMMARY = (
    FYP
    / "data_processing"
    / "bus_stoparea"
    / "outputs_1805_min33"
    / "data"
    / "preprocessing_summary.csv"
)
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LSOA_LAD_LOOKUP = FYP / "IMDdata" / "ons_lsoa11_lsoa21_lad22_london_lookup.csv"

OUT = ROOT / "outputs_1805_min33"
FEATURES = OUT / "features"
COMPARISON = OUT / "comparison"
REPORT = OUT / "report"
for directory in [OUT, FEATURES, COMPARISON, REPORT]:
    directory.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
# 2026-08-08: window truncated from 18:00-06:00 (12 hourly bins) to
# 18:00-05:00 (11 hourly bins). Sensitivity-tested in
# rq1_bus_05cutoff_sensitivity/ before adoption: headline night-persistent
# cluster >=98% stable; timing-metric eta2 improves, not degrades; the
# boundary between the two smaller (moderate/destination-leaning vs.
# peripheral low-flow) clusters redraws under either retention threshold.
HOURS = list(range(1080, 1740, 60))

# MIN_DIRECTION is derived from Marinas-Collado et al. (2022), "average >=1
# passenger per hourly interval": threshold = n_hours x n_day_types. It was
# 36 (=12x3) under the 18:00-06:00 window; with 11 hours it is 33 (=11x3), not
# a re-derivation of 36 -- reusing 36 as an absolute count would silently
# tighten the reliability floor to ~1.09/interval instead of the intended
# >=1/interval. The former `MIN_TOTAL = 50` companion rule remains non-binding
# (both directions >= 33 implies total >= 66 > 50).
MIN_DIRECTION = 33.0
CLR_PSEUDOCOUNT_ALPHA = 1.0

K_RANGE = list(range(2, 13))
# Ks that receive the full diagnostic battery (homogeneity, cluster geography).
CANDIDATE_KS = [3, 4]
# Ks that receive spatial maps and temporal profile figures. Wider than
# CANDIDATE_KS so K=5..8 can be inspected visually without committing them to
# the full diagnostic set.
FIGURE_KS = [3, 4, 5, 6, 7, 8]
BOOTSTRAP_KS = [2, 3, 4, 5, 6, 7, 8]
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
BOOTSTRAP_N_INIT = 3

# --- reported-solution refit protocol (added 2026-08-03) ---------------------
# The BIC grid above is a *scan*: one seed at N_INIT=20, which is enough to rank
# K but not to find each K's own optimum. `rq1_bus_k_selection_check` showed
# that at N_INIT=20 two of five seeds fail to reach the K=4 optimum altogether,
# and that a 100-restart fit beats the previously reported labels by 2,472 BIC.
# The ranking was unaffected (K=4 won 8/8 fits across both budgets), so the scan
# still selects K -- but the solution actually reported must be the best one
# found, not whichever a single seed happened to land on.
#
# Candidate Ks are therefore refitted at N_INIT_FINAL across FINAL_SEEDS and the
# maximum-likelihood solution retained. Cluster ids are then aligned to the scan
# solution's ids by Hungarian matching on the confusion matrix, so cluster
# numbering stays continuous with earlier outputs (GMM component order is
# arbitrary; this changes labels, never membership).
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
# --- map styling -------------------------------------------------------------
# Categorical cluster palette, red-cyan-blue family (2026-08-03; previously
# Okabe-Ito). Deliberately contains no grey and no black: matplotlib's default
# `tab10` has grey at index 7, which at K=8 produced a cluster indistinguishable
# from the excluded-area grey, and the same constraint applies here.
#
# The first four entries are ordered to track night persistence in the adopted
# K=4 solution rather than to be merely distinct: C1 (night-persistent) is the
# red, C2 (moderate-to-high) the teal-cyan, C0 (moderate directional) the mid
# blue, and C3 (low-flow peripheral) the deep navy. So warm = late-running,
# cool = early-quietening, which the previous categorical palette did not
# convey. Entries 4-7 extend the same three hue families for the K=5..8
# supplementary figures, where no such ordering is claimed.
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

# The two non-cluster categories are rendered separately and must never share a
# fill. They mean different things:
#   low flow  -- has night bus demand, below the evidence threshold
#   no stop   -- no StopArea representative point falls inside the LSOA at all;
#                these are not service gaps (median 27 m to the nearest stop
#                unit, 100% within 400 m) but a point-in-polygon artefact that
#                concentrates in dense inner boroughs.
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
