"""Configuration for the independent socio-economic variable lens.

WHY THIS FOLDER EXISTS
Until now RQ2's external context has been carried entirely by *composite*
classifications -- LNWC (7 groups), LOAC (7 Supergroups) and the single overall
IMD score. That is a real methodological exposure: the project's own reference
paper (Peiret-Garcia, Kimani & Suel, "Beyond the Commute", FYP/参考文献/
BtC_paper.pdf) explicitly criticises exactly this move, arguing that using
"predetermined composite classifications rather than testing specific variables
with statistical methods restricts the ability to identify which particular
demographic, socioeconomic, employment, or urban form factors drive
associations". Clara is an author on that paper. This folder tests specific
variables so that criticism cannot be aimed at this dissertation.

It does not replace the composite lenses -- they stay. This is an added layer.

VARIABLE SELECTION (updated by user decision 2026-08-07)
Chosen to serve the dissertation's actual spine -- "night travel differences
correspond to night-time economic function and community type rather than a
general poverty gradient" -- not to replicate BtC's full four-theme framework.

Free (already in the project, IoD2025 File_7, native LSOA 2021):
  income, employment, education, health, living_environment   -- IMD domains
  population_density                                          -- derived

Downloaded (ONS Census 2021, LSOA level):
  no_car_household_share      -- back in ANALYSIS_VARIABLES as of 2026-08-08;
                                 see the RE-ADDED note below for why.
  night_industry_share        -- TS060/TS061. Accommodation & food + human
                                 health & social work + transport & storage.
                                 The *residence-side* counterpart to LNWC,
                                 which is workplace-side (night-worker footfall
                                 + night-economy business registry). Having
                                 both is what lets the entry/exit direction
                                 finding (rail direction_balance, epsilon²
                                 =0.526 as of the 2026-08-02 padded-window
                                 refit -- check rq2_new_clusters_analysis/
                                 outputs/data/rail_cluster_metric_significance.csv
                                 if this drifts again) be read as
                                 origin-vs-destination rather than just
                                 asserted.

Downloaded (OS Points of Interest, June 2026):
  log1p_poi_count             -- facility intensity, log-transformed after the
                                 mode-specific LSOA/catchment aggregation.
  shannon_group               -- unnormalised Shannon H across the nine top-level
                                 OS POI Groups, following the BtC definition.

RE-ADDED 2026-08-08 (user decision, after the 2026-08-07 removal above was
found to conflict with the 2026-08-05 RQ finalisation's Discussion payload):
  no_car_household_share      -- back in ANALYSIS_VARIABLES. It is the single
                                 strongest discriminator in both modes (bus
                                 eps2=0.216, rail eps2=0.420 as of 2026-08-08)
                                 and is the measured fact the "fewest private
                                 alternatives at night" vulnerability argument
                                 in the Discussion is built on (McArthur, Robin
                                 & Smeds anchor). Removing it left that
                                 argument's chain broken.
  age_20_34_share              -- added alongside it as a corroborating,
                                 independently-sourced (TS007B, not TS045)
                                 variable pointing at the same "young, carless"
                                 profile -- not for extra discriminating power
                                 (Spearman rho with no_car_household_share is
                                 0.815 bus / 0.893 rail, near-redundant, and its
                                 own eps2 is lower in both modes: bus 0.172,
                                 rail 0.366). BtC pairs Age65+ and car
                                 ownership the same way -- as two separate
                                 per-cluster t-tested variables, with no
                                 collinearity correction -- because their (and
                                 our) per-cluster method tests each variable
                                 independently rather than fitting a joint
                                 model, so correlated variables are corroborating
                                 evidence, not a violated assumption. BtC's own
                                 age variable is the 65+ band, not a young-age
                                 one; the 20-34 band was chosen here instead
                                 because it is what the vulnerability narrative
                                 needs. The other three TS007B bands
                                 (age_0_19_share, age_35_64_share,
                                 age_65plus_share) stay appendix-only.

DELIBERATELY EXCLUDED
  * BRES workplace employment -- genuinely redundant with LNWC's business
    -registry dimension. BtC uses it; we already have that side covered.
  * Crime and Barriers-to-Housing IMD domains -- not in the user's chosen set,
    but they cost nothing extra to add (same source file). Flip them on in
    IMD_DOMAINS below if wanted; Crime is arguably the most night-specific of
    the free domains given the safety strand in the night-mobility literature.

POPULATION DENSITY IS A CONTROL, NOT A FINDING
Report it, but do not read a strong bus association as a result: the bus
clustering is itself heavily activity-volume driven (activity epsilon² ~0.56),
and activity volume is near-mechanically related to density. Its job is to let
the write-up say how much of the LNWC/LOAC/other associations is just density.
"""

