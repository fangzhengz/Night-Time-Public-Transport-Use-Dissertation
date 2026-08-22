from __future__ import annotations

from pathlib import Path

import pandas as pd

"""01b - Merge co-located, cross-mode NUMBAT NLCs into single physical
stations.

`01_preprocess_rail_allmodes.py` keeps NUMBAT's own station-record
granularity (NLC) unchanged. For most interchanges NUMBAT already reports
one NLC covering every mode sharing a gateline (e.g. mode_label "LO,LU").
But at a specific, identifiable set of locations, modes that are
co-located (same building or the same airport terminal) have historically
separate fare-gated entities and therefore separate NLCs in NUMBAT itself
-- e.g. Heathrow's Underground and Elizabeth-line/Heathrow-Express sides
of each terminal. Left unmerged, these show up as two overlapping points
on the station map and as two separate rows in the clustering input, even
though they are one physical place.

This script sums entry/exit counts across each such group (per day type,
direction, time bin) into one merged unit, keyed by a `merged_NLC` id.
Where a group includes an LU-side NLC, that NLC is kept as the merged id,
so the merged station remains directly joinable against
`analysis/02_mode_specific_clustering/rail`'s canonical 270-station labels for the
groups that overlap with it.

Two of the fourteen groups (West Croydon, Wimbledon) pair a live NLC with
a Tram-only NLC; trams have zero recorded Entries/Exits everywhere (see
the main VALIDATION_REPORT's tram data-coverage note), so merging them is
a no-op on the numbers -- it only updates the merged mode_label to
disclose that a Tram service nominally exists there too.

Reads `01_preprocess_rail_allmodes.py`'s output unchanged; writes a new,
separate merged long table so the original NLC-level extraction remains
available for audit.

Moved 2026-07-24 from `analysis/02_mode_specific_clustering/rail/src/` into
`data_processing/rail_allmodes/` alongside `01`; logic unmodified (its
paths are already self-relative to this script's own folder).
"""

DATA_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
RAW_LONG_IN = DATA_DIR / "numbat_allmodes_station_qhr_all_daytypes.parquet"
META_IN = DATA_DIR / "numbat_allmodes_station_meta.csv"

MERGED_LONG_OUT = DATA_DIR / "numbat_allmodes_station_qhr_all_daytypes_merged.parquet"
MERGED_META_OUT = DATA_DIR / "numbat_allmodes_station_meta_merged.csv"
CROSSWALK_OUT = DATA_DIR / "colocated_station_merge_crosswalk.csv"

# Each group: NLCs that represent one physical site. The first NLC listed
# is used as the merged unit's id/name where it is the LU-side record, to
# stay directly comparable with canonical's 270 LU station identifiers.
MERGE_GROUPS: list[dict] = [
    {"name": "Bethnal Green", "nlcs": ["520", "6961"]},
    {"name": "Canary Wharf", "nlcs": ["852", "842", "6560"]},
    {"name": "Custom House", "nlcs": ["887", "6561"]},
    {"name": "Euston", "nlcs": ["574", "1444"]},
    {"name": "Heathrow Terminals 2 & 3", "nlcs": ["780", "7090"]},
    {"name": "Heathrow Terminal 4", "nlcs": ["781", "7091"]},
    {"name": "Heathrow Terminal 5", "nlcs": ["783", "9846"]},
    {"name": "Liverpool Street", "nlcs": ["634", "6965"]},
    # NUMBAT keeps the National Rail-side and TfL-side Paddington gatelines
    # under separate NLCs even though their matched station points are only
    # 26.4 m apart. Keep the LU-side NLC (670) as the anchor, consistently
    # with the rule above and the other cross-mode interchange groups.
    {"name": "Paddington", "nlcs": ["670", "3087"]},
    {"name": "Shadwell", "nlcs": ["1082", "860"]},
    {"name": "Shepherd's Bush", "nlcs": ["700", "9587"]},
    {"name": "West Croydon", "nlcs": ["5411", "8776"]},
    {"name": "West Hampstead", "nlcs": ["758", "1421"]},
    {"name": "Wimbledon", "nlcs": ["767", "8777"]},
]


