"""Configuration for the RQ3 night-time PT-vs-OD mismatch analysis.

Independent, non-destructive analysis folder. Does not modify any RQ1/RQ2
input or output. See ../README.md for the full method specification.
"""

from pathlib import Path

HERE = Path(__file__).resolve()
RQ3_ROOT = HERE.parents[1]
FYP = HERE.parents[2]

# ---------------------------------------------------------------------------
# Inputs (read-only, owned by other parts of the project)
# ---------------------------------------------------------------------------
OD_FLOWS = FYP / "OD Flows 数据" / "interactions_by_msoa_pair_and_time_2019_directional.csv"

# Repointed 2026-08 to current-canonical PT sources (the previous paths were
# 2026-07-11 vintage: 270-station LU-only rail, stop-level pre-StopArea bus --
# both predate the rail all-modes extension and the bus StopArea migration,
# so msoa_mismatch_scores.csv etc. were resting on data that no longer matches
# the RQ1 clustering used everywhere else in the dissertation).
RAIL_QHR = (
    FYP / "data_processing" / "rail_allmodes" / "outputs" / "preprocessed"
    / "numbat_allmodes_station_qhr_all_daytypes_final.parquet"
)
# NOTE: this file's station-id column is named "unit", not "NLC" -- rename
# after reading (see build_msoa_panels.py).
RAIL_COORDS = FYP / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"

# Already aggregated to LSOA x hour x day_type x direction (boardings/
# alightings) -- the StopArea aggregation happens upstream of this file, so
# BUS_STOP_LSOA (a stop-level lookup) is no longer needed anywhere in this
# folder; the old stop-level BUS_QHR/BUS_STOP_LSOA pair is retired.
BUS_LSOA_HOURLY = (
    FYP / "data_processing" / "bus_stoparea" / "outputs" / "preprocessed"
    / "bus_lsoa_night_long.parquet"
)

LSOA_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LONDON_LAD_LOOKUP = FYP / "IMDdata" / "ons_lsoa11_lsoa21_lad22_london_lookup.csv"

# For run_shiftwork_corridor_check.py: raw TS060 industry section shares (all
# London LSOAs) and IoD2025's population denominator, both already downloaded
# by rq2_independent_variables -- read only, not modified, per this folder's
# own "does not touch RQ1/RQ2 input or output" rule.
TS060_INDUSTRY_SECTIONS = (
    FYP / "rq2_independent_variables" / "data" / "ts060_industry_section_shares_lsoa.csv"
)
IMD_POPULATION = (
    FYP / "IMDdata_2025"
    / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)
IMD_POPULATION_LSOA_COLUMN = "LSOA code (2021)"
IMD_POPULATION_COLUMN = "Total population: mid 2022"

# Bus cluster labels (StopArea CLR K=4), used only by run_rq1_cluster_check.py
# to test the mismatch residual against RQ1's OWN typology -- distinct from
# LNWC_LSOA below, which is genuine external LNWC classification data. These
# two used to be the same variable (BUS_LSOA_LNWC), which was correct for this
# use and wrong for the other -- split 2026-08 so neither can be misused again.
BUS_CLUSTER_LABELS = FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "clr" / "labels" / "k4_labels.csv"

# Real LNWC classification, LSOA21 x lnc_grp (1-7). Fixed 2026-08: this used to
# point at rq1_bus_stoparea_clustering's bus CLUSTER labels file (columns
# lsoa/cluster, no lnc_grp or lsoa21cd at all -- dominant_lnwc_per_msoa() in
# run_mismatch_analysis.py would KeyError on it). That was a copy-paste
# leftover from an earlier version of this variable that genuinely was about
# bus clusters; the equity-closing step has always needed actual LNWC data,
# which lives here, matching rq2test analysis/src/config.py's LNWC path.
LNWC_LSOA = FYP / "night_time_work_data" / "london_night_workers_classification_data.csv"

# ---------------------------------------------------------------------------
# This folder's own data/outputs
# ---------------------------------------------------------------------------
DATA_DIR = RQ3_ROOT / "data"
MSOA_LOOKUP = DATA_DIR / "lsoa21_msoa21_lad22_london.csv"

OUTPUTS = RQ3_ROOT / "outputs"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
REPORT_OUT = OUTPUTS / "report"

for directory in (DATA_DIR, DATA_OUT, FIGURE_OUT, REPORT_OUT):
    directory.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# ONS Open Geography Portal source for the LSOA21-MSOA21-LAD22 lookup
# ---------------------------------------------------------------------------
ONS_OA_LSOA_MSOA_LAD_SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "OA_LSOA_MSOA_EW_DEC_2021_LU_v3/FeatureServer/0/query"
)
ONS_MSOA11_MSOA21_SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "MSOA_(2011)_to_MSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_EW_v2/"
    "FeatureServer/0/query"
)
ONS_SOURCE_NOTE = (
    "ONS Open Geography Portal item b9ca90c10aaa4b8d9791e9859a38ca67: "
    "'Output Area (2021) to LSOA to MSOA to LAD (December 2021) Exact Fit "
    "Lookup in EW (V3)'. Queried for OA21CD/LSOA21CD/MSOA21CD/LAD22CD, "
    "filtered to the 33 Greater London LAD22CD codes used elsewhere in this "
    "project (IMDdata/ons_lsoa11_lsoa21_lad22_london_lookup.csv), then "
    "de-duplicated down to one row per LSOA21CD (dropping the OA level). "
    "The OD flow data (config.OD_FLOWS) is keyed by 2011 MSOA codes, so this "
    "is joined against ONS item 94b5259bdd5e4216b8b70c2a79932312 ('MSOA "
    "(2011) to MSOA (2021) to LAD (2022) Exact Fit Lookup for EW (V2)') to "
    "add an MSOA11CD column per LSOA21CD. Rows where the MSOA21->MSOA11 "
    "relationship is a split/merge (CHNGIND != 'U') keep all matching MSOA11 "
    "candidates; see the audit log for how many LSOAs this affects."
)

# ---------------------------------------------------------------------------
# Design constants (see README.md "Design decisions")
# ---------------------------------------------------------------------------
NIGHT_HOURS = list(range(18, 24)) + list(range(0, 6))  # 18:00-06:00
RAIL_DAY_TYPE = "TWT"       # weekday-representative slice; OD has no day-type split
BUS_DAY_TYPE = "Weekday"    # weekday-representative slice

RANDOM_SEED = 42

LNWC_NIGHT_WORKER_DENSE_GROUPS = {1, 2, 3}  # per lnwc_group_lookup.csv descriptions
LNWC_PERIPHERY_GROUP = 7
