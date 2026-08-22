from __future__ import annotations

from pathlib import Path

import pandas as pd

"""01d - Build the final, analysis-ready all-modes rail long table:
merged stations restricted to those with a NaPTAN Greater-London (area 490)
coordinate match.

Filters `01b`'s merged long table (currently 456 stations) down to the 440 with a
NaPTAN match found by `01c` -- i.e. drops only the 16 stations confirmed
2026-07-24 to be genuinely outside Greater London (Reading, Slough,
Maidenhead, Watford Junction, Shenfield, etc.; checked directly against the
local NaPTAN extract, not a name-matching bug). This mirrors canonical's
own scope convention: canonical's 270-station Underground clustering
already includes several border stations outside the strict Greater London
*boundary* (Amersham, Chesham, Epping, etc.) and only excludes those
downstream, at the LNWC/IMD linkage step -- never from the clustering
input itself. The geometric-extent question (is a station's point inside
the strict boundary, not just NaPTAN-listed) is intentionally NOT decided
here; it stays a downstream concern for whichever analysis needs it (see
`analysis/03_lnwc_context`'s `run_lnwc_analysis.py`).

This does not decide which of the remaining stations have non-zero
night-time activity -- that remains the job of whichever downstream
feature-building script consumes this output (e.g.
`analysis/02_mode_specific_clustering/rail/src/02_build_features_allmodes.py`'s own
`MIN_TOTAL=1` filter on the windowed night activity), so this script does
not duplicate that logic. In practice all 16 NaPTAN-unmatched stations
already have non-zero activity (they are real, served stations, just
outside the coordinate extract) and all 37 stations later dropped
downstream for zero activity (the tram-only stops -- see the main
`analysis/02_mode_specific_clustering/rail` validation report) already have a NaPTAN match --
the two filters are independent and do not overlap, so applying this one
first does not change what the zero-activity filter later removes.

Output is the final preprocessed artifact this preprocessing folder
promises to downstream consumers: `outputs/preprocessed/numbat_allmodes_station_qhr_all_daytypes_final.parquet`,
440 stations in the current run. Also writes the full station-count-chain report.
"""

DATA_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
PREPROCESSED_DIR = Path(__file__).resolve().parents[1] / "outputs" / "preprocessed"
REPORT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "report"
PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

RAW_LONG = DATA_DIR / "numbat_allmodes_station_qhr_all_daytypes.parquet"
MERGED_LONG = DATA_DIR / "numbat_allmodes_station_qhr_all_daytypes_merged.parquet"
MERGED_META = DATA_DIR / "numbat_allmodes_station_meta_merged.csv"
COORDS = DATA_DIR / "rail_allmodes_coords.csv"
CROSSWALK = DATA_DIR / "colocated_station_merge_crosswalk.csv"

FINAL_LONG_OUTPUT = PREPROCESSED_DIR / "numbat_allmodes_station_qhr_all_daytypes_final.parquet"
FINAL_META_OUTPUT = PREPROCESSED_DIR / "numbat_allmodes_station_meta_final.csv"