def build_crosswalk(meta: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped_nlcs: set[str] = set()
    for group in MERGE_GROUPS:
        nlcs = group["nlcs"]
        merged_id = nlcs[0]
        for nlc in nlcs:
            grouped_nlcs.add(nlc)
            rows.append({"NLC": nlc, "merged_NLC": merged_id, "merged_name": group["name"]})

    ungrouped = meta[~meta["NLC"].astype(str).isin(grouped_nlcs)]
    for nlc in ungrouped["NLC"].astype(str):
        rows.append({"NLC": nlc, "merged_NLC": nlc, "merged_name": None})

    crosswalk = pd.DataFrame(rows)
    missing = set(meta["NLC"].astype(str)) - set(crosswalk["NLC"])
    if missing:
        raise ValueError(f"Crosswalk is missing NLCs present in meta: {sorted(missing)[:10]}")
    return crosswalk


def main() -> None:
    long_df = pd.read_parquet(RAW_LONG_IN)
    long_df["NLC"] = long_df["NLC"].astype(str)
    meta = pd.read_csv(META_IN, dtype={"NLC": str})

    crosswalk = build_crosswalk(meta)
    crosswalk.to_csv(CROSSWALK_OUT, index=False)

    n_groups = sum(1 for g in MERGE_GROUPS)
    n_nlcs_in_groups = sum(len(g["nlcs"]) for g in MERGE_GROUPS)
    print(f"Merge groups: {n_groups}, covering {n_nlcs_in_groups} original NLCs -> {n_groups} merged units")
    print(f"Net row reduction at the raw (471-station) level: {n_nlcs_in_groups - n_groups}")

    merged_long = long_df.merge(crosswalk[["NLC", "merged_NLC", "merged_name"]], on="NLC", how="left")
    if merged_long["merged_NLC"].isna().any():
        missing = merged_long.loc[merged_long["merged_NLC"].isna(), "NLC"].unique()
        raise ValueError(f"Unmapped NLCs in long table: {missing[:10]}")

    # Recompute Station display name and mode_label per merged unit.
    display_name = (
        merged_long[["merged_NLC", "merged_name", "Station"]]
        .drop_duplicates(["merged_NLC", "Station"])
        .groupby("merged_NLC")
        .agg(
            merged_name=("merged_name", "first"),
            original_stations=("Station", lambda s: ";".join(sorted(set(s)))),
        )
    )
    # Use the anchor NLC's OWN original Station name (i.e. the row where the
    # original NLC equals the merged unit id) as the merged Station name --
    # NOT a hand-picked display name -- so downstream coordinate matching
    # (05_build_allmodes_coords_and_map.py, which matches the LU side against
    # Underground_Stations.csv by exactly this kind of raw NUMBAT name) keeps
    # working unchanged. `merged_name` is kept only as a separate, human
    # readable label for reports.
    anchor_station_name = (
        merged_long.loc[merged_long["NLC"] == merged_long["merged_NLC"], ["merged_NLC", "Station"]]
        .drop_duplicates("merged_NLC")
        .set_index("merged_NLC")["Station"]
    )
    display_name["Station"] = anchor_station_name.reindex(display_name.index)
    missing_anchor = display_name["Station"].isna()
    if missing_anchor.any():
        display_name.loc[missing_anchor, "Station"] = (
            display_name.loc[missing_anchor, "original_stations"].str.split(";").str[0]
        )

    mode_label_by_unit = (
        merged_long[["merged_NLC", "mode_label"]]
        .drop_duplicates()
        .assign(modes=lambda d: d["mode_label"].str.split(","))
        .explode("modes")
        .groupby("merged_NLC")["modes"]
        .apply(lambda s: ",".join(sorted(set(s))))
        .rename("mode_label")
    )

    group_cols = ["day_type", "direction", "merged_NLC", "bin_label", "clock_time", "hour", "minute", "extended_minute"]
    summed = merged_long.groupby(group_cols, as_index=False, observed=True)["count"].sum()
    summed = summed.merge(mode_label_by_unit.reset_index(), on="merged_NLC", how="left")
    summed = summed.merge(display_name[["Station"]].reset_index(), on="merged_NLC", how="left")
    summed = summed.rename(columns={"merged_NLC": "NLC"})
    summed["ASC"] = summed["NLC"]
    summed["Fare Zone"] = pd.NA

    ordered_cols = [
        "day_type", "direction", "NLC", "ASC", "Station", "Fare Zone", "mode_label",
        "bin_label", "clock_time", "hour", "minute", "extended_minute", "count",
    ]
    summed = summed[ordered_cols]
    summed["day_type"] = pd.Categorical(summed["day_type"], categories=["MON", "TWT", "FRI", "SAT", "SUN"], ordered=True)
    summed = summed.sort_values(["day_type", "direction", "NLC", "extended_minute"]).reset_index(drop=True)

    summed.to_parquet(MERGED_LONG_OUT, index=False)

    meta_totals = (
        summed.groupby(["NLC", "Station", "mode_label", "direction"], as_index=False)
        .agg(total=("count", "sum"))
        .pivot_table(index=["NLC", "Station", "mode_label"], columns="direction", values="total", fill_value=0.0)
        .reset_index()
    )
    meta_totals.columns.name = None
    meta_totals = meta_totals.rename(columns={"entry": "total_entry", "exit": "total_exit"})
    meta_totals["total_activity"] = meta_totals["total_entry"] + meta_totals["total_exit"]
    meta_totals.to_csv(MERGED_META_OUT, index=False)

    print("\nBefore merge:", meta["NLC"].nunique(), "stations")
    print("After merge:", meta_totals["NLC"].nunique(), "stations")
    print("\nMerged units (name, mode_label, total_activity):")
    for _, row in meta_totals[meta_totals["NLC"].isin([g["nlcs"][0] for g in MERGE_GROUPS])].iterrows():
        print(f"  {row['Station']:30s} mode={row['mode_label']:15s} activity={row['total_activity']:.0f}")

    print("\nSaved:", MERGED_LONG_OUT)
    print("Saved:", MERGED_META_OUT)
    print("Saved:", CROSSWALK_OUT)


if __name__ == "__main__":
    main()
