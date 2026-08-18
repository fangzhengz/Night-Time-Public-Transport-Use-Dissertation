"""Does the RQ3 mismatch score relate to RQ1's own usage typology?

The main mismatch analysis interprets residuals only against the external
LNWC classification. This was a real design gap: RQ1's own clustering (the
dissertation's primary contribution -- rail hub/residential/CBD/night-economy
types; bus persistent/high-flow/suburban-low-flow types) was never checked
against the RQ3 gap at all. This script closes that loop, reusing labels
already computed in rq2test analysis/ and the MSOA geography already built
in this folder -- no new preprocessing.

Rail clusters are station-level (NLC); aggregated to MSOA11 by dominant
(mode) cluster among the stations in that MSOA (most MSOAs with rail have
only one station, so this is usually unambiguous). Bus clusters are
LSOA21-level; aggregated to MSOA11 by dominant cluster among LSOAs, same
method already used for dominant_lnwc.

Does not touch any RQ1/RQ2 input or output. See ../README.md.
"""

import logging

import numpy as np
import pandas as pd

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# 2026-07-30: repointed from canonical (270-station Underground-only, K=5) to
# the all-modes NaPTAN-matched 403-station refit, K=5 -- rerun after the
# Paddington NR/TfL co-location correction on 2026-08-07 and promoted to the
# primary RQ1 rail result this same day after a full K=5 vs K=6 and K=5 vs K=7
# bootstrap/seed stability battery (see numbat_all_area_test/outputs/report/).
RAIL_CLUSTER_LABELS = config.FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
BUS_CLUSTER_LABELS = config.BUS_CLUSTER_LABELS  # StopArea CLR K=4, see config.py

# Both dicts are hand-written descriptive labels (not derived by any formula),
# same convention as the canonical names they replace. Rail: drafted 2026-07-30
# from rail_allmodes_k5_labels.csv joined to station names/modes (see
# numbat_all_area_test/outputs/data/rail_allmodes_coords.csv) plus the existing
# rail_allmodes_k5_profiles.png / _map.png. Bus: drafted the same day from
# rq1_bus_stoparea_clustering/outputs/clr/features/sample_metrics.csv joined to
# labels/k4_labels.csv, plus figures/{map,profiles}_k4.png. Both are first-pass
# interpretations, not reviewed/finalised -- RQ3 itself is a deprioritised RQ
# (2026-07-17 meeting), so this is included for consistency, not as a polished
# result to cite directly.
# Direction convention (verified 2026-07-30 against
# data_processing/rail_allmodes/src/01_preprocess_rail_allmodes.py, which reads
# the TfL "Station_Entries"/"Station_Exits" sheets straight through with no
# sign flip): direction_balance = (entry - exit) / total, so POSITIVE = entry/
# departure-dominant (a night ORIGIN -- people tap in and leave from here) and
# NEGATIVE = exit/arrival-dominant (a night DESTINATION -- people tap out and
# arrive here). Cluster means run C0 -0.475 < C3 -0.326 < C1 -0.166 < C2 +0.070
# < C4 +0.172 (rq2_new_clusters_analysis/outputs/data/rail_cluster_metric_
# summary.csv). The first-pass comments below had this backwards for C0, C2 and
# C3 -- corrected 2026-07-30; the mean is quoted inline now so the claim and the
# evidence cannot drift apart again.
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
    config.FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_cluster_names.csv"
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
BUS_CLUSTER_NAMES = {
    0: "C0 moderate-flow, directional",  # n=610 (18.1%): activity med=506, post_midnight_persistence=0.127, direction_balance=-0.193 (one-directional)
    1: "C1 high-flow, night-persistent",  # n=1145 (34.0%, largest): activity med=2605 (~5x C0), post_midnight_persistence=0.212 (highest), most balanced direction (-0.086)
    2: "C2 moderate-to-high flow",  # n=1058 (31.4%): activity med=624, second on every metric after C1
    3: "C3 low-flow, peripheral-leaning",  # n=559 (16.6%, smallest): activity med=244 (lowest), post_midnight_persistence=0.082 (lowest), map shows a weak outer-borough lean vs C1's central concentration
}


def mode_or_nan(s: pd.Series):
    m = s.mode()
    return m.iloc[0] if not m.empty else np.nan