def main() -> None:
    raw_long = pd.read_parquet(RAW_LONG)
    merged_long = pd.read_parquet(MERGED_LONG)
    merged_meta = pd.read_csv(MERGED_META, dtype={"NLC": str})
    coords = pd.read_csv(COORDS, dtype={"unit": str})
    crosswalk = pd.read_csv(CROSSWALK, dtype={"NLC": str, "merged_NLC": str})

    merged_long["NLC"] = merged_long["NLC"].astype(str)
    matched_nlcs = set(coords.loc[coords["easting"].notna(), "unit"])

    n_raw = raw_long["NLC"].nunique()
    n_merged = merged_long["NLC"].nunique()
    n_matched = len(matched_nlcs)
    n_unmatched = n_merged - n_matched
    grouped_members = crosswalk.loc[crosswalk["merged_name"].notna()].copy()
    n_merge_groups = grouped_members["merged_NLC"].nunique()
    n_grouped_nlcs = grouped_members["NLC"].nunique()

    final_long = merged_long.loc[merged_long["NLC"].isin(matched_nlcs)].copy()
    n_final = final_long["NLC"].nunique()
    assert n_final == n_matched, f"expected {n_matched} stations after filter, got {n_final}"

    final_long.to_parquet(FINAL_LONG_OUTPUT, index=False)
    final_meta = merged_meta.loc[merged_meta["NLC"].isin(matched_nlcs)].copy()
    final_meta.to_csv(FINAL_META_OUTPUT, index=False)

    # Mirror the downstream feature builder's native-window retention rule so
    # this report does not hardcode the eventual clustering population.
    native_hi = {"MON": 1500, "TWT": 1500, "FRI": 1740, "SAT": 1740, "SUN": 1500}
    day_type = final_long["day_type"].astype(str)
    native_mask = (
        final_long["extended_minute"].ge(1080)
        & final_long["extended_minute"].lt(day_type.map(native_hi))
    )
    native_total = final_long.loc[native_mask].groupby("NLC")["count"].sum()
    n_cluster_eligible = int(native_total.ge(1).sum())
    n_zero_activity = n_final - n_cluster_eligible

    unmatched_stations = coords.loc[coords["easting"].isna(), ["unit", "Station", "mode_label"]]

    print(f"Raw NLCs (01): {n_raw}")
    print(f"Merged units (01b, {n_merge_groups} co-located groups collapsed): {n_merged}")
    print(f"NaPTAN-matched (01c): {n_matched}")
    print(f"NaPTAN-unmatched, dropped here (01d): {n_unmatched}")
    print(f"Final station count: {n_final}")
    print("Saved:", FINAL_LONG_OUTPUT)
    print("Saved:", FINAL_META_OUTPUT)

    generated = pd.Timestamp.utcnow().isoformat()
    lines = [
        "# All-modes rail preprocessing: station-count chain",
        "",
        "## Material Passport",
        "",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "",
        "## What this covers",
        "",
        "This folder converts raw NUMBAT rail-family workbooks (all modes: LU, "
        "DLR, Overground, Elizabeth line, Tram) into a single analysis-ready "
        "long table, in four steps. It does not build clustering features, "
        "fit any model, or decide which stations have non-zero night-time "
        "activity -- those remain downstream concerns (see "
        "`analysis/02_mode_specific_clustering/rail/`).",
        "",
        "## Station-count chain",
        "",
        f"| step | script | stations | change |",
        f"|---|---|---:|---|",
        f"| 1 | `01_preprocess_rail_allmodes.py` | {n_raw} | raw NLCs across all NUMBAT rail-family modes |",
        f"| 2 | `01b_merge_colocated_stations.py` | {n_merged} | {n_merge_groups} co-located cross-mode site groups ({n_grouped_nlcs} NLCs) merged into {n_merge_groups} units |",
        f"| 3 | `01c_match_naptan_coords.py` | {n_matched} matched / {n_unmatched} unmatched | NaPTAN Greater-London (area 490) coordinate match found or not |",
        f"| 4 | `01d_filter_naptan_matched.py` (this step) | {n_final} | unmatched stations dropped |",
        "",
        f"The **{n_final}-station output of this folder is not yet the {n_cluster_eligible}-station "
        "clustering population** used by `analysis/02_mode_specific_clustering/rail` -- a further "
        f"{n_zero_activity} stations (all tram-only, confirmed to have zero recorded "
        "activity in every day type, not just at night -- London Trams have "
        "no gateline and NUMBAT's Entries/Exits methodology is gateline-based) "
        "get dropped by that folder's own `02_build_features_allmodes.py` "
        "feature-building step, which this preprocessing folder deliberately "
        "does not duplicate. All 37 of those tram stations already have a "
        "NaPTAN match (real, served stops, just zero gateline activity), so "
        "this step's filter and that later one are independent and do not "
        f"overlap: {n_final} - {n_zero_activity} = {n_cluster_eligible}, the final clustering population.",
        "",
        f"## The {n_unmatched} NaPTAN-unmatched stations (dropped by this step)",
        "",
        unmatched_stations.to_markdown(index=False),
        "",
        "Confirmed genuinely outside Greater London by checking the local "
        "`490.xml` NaPTAN extract directly (zero genuine RSE/TMU-type matches "
        "for any of these names) -- a structural/geographic fact, not a "
        "name-matching bug. They are all in Hertfordshire (Watford DC line "
        "and Lea Valley line extensions), Berkshire/Buckinghamshire "
        "(Elizabeth line western branch), or Essex (Elizabeth line eastern "
        "branch).",
        "",
        "## Interpretation boundary",
        "",
        "- This is a station-population decision, not a clustering or "
        "statistical result -- it does not by itself say anything about "
        "night-time transport use.",
        "- The geometric question \"is this station's point inside the "
        "strict Greater London boundary\" (as opposed to \"is it in NaPTAN's "
        "area-490 list\") is intentionally NOT decided here -- canonical's "
        "own 270-station Underground clustering includes several stations "
        "that fail that stricter geometric test (Amersham, Chesham, Epping, "
        "etc.) without excluding them from the clustering itself, only from "
        "downstream LNWC/IMD linkage. Downstream analyses that need that "
        "distinction should compute it themselves against the LSOA boundary "
        "polygon, as `analysis/03_lnwc_context` does.",
    ]
    (REPORT_DIR / "RAIL_ALLMODES_PREPROCESSING.md").write_text("\n".join(lines), encoding="utf-8")
    print("Saved:", REPORT_DIR / "RAIL_ALLMODES_PREPROCESSING.md")


if __name__ == "__main__":
    main()
