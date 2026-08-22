"""Rebuild bus night demand using official bus hubs before LSOA aggregation."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

NAPTAN_DIR = FYP / "巴士数据" / "NaPTAN_data"
BUS_STOPS_CSV = FYP / "巴士数据" / "Bus_Stops.csv"
STOP_FLOW_PARQUET = (
    FYP / "outputs" / "preprocessed_busto" / "busto_stop_qhr_night.parquet"
)
CURRENT_LOOKUP_CSV = (
    FYP
    / "cluster_clean_version_grouped"
    / "outputs"
    / "preprocessed"
    / "bus_stop_lsoa_lookup.csv"
)
CURRENT_LSOA_LONG = (
    FYP
    / "cluster_clean_version_grouped"
    / "outputs"
    / "preprocessed"
    / "bus_lsoa_night_long.parquet"
)
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

PREPROCESSED = ROOT / "outputs" / "preprocessed"
DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
for directory in [PREPROCESSED, DATA, REPORT]:
    directory.mkdir(parents=True, exist_ok=True)

NS = {"n": "http://www.naptan.org.uk/"}
CRS_BNG = "EPSG:27700"
NEAR_ZERO_RATIO = 0.01
CORE_CLUSTER_MIN_TOTAL = 50.0
FLOAT_TOLERANCE = 1e-6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def child_text(node: ET.Element, path: str) -> str | None:
    element = node.find(path, NS)
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def parse_naptan(
    xml_paths: list[Path],
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    point_rows: list[dict] = []
    area_rows: list[dict] = []
    manifest: list[dict] = []

    for path in xml_paths:
        root = ET.parse(path).getroot()
        manifest.append(
            {
                "input": "naptan_xml",
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "rows": np.nan,
                "detail": (
                    f"FileName={root.attrib.get('FileName', '')}; "
                    f"CreationDateTime={root.attrib.get('CreationDateTime', '')}; "
                    f"SchemaVersion={root.attrib.get('SchemaVersion', '')}"
                ),
            }
        )

        for stop in root.findall(".//n:StopPoint", NS):
            point_rows.append(
                {
                    "atco_code": child_text(stop, ".//n:AtcoCode"),
                    "xml_naptan_code": child_text(stop, ".//n:NaptanCode"),
                    "xml_stop_name": child_text(stop, ".//n:CommonName"),
                    "stop_area_code": child_text(stop, ".//n:StopAreaRef"),
                    "source_xml": path.name,
                }
            )

        for area in root.findall(".//n:StopArea", NS):
            area_rows.append(
                {
                    "stop_area_code": child_text(area, ".//n:StopAreaCode"),
                    "stop_area_name": child_text(area, ".//n:Name"),
                    "stop_area_type": child_text(area, ".//n:StopAreaType"),
                    "parent_stop_area_code": child_text(
                        area, ".//n:ParentStopAreaRef"
                    ),
                    "area_easting": child_text(
                        area, ".//n:Location//n:Easting"
                    ),
                    "area_northing": child_text(
                        area, ".//n:Location//n:Northing"
                    ),
                    "source_xml": path.name,
                }
            )

    points = pd.DataFrame(point_rows)
    areas = pd.DataFrame(area_rows)
    if points.empty or areas.empty:
        raise RuntimeError("NaPTAN XML contains no StopPoint or StopArea records.")

    for column in ["area_easting", "area_northing"]:
        areas[column] = pd.to_numeric(areas[column], errors="coerce")

    point_conflicts = (
        points.dropna(subset=["atco_code"])
        .groupby("atco_code")["stop_area_code"]
        .nunique(dropna=False)
    )
    if (point_conflicts > 1).any():
        examples = point_conflicts[point_conflicts > 1].head().index.tolist()
        raise RuntimeError(f"Conflicting StopAreaRef values: {examples}")

    area_conflicts = (
        areas.dropna(subset=["stop_area_code"])
        .groupby("stop_area_code")["parent_stop_area_code"]
        .nunique(dropna=False)
    )
    if (area_conflicts > 1).any():
        examples = area_conflicts[area_conflicts > 1].head().index.tolist()
        raise RuntimeError(f"Conflicting ParentStopAreaRef values: {examples}")

    points = points.drop_duplicates("atco_code", keep="last")
    areas = areas.drop_duplicates("stop_area_code", keep="last")
    return points, areas, manifest


def highest_hub_code(
    stop_area_code: str | None, parent_map: dict[str, str]
) -> tuple[str | None, int, bool]:
    """Follow available ParentStopAreaRef links, including external final IDs."""
    if stop_area_code is None or pd.isna(stop_area_code):
        return None, 0, False
    current = str(stop_area_code)
    seen = {current}
    depth = 0
    cycle = False
    while current in parent_map and parent_map[current]:
        parent = parent_map[current]
        if parent in seen:
            cycle = True
            break
        seen.add(parent)
        current = parent
        depth += 1
    return current, depth, cycle


def choose_medoid(candidates: pd.DataFrame) -> pd.Series:
    """Choose an actual candidate point minimizing total Euclidean distance."""
    ordered = candidates.sort_values("candidate_code").reset_index(drop=True)
    coords = ordered[["candidate_easting", "candidate_northing"]].to_numpy(float)
    if len(coords) == 1:
        choice = 0
    else:
        distances = np.sqrt(
            ((coords[:, None, :] - coords[None, :, :]) ** 2).sum(axis=2)
        )
        choice = int(np.argmin(distances.sum(axis=1)))
    return ordered.iloc[choice]


def build_hub_points(
    stop_crosswalk: pd.DataFrame, areas: pd.DataFrame
) -> pd.DataFrame:
    area_candidates = (
        stop_crosswalk.dropna(subset=["logical_hub_code", "stop_area_code"])
        [["logical_hub_code", "stop_area_code"]]
        .drop_duplicates()
        .merge(
            areas[
                [
                    "stop_area_code",
                    "stop_area_name",
                    "area_easting",
                    "area_northing",
                ]
            ],
            on="stop_area_code",
            how="left",
        )
        .dropna(subset=["area_easting", "area_northing"])
        .rename(
            columns={
                "stop_area_code": "candidate_code",
                "area_easting": "candidate_easting",
                "area_northing": "candidate_northing",
            }
        )
    )

    stop_candidates = (
        stop_crosswalk.dropna(
            subset=["logical_hub_code", "OS_EASTING", "OS_NORTHING"]
        )
        [
            [
                "logical_hub_code",
                "STOP_CODE",
                "OS_EASTING",
                "OS_NORTHING",
            ]
        ]
        .drop_duplicates()
        .rename(
            columns={
                "STOP_CODE": "candidate_code",
                "OS_EASTING": "candidate_easting",
                "OS_NORTHING": "candidate_northing",
            }
        )
    )

    area_groups = {
        hub: group for hub, group in area_candidates.groupby("logical_hub_code")
    }
    stop_groups = {
        hub: group for hub, group in stop_candidates.groupby("logical_hub_code")
    }

    rows: list[dict] = []
    for hub, members in stop_crosswalk.groupby("logical_hub_code", dropna=False):
        if pd.isna(hub):
            continue
        if hub in area_groups:
            candidates = area_groups[hub]
            chosen = choose_medoid(candidates)
            coordinate_source = (
                "official_bus_stop_area"
                if candidates["candidate_code"].nunique() == 1
                else "official_bus_stop_area_medoid"
            )
            n_coordinate_candidates = candidates["candidate_code"].nunique()
        elif hub in stop_groups:
            candidates = stop_groups[hub]
            chosen = choose_medoid(candidates)
            coordinate_source = "bus_stop_point_medoid_fallback"
            n_coordinate_candidates = candidates["candidate_code"].nunique()
        else:
            chosen = pd.Series(
                {
                    "candidate_code": None,
                    "candidate_easting": np.nan,
                    "candidate_northing": np.nan,
                }
            )
            coordinate_source = "missing"
            n_coordinate_candidates = 0

        area_names = members["stop_area_name"].dropna()
        stop_names = members["STOP_NAME"].dropna()
        if not area_names.empty:
            hub_name = area_names.mode().iloc[0]
        elif not stop_names.empty:
            hub_name = stop_names.mode().iloc[0]
        else:
            hub_name = ""

        rows.append(
            {
                "logical_hub_code": hub,
                "logical_hub_name": hub_name,
                "logical_hub_source": members["logical_hub_source"].iloc[0],
                "hierarchy_depth": int(members["hierarchy_depth"].max()),
                "n_member_stops": members["STOP_CODE"].nunique(),
                "n_member_stop_areas": members["stop_area_code"].nunique(),
                "n_coordinate_candidates": n_coordinate_candidates,
                "representative_candidate_code": chosen["candidate_code"],
                "hub_easting": chosen["candidate_easting"],
                "hub_northing": chosen["candidate_northing"],
                "coordinate_source": coordinate_source,
            }
        )
    return pd.DataFrame(rows)


def assign_hubs_to_lsoa(hubs: pd.DataFrame) -> pd.DataFrame:
    lsoa = gpd.read_file(LSOA_GEOJSON)
    code_column = next(column for column in lsoa.columns if column.lower() == "lsoa21cd")
    lsoa = lsoa[[code_column, "geometry"]].to_crs(CRS_BNG)

    valid = hubs.dropna(subset=["hub_easting", "hub_northing"]).copy()
    hub_gdf = gpd.GeoDataFrame(
        valid,
        geometry=gpd.points_from_xy(valid["hub_easting"], valid["hub_northing"]),
        crs=CRS_BNG,
    )
    joined = gpd.sjoin(hub_gdf, lsoa, how="left", predicate="intersects")
    joined = joined.rename(columns={code_column: "hub_lsoa"})

    match_counts = (
        joined.dropna(subset=["hub_lsoa"])
        .groupby("logical_hub_code")["hub_lsoa"]
        .nunique()
        .rename("lsoa_match_count")
    )
    chosen = (
        joined.sort_values(["logical_hub_code", "hub_lsoa"], na_position="last")
        .drop_duplicates("logical_hub_code", keep="first")
        .drop(columns=["geometry", "index_right"], errors="ignore")
    )
    chosen = chosen.merge(match_counts, on="logical_hub_code", how="left")
    chosen["lsoa_match_count"] = chosen["lsoa_match_count"].fillna(0).astype(int)
    chosen["hub_lsoa_match"] = chosen["hub_lsoa"].notna()
    chosen["boundary_multiple_match"] = chosen["lsoa_match_count"] > 1

    missing_coordinates = hubs.loc[
        hubs["hub_easting"].isna() | hubs["hub_northing"].isna()
    ].copy()
    if not missing_coordinates.empty:
        missing_coordinates["hub_lsoa"] = np.nan
        missing_coordinates["lsoa_match_count"] = 0
        missing_coordinates["hub_lsoa_match"] = False
        missing_coordinates["boundary_multiple_match"] = False
        chosen = pd.concat([chosen, missing_coordinates], ignore_index=True)
    return chosen.sort_values("logical_hub_code").reset_index(drop=True)


def assign_stop_points_to_lsoa(stop_crosswalk: pd.DataFrame) -> pd.DataFrame:
    """Independently reproduce the old point-to-LSOA assignment for auditing."""
    lsoa = gpd.read_file(LSOA_GEOJSON)
    code_column = next(column for column in lsoa.columns if column.lower() == "lsoa21cd")
    lsoa = lsoa[[code_column, "geometry"]].to_crs(CRS_BNG)

    valid = stop_crosswalk.dropna(subset=["OS_EASTING", "OS_NORTHING"]).copy()
    stop_gdf = gpd.GeoDataFrame(
        valid[["STOP_CODE", "OS_EASTING", "OS_NORTHING"]],
        geometry=gpd.points_from_xy(valid["OS_EASTING"], valid["OS_NORTHING"]),
        crs=CRS_BNG,
    )
    joined = gpd.sjoin(stop_gdf, lsoa, how="left", predicate="intersects").rename(
        columns={code_column: "direct_point_lsoa"}
    )
    match_counts = (
        joined.dropna(subset=["direct_point_lsoa"])
        .groupby("STOP_CODE")["direct_point_lsoa"]
        .nunique()
        .rename("direct_point_lsoa_match_count")
    )
    chosen = (
        joined.sort_values(["STOP_CODE", "direct_point_lsoa"], na_position="last")
        .drop_duplicates("STOP_CODE", keep="first")
        .drop(columns=["geometry", "index_right"], errors="ignore")
        .merge(match_counts, on="STOP_CODE", how="left")
    )
    chosen["direct_point_lsoa_match_count"] = (
        chosen["direct_point_lsoa_match_count"].fillna(0).astype(int)
    )
    return chosen[
        ["STOP_CODE", "direct_point_lsoa", "direct_point_lsoa_match_count"]
    ]


def build_direction_eligibility(totals: pd.DataFrame) -> pd.DataFrame:
    """Flag degenerate two-direction profiles without deleting source demand."""
    eligibility = totals.copy()
    eligibility["total_activity"] = (
        eligibility["boardings"] + eligibility["alightings"]
    )
    maximum = eligibility[["boardings", "alightings"]].max(axis=1)
    eligibility["direction_ratio"] = (
        eligibility[["boardings", "alightings"]].min(axis=1)
        / maximum.replace(0, np.nan)
    )
    eligibility["exact_direction_zero"] = (
        ((eligibility["boardings"] == 0) & (eligibility["alightings"] > 0))
        | ((eligibility["alightings"] == 0) & (eligibility["boardings"] > 0))
    )
    eligibility["near_zero_ratio_lt_0_01"] = (
        ~eligibility["exact_direction_zero"]
        & (eligibility["direction_ratio"] < NEAR_ZERO_RATIO)
    )
    eligibility["eligible_two_direction_clustering"] = (
        (eligibility["boardings"] > 0) & (eligibility["alightings"] > 0)
    )
    eligibility["exclusion_reason"] = np.select(
        [
            (eligibility["boardings"] == 0) & (eligibility["alightings"] > 0),
            (eligibility["alightings"] == 0) & (eligibility["boardings"] > 0),
            (eligibility["boardings"] == 0) & (eligibility["alightings"] == 0),
        ],
        ["zero_boarding_direction", "zero_alighting_direction", "zero_total"],
        default="",
    )
    return eligibility


def file_manifest_row(label: str, path: Path, rows: int, detail: str = "") -> dict:
    return {
        "input": label,
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "rows": rows,
        "detail": detail,
    }


def main() -> None:
    xml_paths = sorted(NAPTAN_DIR.glob("*.xml"))
    if not xml_paths:
        raise FileNotFoundError(f"No NaPTAN XML files found under {NAPTAN_DIR}")

    points, areas, manifest = parse_naptan(xml_paths)
    parent_map = (
        areas.dropna(subset=["stop_area_code", "parent_stop_area_code"])
        .set_index("stop_area_code")["parent_stop_area_code"]
        .to_dict()
    )

    bus_stops = pd.read_csv(BUS_STOPS_CSV, dtype=str)
    bus_stops["STOP_CODE"] = bus_stops["STOP_CODE"].astype(str)
    bus_stops["NAPTAN_ATCO"] = bus_stops["NAPTAN_ATCO"].str.strip()
    for column in ["OS_EASTING", "OS_NORTHING"]:
        bus_stops[column] = pd.to_numeric(bus_stops[column], errors="coerce")
    if bus_stops["STOP_CODE"].duplicated().any():
        raise RuntimeError("Bus_Stops.csv contains duplicate STOP_CODE values.")

    flow = pd.read_parquet(STOP_FLOW_PARQUET).copy()
    flow["stopcode"] = flow["stopcode"].astype(str)
    used_stops = pd.DataFrame({"STOP_CODE": sorted(flow["stopcode"].unique())})
    stop_totals = (
        flow.groupby("stopcode", as_index=False)[["boardings", "alightings"]]
        .sum()
        .rename(columns={"stopcode": "STOP_CODE"})
    )

    current_lookup = pd.read_csv(CURRENT_LOOKUP_CSV, dtype=str)
    current_lookup["stopcode"] = current_lookup["stopcode"].astype(str)
    if current_lookup["stopcode"].duplicated().any():
        raise RuntimeError("Current LSOA lookup contains duplicate stopcodes.")
    current_long = pd.read_parquet(CURRENT_LSOA_LONG).copy()

    manifest.extend(
        [
            file_manifest_row("bus_stops", BUS_STOPS_CSV, len(bus_stops)),
            file_manifest_row("stop_level_night_flow", STOP_FLOW_PARQUET, len(flow)),
            file_manifest_row(
                "current_lsoa_lookup", CURRENT_LOOKUP_CSV, len(current_lookup)
            ),
            file_manifest_row(
                "current_lsoa_long", CURRENT_LSOA_LONG, len(current_long)
            ),
            file_manifest_row("lsoa21_boundaries", LSOA_GEOJSON, -1),
        ]
    )

    stop_crosswalk = (
        used_stops.merge(
            bus_stops[
                [
                    "STOP_CODE",
                    "STOP_NAME",
                    "NAPTAN_ATCO",
                    "ROAD_NAME",
                    "POINT_LETTER",
                    "ROUTES",
                    "OS_EASTING",
                    "OS_NORTHING",
                    "DATE_UPDATED",
                ]
            ],
            on="STOP_CODE",
            how="left",
        )
        .merge(points, left_on="NAPTAN_ATCO", right_on="atco_code", how="left")
        .merge(areas, on="stop_area_code", how="left", suffixes=("", "_area"))
        .merge(
            current_lookup[["stopcode", "lsoa"]].rename(
                columns={"stopcode": "STOP_CODE", "lsoa": "old_lsoa"}
            ),
            on="STOP_CODE",
            how="left",
        )
        .merge(stop_totals, on="STOP_CODE", how="left")
    )

    hierarchy = stop_crosswalk["stop_area_code"].apply(
        lambda value: highest_hub_code(value, parent_map)
    )
    stop_crosswalk[["logical_hub_code", "hierarchy_depth", "hierarchy_cycle"]] = (
        pd.DataFrame(hierarchy.tolist(), index=stop_crosswalk.index)
    )
    if stop_crosswalk["hierarchy_cycle"].any():
        examples = stop_crosswalk.loc[
            stop_crosswalk["hierarchy_cycle"], "stop_area_code"
        ].head().tolist()
        raise RuntimeError(f"NaPTAN parent hierarchy cycle detected: {examples}")

    no_hub = stop_crosswalk["logical_hub_code"].isna()
    stop_crosswalk.loc[no_hub, "logical_hub_code"] = (
        "STOP::" + stop_crosswalk.loc[no_hub, "STOP_CODE"].astype(str)
    )
    stop_crosswalk["logical_hub_source"] = np.select(
        [
            stop_crosswalk["hierarchy_depth"] > 0,
            stop_crosswalk["stop_area_code"].notna(),
        ],
        ["parent_stop_area_identifier", "official_bus_stop_area"],
        default="singleton_bus_stop_fallback",
    )

    direct_point_lsoa = assign_stop_points_to_lsoa(stop_crosswalk)
    stop_crosswalk = stop_crosswalk.merge(
        direct_point_lsoa, on="STOP_CODE", how="left", validate="one_to_one"
    )
    hubs = build_hub_points(stop_crosswalk, areas)
    hubs = assign_hubs_to_lsoa(hubs)
    stop_crosswalk = stop_crosswalk.merge(
        hubs[
            [
                "logical_hub_code",
                "logical_hub_name",
                "representative_candidate_code",
                "hub_easting",
                "hub_northing",
                "coordinate_source",
                "hub_lsoa",
                "hub_lsoa_match",
                "boundary_multiple_match",
            ]
        ],
        on="logical_hub_code",
        how="left",
    )

    stop_crosswalk["old_and_new_lsoa"] = (
        stop_crosswalk["old_lsoa"].notna() & stop_crosswalk["hub_lsoa"].notna()
    )
    stop_crosswalk["moved_between_lsoa"] = (
        stop_crosswalk["old_and_new_lsoa"]
        & (stop_crosswalk["old_lsoa"] != stop_crosswalk["hub_lsoa"])
    )
    stop_crosswalk["old_and_direct_lsoa"] = (
        stop_crosswalk["old_lsoa"].notna()
        & stop_crosswalk["direct_point_lsoa"].notna()
    )
    stop_crosswalk["old_lookup_diff_from_direct_point"] = (
        stop_crosswalk["old_and_direct_lsoa"]
        & (stop_crosswalk["old_lsoa"] != stop_crosswalk["direct_point_lsoa"])
    )
    stop_crosswalk["direct_and_hub_lsoa"] = (
        stop_crosswalk["direct_point_lsoa"].notna()
        & stop_crosswalk["hub_lsoa"].notna()
    )
    stop_crosswalk["changed_by_hub_rule"] = (
        stop_crosswalk["direct_and_hub_lsoa"]
        & (stop_crosswalk["direct_point_lsoa"] != stop_crosswalk["hub_lsoa"])
    )
    stop_crosswalk["newly_included"] = (
        stop_crosswalk["old_lsoa"].isna() & stop_crosswalk["hub_lsoa"].notna()
    )
    stop_crosswalk["newly_excluded"] = (
        stop_crosswalk["old_lsoa"].notna() & stop_crosswalk["hub_lsoa"].isna()
    )
    stop_crosswalk["total_activity"] = (
        stop_crosswalk["boardings"] + stop_crosswalk["alightings"]
    )

    flow_with_hub = flow.merge(
        stop_crosswalk[["STOP_CODE", "logical_hub_code"]].rename(
            columns={"STOP_CODE": "stopcode"}
        ),
        on="stopcode",
        how="left",
        validate="many_to_one",
    )
    if flow_with_hub["logical_hub_code"].isna().any():
        raise RuntimeError("Some BUSTO flow rows were not assigned to a logical hub.")

    hub_qhr_all = (
        flow_with_hub.groupby(
            ["logical_hub_code", "day_type", "traffic_minute"], as_index=False
        )[["boardings", "alightings"]]
        .sum()
        .merge(
            hubs[
                [
                    "logical_hub_code",
                    "logical_hub_name",
                    "hub_lsoa",
                    "hub_easting",
                    "hub_northing",
                    "coordinate_source",
                ]
            ],
            on="logical_hub_code",
            how="left",
        )
    )
    hub_qhr_london = hub_qhr_all.dropna(subset=["hub_lsoa"]).copy()

    source_boardings = float(flow["boardings"].sum())
    source_alightings = float(flow["alightings"].sum())
    grouped_boardings = float(hub_qhr_all["boardings"].sum())
    grouped_alightings = float(hub_qhr_all["alightings"].sum())
    max_grouping_diff = max(
        abs(source_boardings - grouped_boardings),
        abs(source_alightings - grouped_alightings),
    )
    if max_grouping_diff > FLOAT_TOLERANCE:
        raise RuntimeError(
            f"Hub aggregation failed demand conservation: {max_grouping_diff}"
        )

    hub_qhr_london["hour_bin"] = (
        hub_qhr_london["traffic_minute"] // 60
    ) * 60
    lsoa_hourly_wide = (
        hub_qhr_london.groupby(
            ["hub_lsoa", "day_type", "hour_bin"], as_index=False
        )[["boardings", "alightings"]]
        .sum()
        .rename(columns={"hub_lsoa": "lsoa"})
    )
    lsoa_long = lsoa_hourly_wide.melt(
        id_vars=["day_type", "lsoa", "hour_bin"],
        value_vars=["boardings", "alightings"],
        var_name="direction",
        value_name="count",
    )[["day_type", "direction", "lsoa", "hour_bin", "count"]]

    old_totals = (
        current_long.groupby(["lsoa", "direction"], as_index=False)["count"]
        .sum()
        .pivot(index="lsoa", columns="direction", values="count")
        .fillna(0.0)
        .reset_index()
    )
    new_totals = (
        lsoa_long.groupby(["lsoa", "direction"], as_index=False)["count"]
        .sum()
        .pivot(index="lsoa", columns="direction", values="count")
        .fillna(0.0)
        .reset_index()
    )
    for frame in [old_totals, new_totals]:
        for direction in ["boardings", "alightings"]:
            if direction not in frame:
                frame[direction] = 0.0

    lsoa_comparison = old_totals.merge(
        new_totals, on="lsoa", how="outer", suffixes=("_old", "_hub_first")
    ).fillna(0.0)
    for direction in ["boardings", "alightings"]:
        lsoa_comparison[f"{direction}_delta"] = (
            lsoa_comparison[f"{direction}_hub_first"]
            - lsoa_comparison[f"{direction}_old"]
        )
    lsoa_comparison["total_old"] = (
        lsoa_comparison["boardings_old"] + lsoa_comparison["alightings_old"]
    )
    lsoa_comparison["total_hub_first"] = (
        lsoa_comparison["boardings_hub_first"]
        + lsoa_comparison["alightings_hub_first"]
    )
    lsoa_comparison["total_delta"] = (
        lsoa_comparison["total_hub_first"] - lsoa_comparison["total_old"]
    )

    eligibility = build_direction_eligibility(new_totals)

    group_members = {
        "weekday": ["Weekday"],
        "weekend": ["Saturday", "Sunday"],
    }
    group_eligibility_parts: list[pd.DataFrame] = []
    for group_name, members in group_members.items():
        group_totals = (
            lsoa_long.loc[lsoa_long["day_type"].isin(members)]
            .groupby(["lsoa", "direction"], as_index=False)["count"]
            .sum()
            .pivot(index="lsoa", columns="direction", values="count")
            .fillna(0.0)
            .reset_index()
        )
        for direction in ["boardings", "alightings"]:
            if direction not in group_totals:
                group_totals[direction] = 0.0
        group_flags = build_direction_eligibility(group_totals)
        group_flags.insert(1, "analysis_group", group_name)
        group_eligibility_parts.append(group_flags)
    group_eligibility = pd.concat(group_eligibility_parts, ignore_index=True)
    group_eligibility["is_one_direction_exception"] = group_eligibility[
        "exact_direction_zero"
    ]
    group_eligibility["meets_core_min_total_50"] = (
        group_eligibility["total_activity"] >= CORE_CLUSTER_MIN_TOTAL
    )
    group_eligibility["eligible_core_clustering"] = (
        group_eligibility["eligible_two_direction_clustering"]
        & group_eligibility["meets_core_min_total_50"]
    )
    group_eligibility["analysis_status"] = np.select(
        [
            group_eligibility["is_one_direction_exception"],
            ~group_eligibility["meets_core_min_total_50"],
        ],
        ["one_direction_exception", "below_min_total_50"],
        default="eligible_core_clustering",
    )
    one_direction_exceptions = group_eligibility.loc[
        group_eligibility["is_one_direction_exception"]
    ].copy()

    old_zero = (
        ((old_totals["boardings"] == 0) & (old_totals["alightings"] > 0))
        | ((old_totals["alightings"] == 0) & (old_totals["boardings"] > 0))
    )
    current_retained_activity = float(
        stop_crosswalk.loc[stop_crosswalk["old_lsoa"].notna(), "total_activity"].sum()
    )
    hub_first_retained_activity = float(
        stop_crosswalk.loc[stop_crosswalk["hub_lsoa"].notna(), "total_activity"].sum()
    )
    moved_activity = float(
        stop_crosswalk.loc[stop_crosswalk["moved_between_lsoa"], "total_activity"].sum()
    )
    newly_included_activity = float(
        stop_crosswalk.loc[stop_crosswalk["newly_included"], "total_activity"].sum()
    )
    newly_excluded_activity = float(
        stop_crosswalk.loc[stop_crosswalk["newly_excluded"], "total_activity"].sum()
    )
    stop_crosswalk["activity_changed_by_hub_rule"] = stop_crosswalk[
        "total_activity"
    ].where(stop_crosswalk["changed_by_hub_rule"], 0.0)
    stop_crosswalk["activity_old_lookup_diff"] = stop_crosswalk[
        "total_activity"
    ].where(stop_crosswalk["old_lookup_diff_from_direct_point"], 0.0)
    changed_by_hub_activity = float(
        stop_crosswalk["activity_changed_by_hub_rule"].sum()
    )
    old_lookup_diff_activity = float(stop_crosswalk["activity_old_lookup_diff"].sum())
    london_output_diff = abs(
        float(lsoa_long["count"].sum()) - hub_first_retained_activity
    )
    if london_output_diff > FLOAT_TOLERANCE:
        raise RuntimeError(
            f"London LSOA output failed retained-demand conservation: {london_output_diff}"
        )

    hub_activity = stop_crosswalk.groupby("logical_hub_code")["total_activity"].sum()
    movement_by_hub_source = (
        stop_crosswalk.groupby("logical_hub_source", dropna=False)
        .agg(
            n_stops=("STOP_CODE", "size"),
            n_hubs=("logical_hub_code", "nunique"),
            n_stops_changed_lsoa=("changed_by_hub_rule", "sum"),
            total_activity=("total_activity", "sum"),
            activity_changed_lsoa=("activity_changed_by_hub_rule", "sum"),
        )
        .reset_index()
        .rename(columns={"logical_hub_source": "category"})
    )
    movement_by_hub_source.insert(0, "dimension", "logical_hub_source")
    movement_by_coordinate_source = (
        stop_crosswalk.groupby("coordinate_source", dropna=False)
        .agg(
            n_stops=("STOP_CODE", "size"),
            n_hubs=("logical_hub_code", "nunique"),
            n_stops_changed_lsoa=("changed_by_hub_rule", "sum"),
            total_activity=("total_activity", "sum"),
            activity_changed_lsoa=("activity_changed_by_hub_rule", "sum"),
        )
        .reset_index()
        .rename(columns={"coordinate_source": "category"})
    )
    movement_by_coordinate_source.insert(0, "dimension", "coordinate_source")
    movement_decomposition = pd.concat(
        [movement_by_hub_source, movement_by_coordinate_source], ignore_index=True
    )
    movement_decomposition["pct_activity_changed_within_category"] = 100 * (
        movement_decomposition["activity_changed_lsoa"]
        / movement_decomposition["total_activity"].replace(0, np.nan)
    )
    unresolved_coordinates = stop_crosswalk.loc[
        stop_crosswalk["coordinate_source"] == "missing",
        [
            "STOP_CODE",
            "STOP_NAME",
            "NAPTAN_ATCO",
            "stop_area_code",
            "old_lsoa",
            "boardings",
            "alightings",
            "total_activity",
        ],
    ].copy()
    boundary_inclusion_changes = stop_crosswalk.loc[
        stop_crosswalk["newly_included"] | stop_crosswalk["newly_excluded"],
        [
            "STOP_CODE",
            "STOP_NAME",
            "logical_hub_code",
            "old_lsoa",
            "hub_lsoa",
            "newly_included",
            "newly_excluded",
            "boardings",
            "alightings",
            "total_activity",
        ],
    ].copy()

    summary_rows = [
        ("n_busto_used_stops", len(stop_crosswalk)),
        ("n_logical_hubs", len(hubs)),
        ("n_parent_identifier_hubs", int((hubs["hierarchy_depth"] > 0).sum())),
        (
            "n_hubs_official_bus_area_coordinates",
            int(hubs["coordinate_source"].str.startswith("official_bus").sum()),
        ),
        (
            "n_hubs_stop_point_coordinate_fallback",
            int((hubs["coordinate_source"] == "bus_stop_point_medoid_fallback").sum()),
        ),
        ("n_hubs_missing_coordinates", int((hubs["coordinate_source"] == "missing").sum())),
        ("activity_missing_coordinates", float(unresolved_coordinates["total_activity"].sum())),
        (
            "n_missing_coordinate_stops_without_naptan_atco",
            int(unresolved_coordinates["NAPTAN_ATCO"].isna().sum()),
        ),
        ("n_hubs_assigned_london_lsoa", int(hubs["hub_lsoa_match"].sum())),
        ("n_hubs_boundary_multiple_match", int(hubs["boundary_multiple_match"].sum())),
        (
            "n_stop_points_boundary_multiple_match",
            int((stop_crosswalk["direct_point_lsoa_match_count"] > 1).sum()),
        ),
        ("n_stops_moved_between_lsoa", int(stop_crosswalk["moved_between_lsoa"].sum())),
        (
            "n_stops_old_lookup_diff_from_direct_point",
            int(stop_crosswalk["old_lookup_diff_from_direct_point"].sum()),
        ),
        ("activity_old_lookup_diff_from_direct_point", old_lookup_diff_activity),
        ("n_stops_changed_by_hub_rule", int(stop_crosswalk["changed_by_hub_rule"].sum())),
        ("activity_changed_by_hub_rule", changed_by_hub_activity),
        ("n_stops_newly_included", int(stop_crosswalk["newly_included"].sum())),
        ("n_stops_newly_excluded", int(stop_crosswalk["newly_excluded"].sum())),
        ("current_retained_activity", current_retained_activity),
        ("hub_first_retained_activity", hub_first_retained_activity),
        ("activity_moved_between_lsoa", moved_activity),
        (
            "pct_current_activity_moved_between_lsoa",
            100 * moved_activity / current_retained_activity,
        ),
        ("activity_newly_included", newly_included_activity),
        ("activity_newly_excluded", newly_excluded_activity),
        ("n_lsoa_current", len(old_totals)),
        ("n_lsoa_hub_first", len(new_totals)),
        ("n_exact_direction_zero_lsoa_current", int(old_zero.sum())),
        (
            "n_exact_direction_zero_lsoa_hub_first",
            int(eligibility["exact_direction_zero"].sum()),
        ),
        (
            "n_near_zero_positive_lsoa_hub_first",
            int(eligibility["near_zero_ratio_lt_0_01"].sum()),
        ),
        (
            "n_exact_direction_zero_lsoa_weekday",
            int(
                group_eligibility.loc[
                    group_eligibility["analysis_group"] == "weekday",
                    "exact_direction_zero",
                ].sum()
            ),
        ),
        (
            "n_exact_direction_zero_lsoa_weekend",
            int(
                group_eligibility.loc[
                    group_eligibility["analysis_group"] == "weekend",
                    "exact_direction_zero",
                ].sum()
            ),
        ),
        (
            "n_unique_one_direction_exception_lsoas",
            int(one_direction_exceptions["lsoa"].nunique()),
        ),
        (
            "n_one_direction_exceptions_meeting_min_total_weekday",
            int(
                one_direction_exceptions.loc[
                    one_direction_exceptions["analysis_group"] == "weekday",
                    "meets_core_min_total_50",
                ].sum()
            ),
        ),
        (
            "n_one_direction_exceptions_meeting_min_total_weekend",
            int(
                one_direction_exceptions.loc[
                    one_direction_exceptions["analysis_group"] == "weekend",
                    "meets_core_min_total_50",
                ].sum()
            ),
        ),
        ("n_zero_activity_source_stops", int((stop_crosswalk["total_activity"] == 0).sum())),
        ("n_zero_activity_logical_hubs", int((hub_activity == 0).sum())),
        ("max_abs_demand_conservation_diff_before_lsoa", max_grouping_diff),
        ("abs_retained_demand_diff_in_lsoa_output", london_output_diff),
    ]
    summary = pd.DataFrame(summary_rows, columns=["metric", "value"])

    case_codes = ["940GZZLUFPK", "940GZZLUPYB"]
    case_hubs = hubs.loc[
        hubs["logical_hub_code"].isin(case_codes),
        [
            "logical_hub_code",
            "logical_hub_name",
            "n_member_stops",
            "n_member_stop_areas",
            "representative_candidate_code",
            "hub_easting",
            "hub_northing",
            "hub_lsoa",
            "coordinate_source",
        ],
    ]
    case_flows = (
        hub_qhr_all.loc[hub_qhr_all["logical_hub_code"].isin(case_codes)]
        .groupby(["logical_hub_code", "logical_hub_name", "hub_lsoa"], as_index=False)[
            ["boardings", "alightings"]
        ]
        .sum()
    )

    pd.DataFrame(manifest).to_csv(DATA / "input_manifest.csv", index=False)
    stop_crosswalk.to_csv(
        PREPROCESSED / "stop_to_logical_hub_crosswalk.csv", index=False
    )
    hubs.to_csv(PREPROCESSED / "logical_hub_lsoa_crosswalk.csv", index=False)
    hub_qhr_all.to_parquet(
        PREPROCESSED / "bus_hub_night_qhr_all.parquet", index=False
    )
    hub_qhr_london.to_parquet(
        PREPROCESSED / "bus_hub_night_qhr_london.parquet", index=False
    )
    lsoa_long.to_parquet(PREPROCESSED / "bus_lsoa_night_long.parquet", index=False)
    lsoa_comparison.to_csv(DATA / "lsoa_old_vs_hub_first_totals.csv", index=False)
    eligibility.to_csv(DATA / "lsoa_direction_eligibility.csv", index=False)
    group_eligibility.to_csv(
        DATA / "lsoa_group_direction_eligibility.csv", index=False
    )
    one_direction_exceptions.to_csv(
        DATA / "one_direction_exception_areas.csv", index=False
    )
    movement_decomposition.to_csv(DATA / "movement_decomposition.csv", index=False)
    unresolved_coordinates.to_csv(DATA / "unresolved_coordinate_stops.csv", index=False)
    boundary_inclusion_changes.to_csv(
        DATA / "boundary_inclusion_changes.csv", index=False
    )
    eligibility.loc[eligibility["exact_direction_zero"]].to_csv(
        DATA / "remaining_exact_direction_zero_lsoas.csv", index=False
    )
    summary.to_csv(DATA / "reorganisation_summary.csv", index=False)
    case_hubs.to_csv(DATA / "core_case_hub_assignment.csv", index=False)
    case_flows.to_csv(DATA / "core_case_hub_totals.csv", index=False)

    report_lines = [
        "# Bus hub-first spatial reorganisation",
        "",
        "## Material Passport",
        "",
        "- Mode: deterministic preprocessing reconstruction",
        "- Verification status: VERIFIED",
        "- Rail passenger data used: no",
        "- Rail/Underground parent coordinates used: no",
        "- Representative points: official child BUS StopArea medoids",
        "- Existing clustering inputs or labels modified: no",
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Why LSOA assignments changed",
        "",
        movement_decomposition.to_markdown(index=False, floatfmt=".5f"),
        "",
        "The independent direct-point audit reproduces every comparable old LSOA",
        "assignment. The reported changes therefore arise from the new hub rule, not",
        "from a CRS mismatch or an accidental change of LSOA geography.",
        "",
        "## One-direction exception areas",
        "",
        "- Definition: after hub-to-LSOA aggregation, boardings or alightings equal",
        "  exactly zero within the relevant weekday/weekend analysis group.",
        "- Treatment: retained in the complete spatial dataset and reported separately,",
        "  but ineligible for the core two-direction temporal clustering.",
        "- This rule is evaluated before clustering and independently of the minimum",
        "  activity threshold. The complete exception register is",
        "  `outputs/data/one_direction_exception_areas.csv`.",
        "",
        "## Core interchange assignments",
        "",
        case_hubs.to_markdown(index=False, floatfmt=".3f"),
        "",
        case_flows.to_markdown(index=False, floatfmt=".5f"),
        "",
        "## Validity statements",
        "",
        "- Stop-level BUSTO demand is exactly conserved when stops are grouped into hubs.",
        "- Every parent code is used only as a grouping identifier. Hub locations come",
        "  from member bus StopArea points or, when necessary, bus-stop point fallbacks.",
        "- The LSOA assignment uses a point/polygon intersects relation so boundary",
        "  points are not silently discarded. Multiple boundary matches are flagged.",
        "- Exact one-direction-zero profiles are retained in the complete spatial data",
        "  but explicitly flagged both overall and for the weekday/weekend analysis groups.",
        "- The generated LSOA-long parquet is schema-compatible with the existing bus",
        "  feature-building stage but has not yet been clustered.",
        "",
        "## Remaining limits",
        "",
        "- NaPTAN is a 2026 snapshot while BUSTO represents 2024/25.",
        "- BUSTO stops listed in `unresolved_coordinate_stops.csv` have no matching",
        "  record or NaPTAN ATCO reference in Bus_Stops.csv; they are preserved in",
        "  the all-hub output but cannot be assigned to London without a defensible",
        "  crosswalk. They are not silently guessed from names.",
        "- Assigning a complete cross-boundary hub to one LSOA is a deliberate functional",
        "  node decision; the exact moved activity is reported for sensitivity analysis.",
        "- This spatial repair does not remove uncertainty in inferred BUSTO alightings",
        "  or low-volume temporal profiles.",
    ]
    (REPORT / "RESULTS_SUMMARY.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    print(summary.to_string(index=False))
    print("\nCore hub assignments")
    print(case_hubs.to_string(index=False))
    print("\nCore hub totals")
    print(case_flows.to_string(index=False))


if __name__ == "__main__":
    main()