def dominant_rail_cluster_per_msoa() -> pd.DataFrame:
    # rail_allmodes_k5_labels.csv uses "unit" for the station id, not "NLC".
    rail = pd.read_csv(RAIL_CLUSTER_LABELS).rename(columns={"unit": "NLC"})[["NLC", "cluster"]]
    rail["NLC"] = rail["NLC"].astype(str)
    lookup = pd.read_csv(config.MSOA_LOOKUP, usecols=["LSOA21CD", "MSOA11CD"])

    # station_to_msoa11 isn't persisted by build_msoa_panels.py -- rebuild the
    # same point-in-polygon join rather than duplicate it into a saved file.
    import geopandas as gpd
    # rail_allmodes_coords.csv also uses "unit", not "NLC" -- see config.py's
    # RAIL_COORDS comment.
    coords = pd.read_csv(config.RAIL_COORDS).rename(columns={"unit": "NLC"})
    coords["NLC"] = coords["NLC"].astype(str)
    stations = gpd.GeoDataFrame(coords, geometry=gpd.points_from_xy(coords["lon"], coords["lat"]), crs="EPSG:4326")
    lsoa = gpd.read_file(config.LSOA_BOUNDARIES)[["LSOA21CD", "geometry"]]
    joined = gpd.sjoin(stations, lsoa, how="left", predicate="within").drop(columns="geometry")
    joined = joined.merge(lookup, on="LSOA21CD", how="left")[["NLC", "MSOA11CD"]].dropna()

    rail = rail.merge(joined, on="NLC", how="inner")
    dominant = rail.groupby("MSOA11CD")["cluster"].agg(mode_or_nan).rename("rail_cluster").reset_index()
    log.info("Dominant rail cluster assigned for %d MSOAs (of %d with any rail station)", len(dominant), rail["MSOA11CD"].nunique())
    return dominant


def dominant_bus_cluster_per_msoa() -> pd.DataFrame:
    # k4_labels.csv (StopArea CLR K=4) uses "lsoa" and marks excluded
    # (min_direction<36) LSOAs with cluster==-1 via retained_for_fit -- filter
    # those out before taking the per-MSOA mode, unlike the old bus_analysis_
    # lsoa.csv which only ever contained fitted rows.
    bus_raw = pd.read_csv(BUS_CLUSTER_LABELS)
    bus = bus_raw.loc[bus_raw["retained_for_fit"], ["lsoa", "cluster"]].rename(columns={"lsoa": "LSOA21CD"})
    lookup = pd.read_csv(config.MSOA_LOOKUP, usecols=["LSOA21CD", "MSOA11CD"])
    joined = bus.merge(lookup, on="LSOA21CD", how="inner")
    dominant = joined.groupby("MSOA11CD")["cluster"].agg(mode_or_nan).rename("bus_cluster").reset_index()
    log.info("Dominant bus cluster assigned for %d MSOAs", len(dominant))
    return dominant


def main() -> None:
    scores = pd.read_csv(config.DATA_OUT / "msoa_mismatch_scores.csv")
    rail_cl = dominant_rail_cluster_per_msoa()
    bus_cl = dominant_bus_cluster_per_msoa()

    merged = scores.merge(rail_cl, on="MSOA11CD", how="left").merge(bus_cl, on="MSOA11CD", how="left")

    lines = [
        "# RQ3 x RQ1 cluster check: does the mismatch score relate to the dissertation's own typology?",
        "",
        "The main analysis only interpreted residuals against the external LNWC "
        "classification. This checks the same residuals against RQ1's own rail "
        "(numbat_all_area_test, all-modes 403-station K=5) and bus "
        "(rq1_bus_stoparea_clustering, StopArea CLR K=4) cluster labels, which had "
        "been omitted -- a real gap, not a deliberate exclusion. Rail labels "
        "and descriptive names are the current 2026-08-07 rerun; names are "
        "loaded from the data-derived rail_cluster_names.csv rather than "
        "hard-coded here.",
        "",
    ]

    for direction in ("origin", "destination"):
        sub = merged[merged["direction"] == direction]

        lines.append(f"## {direction}")
        lines.append("")
        n_bus = int(sub["bus_cluster"].notna().sum())
        lines.append(f"### Bus cluster (n={n_bus} MSOAs)")
        bus_summary = sub.dropna(subset=["bus_cluster"]).groupby("bus_cluster")["std_residual"].agg(["mean", "median", "count"])
        bus_summary.index = bus_summary.index.map(lambda c: BUS_CLUSTER_NAMES.get(int(c), f"C{int(c)}"))
        log.info("%s bus cluster residual summary:\n%s", direction, bus_summary.to_string())
        lines.append(bus_summary.round(3).to_markdown())
        lines.append("")

        n_rail = int(sub["rail_cluster"].notna().sum())
        lines.append(f"### Rail cluster (n={n_rail} MSOAs with a station)")
        rail_summary = sub.dropna(subset=["rail_cluster"]).groupby("rail_cluster")["std_residual"].agg(["mean", "median", "count"])
        rail_summary.index = rail_summary.index.map(lambda c: RAIL_CLUSTER_NAMES.get(int(c), f"C{int(c)}"))
        log.info("%s rail cluster residual summary:\n%s", direction, rail_summary.to_string())
        lines.append(rail_summary.round(3).to_markdown())
        lines.append("")

    (config.REPORT_OUT / "RQ1_CLUSTER_CHECK.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote RQ1_CLUSTER_CHECK.md")


if __name__ == "__main__":
    main()