from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

# --- IoD 2025, full domain file (native LSOA 2021, 33,755 rows nationally;
# all 3,372 fitted bus LSOAs and all 4,994 London LSOAs match 1:1) ---
IMD_FULL = (
    FYP / "IMDdata_2025"
    / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)
IMD_LSOA_COLUMN = "LSOA code (2021)"

# Source column -> short name. Order here is the order used in every table and
# figure. Comment out or extend freely; nothing downstream hardcodes the list.
IMD_DOMAINS = {
    "Income Score (rate)": "imd_income",
    "Employment Score (rate)": "imd_employment",
    "Education, Skills and Training Score": "imd_education",
    "Health Deprivation and Disability Score": "imd_health",
    "Living Environment Score": "imd_living_env",
    # "Crime Score": "imd_crime",
    # "Barriers to Housing and Services Score": "imd_barriers",
}
IMD_POPULATION_COLUMN = "Total population: mid 2022"

# --- Census 2021 + BRES downloads (see data/README.md for provenance) ---
#
# DOWNLOAD_SPEC drives 00_download_census.py declaratively. Each entry names a
# Nomis dataset, its cell dimension, the output filename, and the derived
# variables as {output_name: [category label substrings to sum]}. Labels are
# matched as substrings and every match is asserted unique, so a change to
# Nomis's wording fails loudly instead of silently summing the wrong cells.
#
# Denominators differ by table and are stated per entry -- this matters. LSOAs
# are drawn to hold a similar RESIDENT population, so any residence-based
# denominator (residents, households, employed residents) is near-constant
# across London (CV ~0.2) and the resulting shares are stable everywhere. A
# workplace denominator has no such property: BRES jobs per LSOA run 0 to
# 412,000 (CV 6.4), so job shares are unstable in the ~40% of LSOAs with under
# 250 jobs. That is why BRES is stored with BOTH a share and a per-km2 density
# (the density sidesteps the volatile denominator entirely). Which one becomes
# the analysis variable is still open as of 2026-07-31.
CENSUS_DIR = ROOT / "data"
CENSUS_CAR = CENSUS_DIR / "ts045_car_van_availability_lsoa.csv"
CENSUS_INDUSTRY = CENSUS_DIR / "ts060_industry_lsoa.csv"
CENSUS_TENURE = CENSUS_DIR / "ts054_tenure_lsoa.csv"
CENSUS_DEPRIVATION = CENSUS_DIR / "ts011_household_deprivation_lsoa.csv"

# TS011 household deprivation. Added 2026-07-31 for one specific reason: this is
# the EXACT measure both reference works use -- BtC ("percentage of households
# deprived in at least one dimension according to the Census 2021 deprivation
# classification") and Kimani's MSc dissertation (which states it was used "to
# simulate income and poverty levels due to the lack of a highly granular
# dataset"). Computing it ourselves makes the comparison with them direct rather
# than by analogy.
#
# Its four dimensions are education, employment, health/disability and HOUSING
# (overcrowded, or a shared dwelling, or no central heating). That bundling is
# the point: our IoD decomposition finds the economic domains weak and Living
# Environment strong, so if TS011 lands closer to Living Environment than to
# IoD income/employment, the bundled housing component is the likely carrier of
# the deprivation signal those papers report. If instead TS011 is weak too, that
# reconciliation fails and the divergence has to be explained some other way
# (mode coverage, night-only design). Either outcome is informative.
#
# CAVEAT: TS011 is broken down by HOW MANY dimensions a household is deprived
# in, not by WHICH. So it cannot isolate housing on its own -- the test above is
# indirect, and the write-up must say so.
DEPRIVATION_LEVELS = {
    "deprived_1plus_share": [
        "Household is deprived in one dimension",
        "Household is deprived in two dimensions",
        "Household is deprived in three dimensions",
        "Household is deprived in four dimensions",
    ],
    "deprived_2plus_share": [
        "Household is deprived in two dimensions",
        "Household is deprived in three dimensions",
        "Household is deprived in four dimensions",
    ],
}

