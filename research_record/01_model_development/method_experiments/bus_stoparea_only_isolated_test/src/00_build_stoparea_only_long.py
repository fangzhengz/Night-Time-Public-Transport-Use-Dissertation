# -*- coding: utf-8 -*-
"""Build an LSOA long table using child StopAreas only.

The validated BUSTO-to-NaPTAN child StopArea crosswalk is reused read-only.
ParentStopAreaRef is retained for audit fields but never used for grouping or
coordinate selection in this variant.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def choose_medoid(candidates: pd.DataFrame) -> pd.Series:
    ordered = candidates.sort_values("candidate_code").reset_index(drop=True)
    coords = ordered[["candidate_easting", "candidate_northing"]].to_numpy(float)
    if len(coords) == 1:
        return ordered.iloc[0]
    distances = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(axis=2))
    return ordered.iloc[int(np.argmin(distances.sum(axis=1)))]


def build_units(stops: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for unit_code, members in stops.groupby("stoparea_unit_code", sort=True):
        area_candidates = (
            members.dropna(subset=["stop_area_code", "area_easting", "area_northing"])
            [["stop_area_code", "area_easting", "area_northing"]]
            .drop_duplicates()
            .rename(columns={
                "stop_area_code": "candidate_code",
                "area_easting": "candidate_easting",
                "area_northing": "candidate_northing",
            })
        )
        stop_candidates = (
            members.dropna(subset=["STOP_CODE", "OS_EASTING", "OS_NORTHING"])
            [["STOP_CODE", "OS_EASTING", "OS_NORTHING"]]
            .drop_duplicates()
            .rename(columns={
                "STOP_CODE": "candidate_code",
                "OS_EASTING": "candidate_easting",
                "OS_NORTHING": "candidate_northing",
            })
        )
        if not area_candidates.empty:
            chosen = choose_medoid(area_candidates)
            coordinate_source = "official_child_stoparea"
            n_candidates = len(area_candidates)
        elif not stop_candidates.empty:
            chosen = choose_medoid(stop_candidates)
            coordinate_source = "bus_stop_point_medoid_fallback"
            n_candidates = len(stop_candidates)
        else:
            chosen = pd.Series({
                "candidate_code": None,
                "candidate_easting": np.nan,
                "candidate_northing": np.nan,
            })
            coordinate_source = "missing"
            n_candidates = 0

        area_names = members["stop_area_name"].dropna()
        stop_names = members["STOP_NAME"].dropna()
        unit_name = (
            area_names.mode().iloc[0] if not area_names.empty
            else stop_names.mode().iloc[0] if not stop_names.empty
            else ""
        )
        rows.append({
            "stoparea_unit_code": unit_code,
            "stoparea_unit_name": unit_name,
            "unit_source": (
                "official_child_stoparea"
                if members["stop_area_code"].notna().any()
                else "singleton_bus_stop_fallback"
            ),
            "n_member_stops": members["STOP_CODE"].nunique(),
            "n_parent_refs": members["parent_stop_area_code"].nunique(),
            "n_coordinate_candidates": n_candidates,
            "representative_candidate_code": chosen["candidate_code"],
            "unit_easting": chosen["candidate_easting"],
            "unit_northing": chosen["candidate_northing"],
            "coordinate_source": coordinate_source,
        })
    return pd.DataFrame(rows)


def assign_units_to_lsoa(units: pd.DataFrame) -> pd.DataFrame:
    lsoa = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(col for col in lsoa.columns if col.lower() == "lsoa21cd")
    lsoa = lsoa[[code_column, "geometry"]].to_crs(C.CRS_BNG)

    valid = units.dropna(subset=["unit_easting", "unit_northing"]).copy()
    unit_gdf = gpd.GeoDataFrame(
        valid,
        geometry=gpd.points_from_xy(valid["unit_easting"], valid["unit_northing"]),
        crs=C.CRS_BNG,
    )
    joined = gpd.sjoin(unit_gdf, lsoa, how="left", predicate="intersects").rename(
        columns={code_column: "stoparea_lsoa"}
    )
    match_counts = (
        joined.dropna(subset=["stoparea_lsoa"])
        .groupby("stoparea_unit_code")["stoparea_lsoa"]
        .nunique()
        .rename("lsoa_match_count")
    )
    chosen = (
        joined.sort_values(["stoparea_unit_code", "stoparea_lsoa"], na_position="last")
        .drop_duplicates("stoparea_unit_code", keep="first")
        .drop(columns=["geometry", "index_right"], errors="ignore")
        .merge(match_counts, on="stoparea_unit_code", how="left")
    )
    chosen["lsoa_match_count"] = chosen["lsoa_match_count"].fillna(0).astype(int)
    chosen["lsoa_match"] = chosen["stoparea_lsoa"].notna()
    chosen["boundary_multiple_match"] = chosen["lsoa_match_count"] > 1

    missing = units.loc[
        units["unit_easting"].isna() | units["unit_northing"].isna()
    ].copy()
    if not missing.empty:
        missing["stoparea_lsoa"] = np.nan
        missing["lsoa_match_count"] = 0
        missing["lsoa_match"] = False
        missing["boundary_multiple_match"] = False
        chosen = pd.concat([chosen, missing], ignore_index=True)
    return chosen.sort_values("stoparea_unit_code").reset_index(drop=True)


def direction_totals(lsoa_long: pd.DataFrame) -> pd.DataFrame:
    totals = (
        lsoa_long.groupby(["lsoa", "direction"], as_index=False)["count"].sum()
        .pivot(index="lsoa", columns="direction", values="count")
        .fillna(0.0)
        .reset_index()
    )
    for direction in C.BUS_DIRECTIONS:
        if direction not in totals:
            totals[direction] = 0.0
    totals["total_activity"] = totals["boardings"] + totals["alightings"]
    totals["exact_direction_zero"] = (
        ((totals["boardings"] == 0) & (totals["alightings"] > 0))
        | ((totals["alightings"] == 0) & (totals["boardings"] > 0))
    )
    return totals


def main() -> None:
    stops = pd.read_csv(C.SOURCE_STOP_CROSSWALK, dtype={"STOP_CODE": str})
    flow = pd.read_parquet(C.STOP_FLOW_PARQUET).copy()
    flow["stopcode"] = flow["stopcode"].astype(str)
    stops["STOP_CODE"] = stops["STOP_CODE"].astype(str)
    if stops["STOP_CODE"].duplicated().any():
        raise RuntimeError("Source stop crosswalk contains duplicate STOP_CODE values.")
    if set(flow["stopcode"].unique()) != set(stops["STOP_CODE"]):
        raise RuntimeError("Flow stops do not exactly match the validated source crosswalk.")

    numeric_cols = [
        "OS_EASTING", "OS_NORTHING", "area_easting", "area_northing",
        "boardings", "alightings", "total_activity",
    ]
    for col in numeric_cols:
        stops[col] = pd.to_numeric(stops[col], errors="coerce")

    has_area = stops["stop_area_code"].notna()
    stops["stoparea_unit_code"] = np.where(
        has_area,
        "AREA::" + stops["stop_area_code"].fillna("").astype(str),
        "STOP::" + stops["STOP_CODE"],
    )

    units = assign_units_to_lsoa(build_units(stops))
    stops = stops.merge(
        units[[
            "stoparea_unit_code", "representative_candidate_code",
            "unit_easting", "unit_northing", "coordinate_source",
            "stoparea_lsoa", "lsoa_match", "boundary_multiple_match",
        ]],
        on="stoparea_unit_code", how="left", validate="many_to_one",
    )
    stops["changed_vs_original"] = (
        stops["old_lsoa"].notna() & stops["stoparea_lsoa"].notna()
        & (stops["old_lsoa"] != stops["stoparea_lsoa"])
    )
    stops["changed_vs_parent_hub"] = (
        stops["hub_lsoa"].notna() & stops["stoparea_lsoa"].notna()
        & (stops["hub_lsoa"] != stops["stoparea_lsoa"])
    )
    stops["newly_included_vs_original"] = (
        stops["old_lsoa"].isna() & stops["stoparea_lsoa"].notna()
    )
    stops["newly_excluded_vs_original"] = (
        stops["old_lsoa"].notna() & stops["stoparea_lsoa"].isna()
    )

    flow_with_unit = flow.merge(
        stops[["STOP_CODE", "stoparea_unit_code"]].rename(columns={"STOP_CODE": "stopcode"}),
        on="stopcode", how="left", validate="many_to_one",
    )
    if flow_with_unit["stoparea_unit_code"].isna().any():
        raise RuntimeError("Some flow rows were not assigned to a StopArea-only unit.")

    unit_qhr_all = (
        flow_with_unit.groupby(
            ["stoparea_unit_code", "day_type", "traffic_minute"], as_index=False
        )[["boardings", "alightings"]].sum()
        .merge(
            units[[
                "stoparea_unit_code", "stoparea_unit_name", "stoparea_lsoa",
                "unit_easting", "unit_northing", "coordinate_source",
            ]],
            on="stoparea_unit_code", how="left", validate="many_to_one",
        )
    )
    source_totals = flow[["boardings", "alightings"]].sum()
    grouped_totals = unit_qhr_all[["boardings", "alightings"]].sum()
    grouping_diff = float((source_totals - grouped_totals).abs().max())
    if grouping_diff > C.FLOAT_TOLERANCE:
        raise RuntimeError(f"StopArea aggregation failed demand conservation: {grouping_diff}")

    unit_qhr_london = unit_qhr_all.dropna(subset=["stoparea_lsoa"]).copy()
    unit_qhr_london["hour_bin"] = (unit_qhr_london["traffic_minute"] // 60) * 60
    lsoa_hourly = (
        unit_qhr_london.groupby(
            ["stoparea_lsoa", "day_type", "hour_bin"], as_index=False
        )[["boardings", "alightings"]].sum()
        .rename(columns={"stoparea_lsoa": "lsoa"})
    )
    lsoa_long = lsoa_hourly.melt(
        id_vars=["day_type", "lsoa", "hour_bin"],
        value_vars=C.BUS_DIRECTIONS,
        var_name="direction", value_name="count",
    )[["day_type", "direction", "lsoa", "hour_bin", "count"]]

    retained_stop_activity = float(
        stops.loc[stops["stoparea_lsoa"].notna(), "total_activity"].sum()
    )
    output_diff = abs(float(lsoa_long["count"].sum()) - retained_stop_activity)
    if output_diff > C.FLOAT_TOLERANCE:
        raise RuntimeError(f"LSOA output failed demand conservation: {output_diff}")

    totals = direction_totals(lsoa_long)
    summary_rows = [
        ("n_busto_used_stops", len(stops)),
        ("n_stoparea_only_units", len(units)),
        ("n_official_child_stopareas", int(has_area.groupby(stops["stop_area_code"]).any().sum())),
        ("n_singleton_stop_units", int((~has_area).sum())),
        ("n_units_official_child_coordinate", int((units["coordinate_source"] == "official_child_stoparea").sum())),
        ("n_units_stop_point_fallback", int((units["coordinate_source"] == "bus_stop_point_medoid_fallback").sum())),
        ("n_units_missing_coordinates", int((units["coordinate_source"] == "missing").sum())),
        ("n_units_assigned_london_lsoa", int(units["lsoa_match"].sum())),
        ("n_units_boundary_multiple_match", int(units["boundary_multiple_match"].sum())),
        ("n_lsoa_with_rows", int(totals["lsoa"].nunique())),
        ("n_lsoa_positive_activity", int((totals["total_activity"] > 0).sum())),
        ("n_lsoa_exact_direction_zero", int(totals["exact_direction_zero"].sum())),
        ("n_stops_changed_vs_original", int(stops["changed_vs_original"].sum())),
        ("activity_changed_vs_original", float(stops.loc[stops["changed_vs_original"], "total_activity"].sum())),
        ("n_stops_changed_vs_parent_hub", int(stops["changed_vs_parent_hub"].sum())),
        ("activity_changed_vs_parent_hub", float(stops.loc[stops["changed_vs_parent_hub"], "total_activity"].sum())),
        ("n_stops_newly_included_vs_original", int(stops["newly_included_vs_original"].sum())),
        ("n_stops_newly_excluded_vs_original", int(stops["newly_excluded_vs_original"].sum())),
        ("max_abs_demand_conservation_diff_before_lsoa", grouping_diff),
        ("abs_retained_demand_diff_in_lsoa_output", output_diff),
    ]
    summary = pd.DataFrame(summary_rows, columns=["metric", "value"])

    stops.to_csv(C.PRE / "stop_to_stoparea_crosswalk.csv", index=False)
    units.to_csv(C.PRE / "stoparea_unit_lsoa_crosswalk.csv", index=False)
    unit_qhr_all.to_parquet(C.PRE / "bus_stoparea_night_qhr_all.parquet", index=False)
    unit_qhr_london.to_parquet(C.PRE / "bus_stoparea_night_qhr_london.parquet", index=False)
    lsoa_long.to_parquet(C.BUS_LONG, index=False)
    totals.to_csv(C.DATA / "lsoa_direction_totals.csv", index=False)
    summary.to_csv(C.DATA / "preprocessing_summary.csv", index=False)

    report = [
        "## Material Passport", "",
        "- Origin Skill: academic-research-suite/experiment-agent", "- Origin Mode: run",
        "- Verification Status: ANALYZED", "- Version Label: stoparea_only_isolated_v1", "",
        "# StopArea-only preprocessing", "",
        "Single changed rule: child `StopAreaCode` is the terminal grouping unit;",
        "`ParentStopAreaRef` is ignored for grouping and coordinates.", "",
        "## Summary", "", summary.to_markdown(index=False, floatfmt=".6f"), "",
        "## Invariants", "",
        "- The validated BUSTO-to-child-StopArea crosswalk is reused read-only.",
        "- Stop-level boardings and alightings are conserved before London assignment.",
        "- LSOA matching uses the same EPSG:27700 boundaries and `intersects` rule.",
        "- Low-flow filtering, direction exclusions, feature construction and GMM do not occur here.", "",
    ]
    (C.REPORT / "STOPAREA_ONLY_PREPROCESSING.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
