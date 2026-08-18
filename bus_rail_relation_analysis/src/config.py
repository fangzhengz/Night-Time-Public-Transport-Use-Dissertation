"""Configuration for the bus x rail spatial relation analysis.

Origin: Clara's 2026-07-28 supervision meeting. She overlaid the Underground
network on the bus cluster map by hand and observed that bus clusters appeared
to sit along tube lines, then asked for "some sort of analysis of how do the
bus clusters link to ... distance to underground stations or something like
that". This folder answers exactly that and nothing more.

SCOPE -- deliberately narrow (agreed with the user 2026-07-30):

  What this folder tests: how far the bus night-activity clusters sit from
  rail NODES, and whether particular bus cluster types co-occur with
  particular rail cluster types.

  What this folder does NOT test:
  * Interchange / "last-mile" behaviour. Identifying an actual transfer needs
    OD flows and timetables, neither of which this project has. Any
    interchange reading stays in the Discussion as interpretation, never in
    the Results as a claim.
  * Corridor / along-the-line structure. The user's claim (2026-07-30) is
    about proximity to nodes, not about elongation along lines, so rail line
    geometry is deliberately not used. If that ever changes, the extra input
    needed is TfL line geometry -- distance-to-nearest-station cannot stand
    in for distance-to-nearest-line.
  * Night-rail service gaps ("test C" in the planning discussion): whether
    bus compensates where no night rail exists. Deferred to the Chapter 6
    transport-vulnerability write-up -- it is a different question (service
    provision) wearing the same coat, and mixing it in here blurs the aim.

TWO KNOWN CONFOUNDS, both handled rather than hidden:

  1. Centre-periphery gradient. Both clusterings track "how central are you",
     so SOME association is close to guaranteed and therefore uninformative on
     its own. Distance to Charing Cross is carried through every output so the
     write-up can say how much of the pattern is just centrality.
  2. Pseudo-replication in the co-occurrence test. 3,372 bus LSOAs share only
     403 rail station labels in the current run, so a chi-square on n=3372
     would be wildly over-confident (effective n is nearer the station count).
     Cramer's V is reported as a
     descriptive effect size and significance comes from a permutation test
     that shuffles labels ACROSS STATIONS, preserving the replication
     structure under the null.

Clusterings used are the official adopted RQ1 results (bus 2026-07-29, rail
2026-07-30), identical to those in ``rq2_new_clusters_analysis`` and
``rq2_loac_analysis``. This folder never modifies its sources -- read only.
"""

from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

# --- rail: numbat_all_area_test, all-modes merged (LU + DLR + Overground +
# Elizabeth line + National Rail), NaPTAN-Greater-London-matched 403-station
# refit, K=5 ---
RAIL_LABELS = FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
RAIL_COORDS = FYP / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"
# Per-station night metrics (cluster, direction_balance, night_tube_extension_
# share, ...) already computed by rq2_new_clusters_analysis -- reused, not
# recomputed, so the two folders cannot drift apart.
RAIL_UNIT_METRICS = FYP / "rq2_new_clusters_analysis" / "outputs" / "data" / "rail_unit_metrics.csv"
RAIL_K = 5

# --- bus: rq1_bus_stoparea_clustering, official StopArea allocation, CLR
# feature transform, K=4 ---
BUS_LABELS = FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "clr" / "labels" / "k4_labels.csv"
BUS_UNIT_METRICS = FYP / "rq2_new_clusters_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"
BUS_K = 4

# --- StopArea geometry + LSOA crosswalk (the whole point of measuring from
# StopArea points rather than LSOA centroids: an outer-London LSOA can be
# large, so its centroid is a poor stand-in for where its bus stops are) ---
STOPAREA_CROSSWALK = (
    FYP / "data_processing" / "bus_stoparea" / "outputs" / "preprocessed"
    / "stoparea_unit_lsoa_crosswalk.csv"
)
# StopArea-level quarter-hourly night counts, used only to activity-weight the
# StopArea -> LSOA distance aggregation.
STOPAREA_NIGHT_QHR = (
    FYP / "data_processing" / "bus_stoparea" / "outputs" / "preprocessed"
    / "bus_stoparea_night_qhr_london.parquet"
)

LSOA_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

# --- distance settings ---
# 800 m primary (user decision 2026-07-30), 1200 m sensitivity. Both radii are
# pre-existing project conventions: 800 m matches rq2_loac_analysis and
# rq2_new_clusters_analysis's 800 m sidecar, 1200 m the canonical rail Voronoi
# catchment. The radius only caps the co-occurrence test (test B) -- beyond it
# a bus LSOA is recorded as having no rail node, rather than borrowing the
# label of an implausibly distant station. Test A's distances are uncapped.
CATCHMENT_PRIMARY_M = 800
CATCHMENT_SENSITIVITY_M = 1200

# Charing Cross in British National Grid -- the standard London "centre"
# reference. Carried through as the centrality control, not as a finding.
CENTRE_EASTING = 530034.0
CENTRE_NORTHING = 180381.0

RANDOM_SEED = 42
N_PERMUTATIONS = 9999

CRS_BNG = "EPSG:27700"
CRS_WGS84 = "EPSG:4326"

