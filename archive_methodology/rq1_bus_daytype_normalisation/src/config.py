# -*- coding: utf-8 -*-
"""Configuration for the day-type-closure bus clustering sidecar.

WHY THIS FOLDER EXISTS (2026-08-01)
-----------------------------------
The canonical pipeline (`rq1_bus_stoparea_clustering`) normalises each
direction over its WHOLE 36-cell week, so one row's boarding block sums to 1
across all three day types jointly. That choice was made after the 2026-06-25
Clara catch-up, on the belief that she had asked for it.

Re-reading the transcript (18:00 mark) she actually said "using the full week
and try normalising every, well, I mean, AS YOU'VE DONE ALREADY" -- she asked
for the full-week VECTOR and explicitly deferred the denominator to whatever
was already in place, which at that point was per-day-group closure. Her own
paper (Peiret-Garcia, Kimani & Suel, "Beyond the Commute", `FYP/参考文献/
BtC_paper.pdf`, Eqs. 1-2) is unambiguous: the denominator is the station's
total for THAT DAY TYPE, and each 96-bin block sums to one independently.

So full-week closure is this project's own extension, not Clara's instruction,
and it diverges from the closest methodological precedent available (same
supervisor, same city, same data family). This folder tests the alternative.

SCOPE -- read-only sidecar. Nothing here writes into the canonical folder.
Inputs are the canonical folder's own preprocessed long table and
`sample_metrics.csv`, so the two pipelines cannot drift apart on the data.

THE FOUR VARIANTS
-----------------
B1 `daytype_raw_share`      per (direction, day_type) 12-bin closure.
B2 `daytype_clr_a1`         block-wise CLR, alpha=1.0, block-internal prior.
B3 `daytype_clr_a033`       block-wise CLR, alpha=0.33.
B4 `daytype_raw_share_strict`  B1 on the stricter sample (EVERY direction x
                            day_type block >= 36, not just the week total).

B3 exists because alpha's meaning changes silently under block closure. The
canonical CLR divides by the whole-week direction total (median ~400 counts),
so alpha=1 is ~1/400 of the mass. Under block closure the denominator is a
single block (median 133), making the same alpha ~3x stronger, and ~1/13 in
the sparse tail. Without B3, a CLR-vs-raw_share comparison would be partly
measuring smoothing strength rather than closure.

B4 exists because block closure gives every day type equal weight regardless
of evidence. 14.7% of (LSOA x direction x day_type) blocks carry fewer than 36
counts and 5.2% fewer than 20; under B1 a 20-count Sunday block pushes on the
distance metric exactly as hard as a 745-count weekday block. Full-week closure
happened to weight day types by their evidence; this is what giving that up
costs, and B4 bounds it.
"""
from pathlib import Path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent
CANONICAL = FYP / "rq1_bus_stoparea_clustering"

# --- inputs: shared with the canonical run, never copied ---------------------
LONG_INPUT = (
    FYP / "data_processing" / "bus_stoparea" / "outputs" / "preprocessed"
    / "bus_lsoa_night_long.parquet"
)
# Raw-count-derived per-LSOA metrics (activity, post_midnight_share, ...).
# These are computed from counts, NOT from features, so they are identical
# under either closure -- only the cluster grouping of them changes.
SAMPLE_METRICS = CANONICAL / "outputs" / "features" / "sample_metrics.csv"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LSOA_LAD_LOOKUP = FYP / "IMDdata" / "ons_lsoa11_lsoa21_lad22_london_lookup.csv"

# --- the adopted results this sidecar is measured against --------------------
CANON_CLR_K4_LABELS = CANONICAL / "outputs" / "clr" / "labels" / "k4_labels.csv"
CANON_RAW_K3_LABELS = CANONICAL / "outputs" / "raw_share" / "labels" / "k3_labels.csv"

OUT = ROOT / "outputs"
FEATURES = OUT / "features"
COMPARISON = OUT / "comparison"
REPORT = OUT / "report"
for directory in [OUT, FEATURES, COMPARISON, REPORT]:
    directory.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
HOURS = list(range(1080, 1800, 60))

# Retention. MIN_DIRECTION is the canonical whole-week rule and is held FIXED
# for B1-B3 so that ARI against the adopted labels is computed on identical
# units -- changing the sample and the closure at once would make the
# comparison uninterpretable. B4 alone tightens it.
MIN_DIRECTION = 36.0
STRICT_MIN_BLOCK = 36.0

VARIANTS = {
    "daytype_raw_share": {"kind": "raw_share", "alpha": None, "strict": False, "closure": "daytype"},
    "daytype_clr_a1": {"kind": "clr", "alpha": 1.0, "strict": False, "closure": "daytype"},
    "daytype_clr_a033": {"kind": "clr", "alpha": 0.33, "strict": False, "closure": "daytype"},
    "daytype_raw_share_strict": {"kind": "raw_share", "alpha": None, "strict": True, "closure": "daytype"},
    # B5, added 2026-08-01 to close the confound in B4. B4 changed the closure
    # AND the sample at once, so its striking numbers (activity eta2 0.138,
    # zero-cell eta2 0.028) could not be attributed to either. This cell is
    # full-week closure on the SAME strict sample, completing the 2x2:
    #
    #                   full-week closure          day-type closure
    #   base 3,372      canonical raw_share        B1
    #   strict 2,493    B5 (this)                  B4
    #
    # Without it B4's numbers must not be quoted as a closure effect.
    "fullweek_raw_share_strict": {"kind": "raw_share", "alpha": None, "strict": True, "closure": "fullweek"},
}

# --- GMM settings: copied verbatim from the canonical config so the two runs
# differ ONLY in how the feature matrix was closed -------------------------
K_RANGE = list(range(2, 13))
CANDIDATE_KS = [3, 4]
FIGURE_KS = [3, 4, 5, 6]
BOOTSTRAP_KS = [2, 3, 4, 5, 6, 7, 8]
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
BOOTSTRAP_N_INIT = 3
REG_COVAR = 1e-6
MAX_ITER = 300
SEED = 42

TIMING_METRICS = [
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
]

CLUSTER_COLOURS = [
    "#0072B2", "#E69F00", "#009E73", "#CC79A7",
    "#56B4E9", "#D55E00", "#F0E442", "#785EF0",
]

# Map styling copied verbatim from rq1_bus_stoparea_clustering/src/config.py.
# `04_figures.py` imports that folder's `map_style` module, which resolves
# `import config` to THIS module, so these names must stay in sync with the
# canonical ones or the sidecar maps will stop matching the maps Clara has
# already seen. The three-state distinction (clustered / low flow / no stop in
# LSOA) is the 2026-07-29 fix and must not be collapsed back into one grey.
LOW_FLOW_FACE = "#6e6e6e"
NO_STOP_FACE = "#ffffff"
NO_STOP_HATCH = "///"
NO_STOP_EDGE = "#000000"
NO_STOP_EDGE_WIDTH = 0.15
LOW_FLOW_LABEL = "Low night flow, excluded"
NO_STOP_LABEL = "No stop point within LSOA"

# Charing Cross, British National Grid -- the project's standard London centre
# reference (same value as bus_rail_relation_analysis/src/config.py).
CENTRE_EASTING = 530034.0
CENTRE_NORTHING = 180381.0
CRS_BNG = "EPSG:27700"

TARGET_LADS = {
    "E09000033": "Westminster",
    "E09000007": "Camden",
    "E09000021": "Kingston upon Thames",
    "E09000027": "Richmond upon Thames",
}