# Tenure: private and social rented shares only. "Owned" is deliberately
# omitted -- the three are compositionally constrained (they sum to ~1 with
# shared ownership), so including all three adds a redundant, collinear column.
# The two kept capture genuinely different populations: private renting picks up
# young, mobile, service-sector residents; social renting picks up lower-income
# long-term ones. Added 2026-07-31 after reading Kimani's MSc dissertation
# (FYP/参考文献/24114779_MSc_Dissertation.pdf, same supervisors), which uses
# TS054 and is the closest methodological precedent in this project's lineage.
TENURE_CATEGORIES = {
    "Private rented": "private_rented_share",
    "Social rented": "social_rented_share",
}

# Residence-side industry aggregates, split along the leisure-vs-labour axis
# Clara asked about on 2026-07-28 ("whether some people are out just for
# leisure, but other people will be out for work").
#
# HISTORY -- this replaces a hand-picked 3-section aggregate (accommodation &
# food + human health & social work + transport & storage) that was wrong in
# two ways, found 2026-08-01 by testing all 18 sections individually:
#   * it KEPT health & social work, whose correlation with deep-night bus
#     activity is only +0.138 -- among the weakest positives, not a driver;
#   * it DROPPED administrative & support services (+0.384, the strongest of
#     all) purely because security, which LNWC's own night-industry list names,
#     could not be isolated from that section; and retail (+0.326) and
#     construction (+0.245).
#
# The fix is NOT to reselect on those correlations -- choosing predictors by
# their association with the outcome is circular and indefensible. Instead the
# split below uses two external, non-circular criteria:
#   1. Membership of LNWC's night-industry list (Mavrogeni et al., derived from
#      a Night Worker Survey): health, hospitality, manufacturing, public
#      services, retail, security, transport.
#   2. WEEKEND behaviour, which is independent of the deep-night outcome:
#      accommodation & food is the only section with a substantial positive
#      weekend correlation (+0.253); transport, admin/support and retail are
#      flat or negative. That is the empirical signature of leisure-serving
#      work versus shift work, and it is what makes the split defensible.
HOSPITALITY_SECTIONS = ["I Accommodation and food service activities"]
SHIFTWORK_SECTIONS = [
    "H Transport and storage",
    "N Administrative and support service activities",
    "G Wholesale and retail trade; repair of motor vehicles and motor cycles",
]

CENSUS_ETHNICITY = CENSUS_DIR / "ts021_ethnicity_lsoa.csv"
CENSUS_HOUSEHOLD = CENSUS_DIR / "ts003_household_composition_lsoa.csv"
CENSUS_AGE = CENSUS_DIR / "ts007b_age_bands_lsoa.csv"
CENSUS_ECONOMIC = CENSUS_DIR / "ts066_economic_activity_lsoa.csv"
BRES_INDUSTRY = CENSUS_DIR / "bres2024_industry_sections_lsoa.csv"

