# -*- coding: utf-8 -*-
"""Configuration for the rail day-type-closure sidecar.

Companion to `rq1_bus_daytype_normalisation`, same motivation: the adopted
rail run (`numbat_all_area_test`) normalises each direction over its WHOLE
172-bin week, which is this project's own extension rather than Clara's
instruction. Her paper (Peiret-Garcia, Kimani & Suel, Eqs. 1-2) closes each
day-type block independently.

WHY THIS FOLDER IS A 2x2 AND THE BUS ONE WAS NOT
------------------------------------------------
The bus sidecar's strict variant changed the closure AND the sample at once,
which left its headline numbers unattributable. Rail has the same trap in a
different guise: switching to day-type closure raises a second question --
what to do about the fact that the five rail day types do NOT share a window.

    MON / TWT / SUN   18:00-01:00   28 quarter-hour bins
    FRI / SAT         18:00-05:00   44 quarter-hour bins

Under full-week closure that asymmetry is harmless: every bin competes for the
same single denominator. Under day-type closure a 7-hour Monday and an 11-hour
Friday each receive mass 1.0, so Monday's columns sit at roughly 1/28 against
Friday's 1/44 -- a systematic ~1.6x scale difference between day types that has
nothing to do with behaviour.

Padding every day type out to 18:00-05:00 removes that, at the cost of 96 extra
dimensions on a 404-station sample that is already n < p. Rather than guess,
all four cells are fitted:

                     full-week closure      day-type closure
    unpadded 344     fullweek_unpadded      daytype_unpadded
    padded   440     fullweek_padded        daytype_padded

`fullweek_unpadded` reproduces the adopted feature matrix and is asserted
against it in 01, so the 2x2 is anchored to the real pipeline rather than to a
re-implementation that might have drifted.

NOTE ON PADDING: the 01:00-05:00 extension is NOT empty on non-Night-Tube days.
It carries 0.18-0.24% of those day types' evening activity across 368 of the
404 stations -- real all-modes service (National Rail, Elizabeth line) that the
current 01:00 truncation discards because the window was designed for
Underground Night Tube. So padding both equalises the blocks and stops throwing
that away; it does not fabricate structural zeros.

SCOPE -- read-only sidecar. Writes nothing outside its own outputs/.
"""
from pathlib import Path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
# ROOT.parent is FYP when this folder sits directly under FYP, but it now
# lives one level deeper (FYP/<archive>/rq1_rail_method_tests) after being
# archived on 2026-08-02 -- walk up an extra level if the direct parent
# doesn't look like FYP.
FYP = ROOT.parent if (ROOT.parent / "numbat_all_area_test").exists() else ROOT.parent.parent
CANONICAL = FYP / "numbat_all_area_test"

RAW_LONG = (
    FYP / "data_processing" / "rail_allmodes" / "outputs" / "preprocessed"
    / "numbat_allmodes_station_qhr_all_daytypes_final.parquet"
)
# The adopted feature matrix and labels this sidecar is measured against.
CANON_X = CANONICAL / "outputs" / "data" / "X_rail_allmodes.parquet"
CANON_K5_LABELS = CANONICAL / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
# Raw-count-derived per-station metrics (activity, direction balance, night
# tube extension, ...). Computed from counts, so identical under any closure.
RAIL_UNIT_METRICS = (
    FYP / "rq2_new_clusters_analysis" / "outputs" / "data" / "rail_unit_metrics.csv"
)

OUT = ROOT / "outputs"
FEATURES = OUT / "features"
COMPARISON = OUT / "comparison"
REPORT = OUT / "report"
for directory in [OUT, FEATURES, COMPARISON, REPORT]:
    directory.mkdir(parents=True, exist_ok=True)

EVENING_START = 18 * 60      # 1080
RAIL_CLOSE = 25 * 60         # 01:00 -> 1500
NIGHT_TUBE_END = 29 * 60     # 05:00 -> 1740
QUARTER = 15

RAIL_DAYS = ["MON", "TWT", "FRI", "SAT", "SUN"]
RAIL_DIRECTIONS = ["entry", "exit"]
NATIVE_WINDOWS = {
    "MON": (EVENING_START, RAIL_CLOSE),
    "TWT": (EVENING_START, RAIL_CLOSE),
    "FRI": (EVENING_START, NIGHT_TUBE_END),
    "SAT": (EVENING_START, NIGHT_TUBE_END),
    "SUN": (EVENING_START, RAIL_CLOSE),
}
PADDED_WINDOWS = {day: (EVENING_START, NIGHT_TUBE_END) for day in RAIL_DAYS}

MIN_TOTAL = 1  # canonical rule; drops the 37 tram-only zero-activity stations

VARIANTS = {
    "fullweek_unpadded": {"closure": "fullweek", "padded": False},
    "daytype_unpadded": {"closure": "daytype", "padded": False},
    "fullweek_padded": {"closure": "fullweek", "padded": True},
    "daytype_padded": {"closure": "daytype", "padded": True},
}

# --- GMM settings: copied from numbat_all_area_test/src/03_cluster_allmodes.py
# so the sidecar differs from the adopted run only in the feature matrix ----
K_RANGE = list(range(2, 13))
COVARIANCES = ["diag", "full"]
PRIMARY_COVARIANCE = "diag"   # what the adopted rail run reports
CANDIDATE_KS = [4, 5, 6, 7]
N_INIT = 20
BOOTSTRAP_N_INIT = 3
N_BOOTSTRAP = 20
REG_COVAR = 1e-6
MAX_ITER = 300
SEED = 42

# Random-seed stability decided K=5 over K=7 on the adopted run (mean ARI 0.894
# vs 0.703), so it is not optional here -- a closure change that quietly
# destabilises K is the failure mode this battery exists to catch.
#
# Protocol copied from numbat_all_area_test/src/07_stability_allmodes.py: 20
# full-data refits at seeds SEED+10000+run, each with its OWN n_init=20, scored
# by ARI against the reference partition. Scoring seed runs pairwise, or fitting
# them at n_init=1, produces numbers a factor lower that cannot be read against
# the adopted run's 0.894.
SEED_RUNS = 20
SEED_N_INIT = 20

TIMING_METRICS = [
    "midnight_share_common_window",
    "night_tube_extension_share",
    "common_window_persistence",
]
EXTERNAL_METRICS = TIMING_METRICS + ["direction_balance", "weekend_common_ratio"]
