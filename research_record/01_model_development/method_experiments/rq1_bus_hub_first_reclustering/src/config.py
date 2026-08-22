from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FYP = ROOT.parent
UPSTREAM = FYP / "rq1_bus_hub_first_reorganisation"
OLD_FULLWEEK = FYP / "cluster_clean_version_fullweek"

LONG_INPUT = UPSTREAM / "outputs" / "preprocessed" / "bus_lsoa_night_long.parquet"
EXCEPTION_INPUT = UPSTREAM / "outputs" / "data" / "one_direction_exception_areas.csv"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

OUT = ROOT / "outputs"
FEATURES = OUT / "features"
DIAGNOSTICS = OUT / "diagnostics"
LABELS = OUT / "labels"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
MODELS = OUT / "models"
for path in (OUT, FEATURES, DIAGNOSTICS, LABELS, FIGURES, REPORT, MODELS):
    path.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
HOURS = list(range(1080, 1800, 60))

K_RANGE = list(range(2, 13))
PROFILE_K = list(range(2, 9))
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
BOOTSTRAP_N_INIT = 3
REG_COVAR = 1e-6
MAX_ITER = 300
RANDOM_STATE = 42