DOWNLOAD_SPEC = [
    {
        "table": "TS045", "dataset": "NM_2063_1", "dimension": "C2021_CARS_5",
        "path": CENSUS_CAR, "total": "Total: All households",
        "note": "denominator = households",
        "variables": {"no_car_household_share": ["No cars or vans in household"]},
    },
    {
        "table": "TS011", "dataset": "NM_2031_1", "dimension": "C2021_DEP_6",
        "path": CENSUS_DEPRIVATION, "total": "Total: All households",
        "note": "denominator = households; the measure BtC and Kimani both use",
        "variables": {
            "deprived_1plus_share": [
                "deprived in one dimension", "deprived in two dimensions",
                "deprived in three dimensions", "deprived in four dimensions",
            ],
            "deprived_2plus_share": [
                "deprived in two dimensions", "deprived in three dimensions",
                "deprived in four dimensions",
            ],
        },
    },
    {
        "table": "TS054", "dataset": "NM_2072_1", "dimension": "C2021_TENURE_9",
        "path": CENSUS_TENURE, "total": "Total: All households",
        "note": "denominator = households; 'Owned' omitted (compositionally redundant)",
        "variables": {
            "private_rented_share": ["Private rented"],
            "social_rented_share": ["Social rented"],
        },
        "exact": True,  # headline rows only -- the table also carries sub-breakdowns
    },
    {
        "table": "TS021", "dataset": "NM_2041_1", "dimension": "C2021_ETH_20",
        "path": CENSUS_ETHNICITY, "total": "Total: All usual residents",
        "note": "denominator = residents; the two groups BtC reports",
        "variables": {
            "asian_share": ["Asian, Asian British or Asian Welsh"],
            "black_share": ["Black, Black British, Black Welsh, Caribbean or African"],
        },
        "exact": True,
    },
    {
        "table": "TS003", "dataset": "NM_2023_1", "dimension": "C2021_HHCOMP_15",
        "path": CENSUS_HOUSEHOLD, "total": "Total: All households",
        "note": "denominator = households",
        "variables": {
            # Summed across every family type, matching Kimani's "households that
            # have dependent children living with them".
            "dependent_children_share": [
                "Single family household: Married or civil partnership couple: Dependent children",
                "Single family household: Cohabiting couple family: With dependent children",
                "Single family household: Lone parent family: With dependent children",
                "Other household types: With dependent children",
            ],
            "lone_parent_dependent_share": [
                "Single family household: Lone parent family: With dependent children",
            ],
            "one_person_share": ["One-person household"],
        },
        # Exact: this table nests headline rows above their own sub-breakdowns
        # ("One-person household" also prefixes ": Aged 66 and over" and
        # ": Other"), so substring matching would double-count.
        "exact": True,
    },
    {
        "table": "TS007B", "dataset": "NM_2018_1", "dimension": "C2021_AGE_12A",
        "path": CENSUS_AGE, "total": "Total",
        "note": "denominator = residents; four bands matching Kimani's aggregation. "
                "The four sum to 1 -- compositionally constrained, relevant when "
                "reading the correlation matrix.",
        "variables": {
            "age_0_19_share": ["Aged 4 years and under", "Aged 5 to 9 years",
                               "Aged 10 to 15 years", "Aged 16 to 19 years"],
            "age_20_34_share": ["Aged 20 to 24 years", "Aged 25 to 34 years"],
            "age_35_64_share": ["Aged 35 to 49 years", "Aged 50 to 64 years"],
            "age_65plus_share": ["Aged 65 to 74 years", "Aged 75 to 84 years",
                                 "Aged 85 years and over"],
        },
        "exact": True,
    },
    {
        "table": "TS066", "dataset": "NM_2083_1", "dimension": "C2021_EASTAT_20",
        "path": CENSUS_ECONOMIC, "total": "Total: All usual residents aged 16 years and over",
        "note": "denominator = residents 16+. Self-employment and part-time originally chosen "
                "over an unemployment rate to avoid duplicating IoD's Employment Deprivation "
                "domain -- added back 2026-08 on user decision (unemployed_share below); the "
                "duplication risk is real (rho with imd_employment not yet checked here) and "
                "should be read off the correlation matrix once rebuilt, not assumed away.",
        "variables": {
            # Both self-employment headline rows. Note Nomis writes the
            # aggregate rows WITHOUT spaces after the colons and the leaf rows
            # WITH them -- the labels below are copied verbatim.
            "self_employed_share": [
                "Economically active (excluding full-time students):In employment:Self-employed with employees",
                "Economically active (excluding full-time students):In employment:Self-employed without employees",
            ],
            # Employees only. Part-time self-employment is left out to keep this
            # a clean "works part-time for an employer" measure.
            "part_time_employee_share": [
                "Economically active (excluding full-time students): In employment: Employee: Part-time",
            ],
            # Added 2026-08, user decision: unemployment rate as a direct labour-market
            # -disadvantage measure, replacing self_employed_share in ANALYSIS_VARIABLES
            # (self_employed_share stays downloaded, just no longer in the headline set).
            # Headline row, same tree depth as "In employment" -- following this table's own
            # no-space-at-aggregate-depth convention seen above; verify against the
            # RuntimeError's printed available-categories list if this label is wrong.
            "unemployed_share": [
                "Economically active (excluding full-time students): Unemployed",
            ],
        },
        "exact": True,
    },
]