# Cluster names. Rail names/direction readings are the corrected ones (see
# rq3_mismatch_analysis/src/run_rq1_cluster_check.py, fixed 2026-07-30 -- the
# first-pass versions had the entry/exit direction backwards for C0, C2, C3).
# direction_balance = (entry - exit) / total: POSITIVE = entry/departure
# dominant (a night ORIGIN), NEGATIVE = exit/arrival dominant (a night
# DESTINATION).
# --- rail cluster names: loaded, never hardcoded -----------------------------
# These were three hardcoded dicts in three folders until 2026-08-01. GMM
# component ids are arbitrary, so the window change renumbered every cluster
# and invalidated all three at once -- silently, because each kept running and
# kept attaching a plausible name to the wrong cluster. Two of the names were
# also wrong before the renumbering ("airport & major terminus hub" for a
# 12-station group of which only four are airports; "secondary DLR/inner mixed"
# for the cluster whose defining property is night persistence).
#
# numbat_all_area_test/src/09_cluster_names.py now derives the names from the
# data and asserts each against a machine-checkable claim before writing them.
RAIL_CLUSTER_NAMES_FILE = (
    FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_cluster_names.csv"
)


def _load_rail_cluster_names(path=RAIL_CLUSTER_NAMES_FILE):
    import pandas as pd

    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Run numbat_all_area_test/src/09_cluster_names.py; "
            "cluster names must not be reintroduced by hand."
        )
    table = pd.read_csv(path)
    return {int(r.cluster): str(r.name_en) for r in table.itertuples()}


RAIL_CLUSTER_NAMES = _load_rail_cluster_names()

# Bus went through the same fix on 2026-08-02: rq1_bus_stoparea_clustering/
# src/06_cluster_names.py now derives bus cluster names from the data the
# same way 09_cluster_names.py does for rail, and asserts each against a
# machine-checkable claim. Bus has not been refit since these names were
# first hardcoded, so nothing was numerically wrong -- but three separate
# hardcoded copies (here, rq2_independent_variables, rq3_mismatch_analysis)
# were the same latent risk rail already hit once.
BUS_CLUSTER_NAMES_FILE = (
    FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "data" / "bus_cluster_names.csv"
)


def _load_bus_cluster_names(path=BUS_CLUSTER_NAMES_FILE):
    import pandas as pd

    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Run rq1_bus_stoparea_clustering/src/"
            "06_cluster_names.py; cluster names must not be reintroduced by hand."
        )
    table = pd.read_csv(path)
    return {int(r.cluster): str(r.name_en) for r in table.itertuples()}


BUS_CLUSTER_NAMES = _load_bus_cluster_names()

# --- map styling ---
# Copied verbatim from rq1_bus_stoparea_clustering/src/config.py so the bus
# clusters keep the same colours the user and Clara have already seen on the
# bus maps. Copied rather than imported to avoid a cross-folder sys.path hack;
# if that folder's palette ever changes, this must be updated to match.
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
# The two non-cluster states must never share a fill -- "has night demand but
# below the retention threshold" and "no StopArea point falls inside this
# polygon" mean different things, and collapsing them was a real map bug fixed
# on 2026-07-29.
LOW_FLOW_FACE = "#6e6e6e"
NO_STOP_FACE = "#ffffff"
NO_STOP_HATCH = "///"
NO_STOP_EDGE = "#000000"
NO_STOP_EDGE_WIDTH = 0.15
LOW_FLOW_LABEL = "Low night flow, excluded"
NO_STOP_LABEL = "No stop point within LSOA"
RAIL_POINT_FACE = "#111111"
RAIL_POINT_EDGE = "#ffffff"

OUTPUTS = ROOT / "outputs"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
REPORT_OUT = OUTPUTS / "report"

for directory in (DATA_OUT, FIGURE_OUT, REPORT_OUT):
    directory.mkdir(parents=True, exist_ok=True)


# --- resolving the night-persistent bus cluster ------------------------------
# Until 2026-08-01 `03_distance_band_profile.py` hardcoded `bus_cluster == 1`
# to mean the night-persistent cluster. GMM component ids are arbitrary, so on
# any refit that line kept running and kept printing a plausible percentage for
# whatever cluster happened to be numbered 1 -- a silent failure in this
# folder's headline statistic. It is now resolved from the cluster profile.
#
# Operational definition: the cluster with the highest mean post-midnight share
# of activity. On the adopted bus result this is cluster 1 (0.135, against
# 0.114 / 0.089 / 0.059), so behaviour is unchanged -- but it now follows the
# data instead of an id.
NIGHT_PERSISTENT_METRIC = "post_midnight_share"
NIGHT_PERSISTENT_MIN_MARGIN = 0.01


def resolve_night_persistent_cluster(metrics):
    """Return the id of the night-persistent bus cluster, or raise if unclear.

    `metrics` is bus_unit_metrics.csv as a DataFrame (needs `cluster` and
    NIGHT_PERSISTENT_METRIC). Raises when the top two clusters are within
    NIGHT_PERSISTENT_MIN_MARGIN, because in that case "the night-persistent
    cluster" is not a well-defined object and the analysis should stop rather
    than pick one.
    """
    ranked = (
        metrics.groupby("cluster")[NIGHT_PERSISTENT_METRIC].mean().sort_values(ascending=False)
    )
    if len(ranked) < 2:
        raise RuntimeError("Need at least two bus clusters to resolve.")
    margin = float(ranked.iloc[0] - ranked.iloc[1])
    if margin < NIGHT_PERSISTENT_MIN_MARGIN:
        raise RuntimeError(
            f"Night-persistent cluster is ambiguous: top two {NIGHT_PERSISTENT_METRIC} "
            f"means differ by {margin:.4f} (< {NIGHT_PERSISTENT_MIN_MARGIN}). "
            f"Ranking: {ranked.round(4).to_dict()}"
        )
    return int(ranked.index[0]), ranked