# Residence-side industry sections, kept RAW rather than merged into the
# hospitality_industry_share / shiftwork_industry_share composites above.
# Changed 2026-08, user decision: composites obscured which specific section was
# actually carrying an association. Same four sections, same selection criteria
# (LNWC night-industry list membership + weekend-behaviour independence -- see
# the HOSPITALITY_SECTIONS / SHIFTWORK_SECTIONS history comment above), just no
# longer summed together. Names match BRES_SECTIONS' naming so the residence-
# side (Census, here) and workplace-side (BRES, employment) versions of the same
# industry are directly comparable by variable-name stem.
RESIDENCE_INDUSTRY_SECTIONS = {
    "accom_food_share": "I Accommodation and food service activities",
    "transport_storage_share": "H Transport and storage",
    "admin_support_share": "N Administrative and support service activities",
    "wholesale_retail_share": "G Wholesale and retail trade; repair of motor vehicles and motor cycles",
    # Added 2026-08, user decision: cover the rest of the LNWC Night Worker
    # Survey's own 8 industry categories (Mavrogeni et al. Appendix B --
    # Arts and recreation, Health, Hospitality, Manufacturing, Public admin.
    # and defence, Retail, Security, Transport and storage). Hospitality,
    # Transport and storage, Security (via admin_support) and Retail (via
    # wholesale_retail) are already covered above, at section granularity
    # (broader than LNWC's own group-level SIC picks -- accepted, see
    # 2026-08 discussion). These three fill in Health, Manufacturing, and
    # Public admin. and defence. Arts and recreation (Section R) is NOT
    # addable this way -- ONS's LSOA-published TS060A collapses R/S/T/U into
    # one "Other" column; see CENSUS_INDUSTRY_ALL_SECTIONS's own column
    # header. Open decision, not yet resolved.
    "health_social_share": "Q Human health and social work activities",
    "manufacturing_share": "C Manufacturing",
    "public_admin_share": "O Public administration and defence; compulsory social security",
}
# Already written by 00_download_census.py (the "full 18-section composition
# (reference copy)" step) regardless of which sections end up in the composites
# above -- no re-download needed to pull the four raw shares out of it.
CENSUS_INDUSTRY_ALL_SECTIONS = CENSUS_DIR / "ts060_industry_section_shares_lsoa.csv"

# BRES 2024 (workplace-based), SIC section -> division ranges. Verified
# 2026-07-31: every division below exists in NM_189_1's codelist, values are
# published at LSOA (not suppressed), and the eight sections reproduce London's
# known employment structure (manufacturing 1.85%, professional/scientific
# 13.80%, total 5,737,530 jobs).
#
# Six sections follow BtC's own selection; Health/social work and Transport/
# storage are added because BtC's list was built for a full-day study and omits
# the two classic shift-work sectors, which a night study cannot sensibly drop.
BRES_DATASET = "NM_189_1"
BRES_SECTIONS = {
    "manufacturing": range(10, 34),
    "wholesale_retail": range(45, 48),
    "transport_storage": range(49, 54),
    "accom_food": range(55, 57),
    "info_comms": range(58, 64),
    "professional_sci": range(69, 76),
    "education": range(85, 86),
    "health_social": range(86, 89),
    # Added 2026-08, user decision: workplace-side (BRES) counterpart to
    # admin_support_share (Section N, the Security proxy) so the six LNWC-
    # aligned industries kept in ANALYSIS_VARIABLES each have a residence-side
    # AND workplace-side pair, echoing this file's own residence-vs-workplace
    # rationale (see "Why two industry sources" in data/README.md). Section N
    # is divisions 77-82; the other five BRES sections needed already existed
    # from the 2026-07-31 pull, only this one required a fresh Nomis request.
    "admin_support": range(77, 83),
}

# --- clusterings (the adopted RQ1 results, same as every other RQ2 folder) ---
RAIL_LABELS = FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
RAIL_COORDS = FYP / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"
RAIL_UNIT_METRICS = FYP / "rq2_new_clusters_analysis" / "outputs" / "data" / "rail_unit_metrics.csv"
RAIL_K = 5
EXPECTED_RAIL_UNITS = 403

BUS_LABELS = FYP / "rq1_bus_stoparea_clustering" / "outputs_1805_min33" / "clr" / "labels" / "k4_labels.csv"
BUS_K = 4
EXPECTED_BUS_UNITS = 3383

LSOA_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LSOA_BOUNDARY_CODE_COLUMN = "LSOA21CD"

# OS Points of Interest, June 2026, downloaded from EDINA Digimap on
# 2026-08-07. The licensed raw file remains in the dedicated facility sidecar;
# this pipeline derives only LSOA-level total-count and Shannon-diversity
# variables from it. These are external post-clustering context variables.
OS_POI = (
    FYP / "rq2_facility_diversity_analysis" / "data" / "source"
    / "poi_6438516" / "poi_6438516.gpkg"
)
OS_POI_LAYER = "Points of Interest 2026_06"
FACILITY_RAW_VARIABLES = ["poi_count", "shannon_group"]

# 800 m Voronoi-clipped station catchments, matching rq2_loac_analysis and
# rq2_new_clusters_analysis's 800 m sidecar.
RAIL_CATCHMENT_METRES = 800

# Rail contextual variables use an equal-weight arithmetic mean across the
# distinct LSOAs intersecting each catchment. The variables have heterogeneous
# denominators (households, residents, residents aged 16+, employed residents),
# so one generic population weight would not be denominator-consistent. The
# resulting station value describes the average intersecting LSOA context, not
# the exact population or household composition of the catchment.
CRS_BNG = "EPSG:27700"
CRS_WGS84 = "EPSG:4326"

RANDOM_SEED = 42

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
# hardcoded copies (here, bus_rail_relation_analysis, rq3_mismatch_analysis)
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

# --- composite lenses on the CURRENT clustering, read live -----------------
#
# These three numbers (LNWC Cramer's V, LOAC Cramer's V, IMD epsilon-squared)
# used to be typed as literals in three places in this folder (this module's
# own docstring, 02_run_association_tests.py's terminal printout, and
# 05_build_report.py's comparison table) and went stale together when the
# rail padded-window refit changed them on 2026-08-02. Load them from their
# source folders instead so there is nothing left to go stale.
COMPARISON_EXTERNAL_ASSOCIATION = (
    FYP / "rq2_new_clusters_analysis" / "outputs" / "data" / "comparison_external_association.csv"
)
LOAC_STATISTICAL_SUMMARY = {
    "bus": FYP / "rq2_loac_analysis" / "outputs" / "data" / "bus_loac_statistical_summary.csv",
    "rail": FYP / "rq2_loac_analysis" / "outputs" / "data" / "rail_loac_statistical_summary.csv",
}


def load_composite_associations() -> dict[str, dict[str, float]]:
    """{"bus": {"lnwc": V, "loac": V, "imd": eps2}, "rail": {...}} for the
    clustering currently in force (never the retired canonical/original row)."""
    import pandas as pd

    ext = pd.read_csv(COMPARISON_EXTERNAL_ASSOCIATION)
    out = {}
    for mode in ("bus", "rail"):
        current = ext.loc[
            (ext["mode"] == mode)
            & (~ext["clustering"].str.contains("canonical|original", case=False))
        ]
        if len(current) != 1:
            raise RuntimeError(
                f"Expected exactly one non-canonical {mode} row in "
                f"{COMPARISON_EXTERNAL_ASSOCIATION}, got {len(current)}"
            )
        row = current.iloc[0]
        loac = pd.read_csv(LOAC_STATISTICAL_SUMMARY[mode])
        loac_v = float(loac.loc[loac["cramers_v"].notna(), "cramers_v"].iloc[0])
        out[mode] = {
            "lnwc": float(row["lnwc_cramers_v"]),
            "loac": loac_v,
            "imd": float(row["imd_epsilon2"]),
        }
    return out


# --- the analysis set ---
#
# 01 still builds the full variable table (32 columns before this change; see
# data/README.md); everything downstream uses only the list below. The rest are
# kept as appendix material, not deleted.
#
# CHANGED 2026-08, user decision -- this is no longer the evidence-reduced set
# from the 2026-08-01 hierarchical clustering (that grouping is kept above in
# git history / the RESULTS.md this replaces, not restated here since the
# variable set it justified is gone). The user chose these 15 directly:
#   * imd_income -> imd_education, and imd_health added: broadens the IMD
#     domains tested beyond income, which the 2026-08-01 grouping had folded
#     into one "socio-economic disadvantage" dimension with education/health/
#     employment -- worth testing individually now rather than picking one
#     representative.
#   * deprived_1plus_share added: the exact BtC/Kimani measure (see the TS011
#     entry in DOWNLOAD_SPEC above), direct comparability with both.
#   * social_rented_share added: private_rented_share alone only captured one
#     of the two non-owner tenures.
#   * self_employed_share -> unemployed_share: a direct labour-market-
#     disadvantage measure. Correlation with imd_employment is NOT yet
#     re-checked under this variable set -- read the rebuilt correlation matrix
#     before treating both as independent evidence of the same claim.
#   * hospitality_industry_share / shiftwork_industry_share -> the four raw
#     TS060 sections (RESIDENCE_INDUSTRY_SECTIONS above) that used to be summed
#     into them. Un-merging trades a cleaner two-row story for the ability to
#     say which specific section (transport/storage vs admin/support vs
#     wholesale/retail vs accommodation/food) is actually carrying an
#     association -- these four are compositionally related (they are shares of
#     the same 18-section total) so expect some shared variance between them in
#     the correlation matrix; that is expected, not a new problem.
# population_density stays as the control. User decision 2026-08-07 removed
# no_car_household_share (over-read risk vs centre/periphery structure) and
# added log1p_poi_count / shannon_group (OS POI). User decision 2026-08-08
# reversed the no_car_household_share removal and added age_20_34_share
# alongside it -- see the RE-ADDED note near the top of this file for why.
ANALYSIS_VARIABLES = [
    "imd_education",
    "imd_health",
    "deprived_1plus_share",         # the exact BtC/Kimani measure
    "social_rented_share",
    "no_car_household_share",       # RE-ADDED 2026-08-08; strongest single discriminator both modes
    "age_20_34_share",               # RE-ADDED 2026-08-08; corroborates no_car_household_share, independent source
    "dependent_children_share",     # used by both
    "private_rented_share",
    "asian_share",                  # ethnicity, following BtC
    "black_share",                  # ethnicity, following BtC
    "unemployed_share",
    "accom_food_share",             # TS060 section I, residence side -- LNWC Hospitality
    "transport_storage_share",      # TS060 section H, residence side -- LNWC Transport & storage
    "admin_support_share",          # TS060 section N, residence side -- LNWC Security (broader proxy)
    "wholesale_retail_share",       # TS060 section G, residence side -- LNWC Retail (broader proxy)
    "health_social_share",          # TS060 section Q, residence side -- LNWC Health
    "manufacturing_share",          # TS060 section C, residence side -- LNWC Manufacturing
    "log1p_poi_count",              # OS POI activity intensity; log-transformed
    "shannon_group",                # Shannon H across the nine OS POI Groups
    "population_density",           # CONTROL, not a finding
]
# WORKPLACE-SIDE (BRES) TRIAL, 2026-08 -- tested and reverted, finding kept.
# The six residence-side LNWC industries above were each paired with a BRES
# workplace-side twin (bres_accom_food_share, bres_transport_storage_share,
# bres_admin_support_share, bres_wholesale_retail_share,
# bres_health_social_share, bres_manufacturing_share; admin_support's BRES
# pull, divisions 77-82, was new -- the other five already existed) and run
# through the full pipeline. Result: residence-side eps^2 exceeded workplace-
# side for every industry except health_social on rail (bres 0.108 vs
# residence 0.092), and at cluster level workplace-side variables were only
# ever the LEADING signal for rail C1 "atypical temporal profile" (n=12) --
# every other cluster's top cells stayed residence-side even for the
# arrival-dominant clusters (C3, C4) where a workplace/destination story
# would have predicted otherwise. Reading: "arrival-dominant" at a station
# more often means passengers arriving HOME than arriving AT WORK -- this
# project has no OD/trip-chain data to confirm destinations directly, and the
# residence-side dominance is the closest indirect evidence available.
# Practical consequence: keep BRES as a rebuild-if-needed appendix
# (BRES_SECTIONS.admin_support stays downloaded), not in the headline
# ANALYSIS_VARIABLES -- workplace-side did not earn a place as a second
# primary lens, it reinforced residence-side as the right primary lens
# instead. This also reinforces the rail C0 "night-persistent inner & DLR"
# reading: high social_rented/unemployed/imd_health/imd_education
# (deprivation) alongside high accom_food_share/admin_support_share
# (RESIDENCE-side hospitality/security industry) means the people living in
# that catchment work in night-adjacent industries -- not merely that
# night-economy businesses happen to cluster near the station. Combined with
# C0's own night-persistence and early-departure timing signal and its
# population density (18,244/km^2, the highest of any rail cluster --
# unambiguously inner, not outer), this reads as a potential inner/middle-
# ring disadvantaged night-worker residential zone, a genuinely different
# story from the outer, family, high-shiftwork-industry, car-owning profile
# of C3.
# LNWC's 8th category, Arts and recreation (Section R), has no section-level
# variable here -- ONS collapses R/S/T/U into one "Other" column in the
# LSOA-published TS060A table, and no clean isolation is possible from this
# data source. User decision 2026-08: do not add it (ruled out both the noisy
# R+S+T+U merge and a BRES workplace-side substitute). Coverage of LNWC's 8
# categories is 6/8 in ANALYSIS_VARIABLES (Public admin. and defence also
# excluded, residence-side only, by a separate 2026-08 decision) -- state
# this plainly if the write-up lists which LNWC categories are represented.

# Cluster colours. These are now mode-specific: the bus palette was changed to a
# red-cyan-blue family on 2026-08-03 (copied verbatim from
# rq1_bus_stoparea_clustering/src/config.py so figures here match the bus maps),
# while rail keeps the original Okabe-Ito set because its maps were not part of
# that change. Keeping them distinct also stops a shared palette implying that
# bus C1 and rail C1 are the same kind of cluster -- they are not.
BUS_CLUSTER_COLOURS = [
    "#4C93D3",  # 0 mid blue
    "#D1284B",  # 1 red
    "#00A6A6",  # 2 teal cyan
    "#1B3A6B",  # 3 deep navy
    "#F2A2AC",  # 4 rose
    "#7FCFCB",  # 5 pale cyan
    "#8C1327",  # 6 dark red
    "#A9C7E8",  # 7 pale blue
]
RAIL_CLUSTER_COLOURS = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#D55E00",  # vermillion
    "#F0E442",  # yellow
    "#785EF0",  # violet
]


def cluster_colours(mode: str) -> list[str]:
    """Palette for one mode. Raises on an unknown mode rather than defaulting."""
    if mode == "bus":
        return BUS_CLUSTER_COLOURS
    if mode == "rail":
        return RAIL_CLUSTER_COLOURS
    raise ValueError(f"Unknown mode {mode!r}; expected 'bus' or 'rail'.")

OUTPUTS = ROOT / "outputs"
DATA_OUT = OUTPUTS / "data"
FIGURE_OUT = OUTPUTS / "figures"
REPORT_OUT = OUTPUTS / "report"

for directory in (DATA_OUT, FIGURE_OUT, REPORT_OUT, CENSUS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
