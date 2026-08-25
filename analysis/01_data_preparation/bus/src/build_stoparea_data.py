# -*- coding: utf-8 -*-
"""Build the canonical child-StopArea-to-LSOA night-bus data products.

The grouping unit is the NaPTAN child StopArea referenced by each StopPoint.
ParentStopAreaRef is never followed for grouping, coordinates, or LSOA
assignment; it is retained only as audit metadata.
"""
from __future__ import annotations

import hashlib
import os
import platform
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[4]
SOURCE_ROOT = Path(os.environ.get("CASA_FYP_SOURCE_ROOT", FYP / "authorised_data")).expanduser().resolve()

NAPTAN_DIR = SOURCE_ROOT / "巴士数据" / "NaPTAN_data"
BUS_STOPS_CSV = SOURCE_ROOT / "巴士数据" / "Bus_Stops.csv"
# Adopted 18:00-05:00 source table.
STOP_FLOW_PARQUET = (
    FYP / "outputs" / "preprocessed_busto_1805_min33" / "busto_stop_qhr_night.parquet"
)
LSOA_GEOJSON = SOURCE_ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"

OUT = ROOT / "outputs_1805_min33"
PRE = OUT / "preprocessed"
DATA = OUT / "data"
AUDIT = OUT / "audit"
REPORT = OUT / "report"

NS = {"n": "http://www.naptan.org.uk/"}
CRS_BNG = "EPSG:27700"
BUS_DIRECTIONS = ["boardings", "alightings"]
FLOAT_TOLERANCE = 1e-6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_row(label: str, path: Path, rows: int | None, detail: str = "") -> dict:
    return {
        "input": label,
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "rows": rows,
        "detail": detail,
    }


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
            manifest_row(
                "naptan_xml",
                path,
                None,
                (
                    f"FileName={root.attrib.get('FileName', '')}; "
                    f"CreationDateTime={root.attrib.get('CreationDateTime', '')}; "
                    f"SchemaVersion={root.attrib.get('SchemaVersion', '')}"
                ),
            )
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
                    "area_easting": child_text(area, ".//n:Location//n:Easting"),
                    "area_northing": child_text(area, ".//n:Location//n:Northing"),
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
        raise RuntimeError(f"Conflicting child StopAreaRef values: {examples}")

    area_conflicts = (
        areas.dropna(subset=["stop_area_code"])
        .groupby("stop_area_code")
        .agg(
            n_parent=("parent_stop_area_code", lambda x: x.nunique(dropna=False)),
            n_easting=("area_easting", lambda x: x.nunique(dropna=False)),
            n_northing=("area_northing", lambda x: x.nunique(dropna=False)),
        )
    )
    conflicts = area_conflicts.max(axis=1) > 1
    if conflicts.any():
        examples = area_conflicts[conflicts].head().index.tolist()
        raise RuntimeError(f"Conflicting StopArea definitions: {examples}")

    points = points.drop_duplicates("atco_code", keep="last")
    areas = areas.drop_duplicates("stop_area_code", keep="last")
    return points, areas, manifest


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
            .rename(
                columns={
                    "stop_area_code": "candidate_code",
                    "area_easting": "candidate_easting",
                    "area_northing": "candidate_northing",
                }
            )
        )
        stop_candidates = (
            members.dropna(subset=["STOP_CODE", "OS_EASTING", "OS_NORTHING"])
            [["STOP_CODE", "OS_EASTING", "OS_NORTHING"]]
            .drop_duplicates()
            .rename(
                columns={
                    "STOP_CODE": "candidate_code",
                    "OS_EASTING": "candidate_easting",
                    "OS_NORTHING": "candidate_northing",
                }
            )
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
            chosen = pd.Series(
                {
                    "candidate_code": None,
                    "candidate_easting": np.nan,
                    "candidate_northing": np.nan,
                }
            )
            coordinate_source = "missing"
            n_candidates = 0

        area_names = members["stop_area_name"].dropna()
        stop_names = members["STOP_NAME"].dropna()
        unit_name = (
            area_names.mode().iloc[0]
            if not area_names.empty
            else stop_names.mode().iloc[0]
            if not stop_names.empty
            else ""
        )
        rows.append(
            {
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
            }
        )
    return pd.DataFrame(rows)


def assign_units_to_lsoa(units: pd.DataFrame) -> pd.DataFrame:
    lsoa = gpd.read_file(LSOA_GEOJSON)
    code_column = next(col for col in lsoa.columns if col.lower() == "lsoa21cd")
    lsoa = lsoa[[code_column, "geometry"]].to_crs(CRS_BNG)

    valid = units.dropna(subset=["unit_easting", "unit_northing"]).copy()
    unit_gdf = gpd.GeoDataFrame(
        valid,
        geometry=gpd.points_from_xy(valid["unit_easting"], valid["unit_northing"]),
        crs=CRS_BNG,
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
        lsoa_long.groupby(["lsoa", "direction"], as_index=False)["count"]
        .sum()
        .pivot(index="lsoa", columns="direction", values="count")
        .fillna(0.0)
        .reset_index()
    )
    for direction in BUS_DIRECTIONS:
        if direction not in totals:
            totals[direction] = 0.0
    totals["total_activity"] = totals["boardings"] + totals["alightings"]
    totals["exact_direction_zero"] = (
        ((totals["boardings"] == 0) & (totals["alightings"] > 0))
        | ((totals["alightings"] == 0) & (totals["boardings"] > 0))
    )
    return totals


def build_stop_crosswalk(
    points: pd.DataFrame,
    areas: pd.DataFrame,
    bus_stops: pd.DataFrame,
    flow: pd.DataFrame,
) -> pd.DataFrame:
    used_stops = pd.DataFrame({"STOP_CODE": sorted(flow["stopcode"].unique())})
    stop_totals = (
        flow.groupby("stopcode", as_index=False)[BUS_DIRECTIONS]
        .sum()
        .rename(columns={"stopcode": "STOP_CODE"})
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
            validate="one_to_one",
        )
        .merge(
            points,
            left_on="NAPTAN_ATCO",
            right_on="atco_code",
            how="left",
            validate="many_to_one",
        )
        .merge(
            areas,
            on="stop_area_code",
            how="left",
            suffixes=("", "_area"),
            validate="many_to_one",
        )
    )
    stop_crosswalk = stop_crosswalk.merge(
        stop_totals,
        on="STOP_CODE",
        how="left",
        validate="one_to_one",
    )
    stop_crosswalk["total_activity"] = stop_crosswalk[BUS_DIRECTIONS].sum(axis=1)
    has_area = stop_crosswalk["stop_area_code"].notna()
    stop_crosswalk["stoparea_unit_code"] = np.where(
        has_area,
        "AREA::" + stop_crosswalk["stop_area_code"].fillna("").astype(str),
        "STOP::" + stop_crosswalk["STOP_CODE"],
    )
    return stop_crosswalk


def main() -> None:
    for directory in [OUT, PRE, DATA, AUDIT, REPORT]:
        directory.mkdir(parents=True, exist_ok=True)

    xml_paths = sorted(NAPTAN_DIR.glob("*.xml"))
    if not xml_paths:
        raise FileNotFoundError(f"No NaPTAN XML files found under {NAPTAN_DIR}")
    for required in [BUS_STOPS_CSV, STOP_FLOW_PARQUET, LSOA_GEOJSON]:
        if not required.exists():
            raise FileNotFoundError(required)

    points, areas, manifest = parse_naptan(xml_paths)
    bus_stops = pd.read_csv(BUS_STOPS_CSV, dtype=str)
    bus_stops["STOP_CODE"] = bus_stops["STOP_CODE"].astype(str)
    bus_stops["NAPTAN_ATCO"] = bus_stops["NAPTAN_ATCO"].str.strip()
    for column in ["OS_EASTING", "OS_NORTHING"]:
        bus_stops[column] = pd.to_numeric(bus_stops[column], errors="coerce")
    if bus_stops["STOP_CODE"].duplicated().any():
        raise RuntimeError("Bus_Stops.csv contains duplicate STOP_CODE values.")

    flow = pd.read_parquet(STOP_FLOW_PARQUET).copy()
    required_flow_columns = {
        "stopcode",
        "day_type",
        "traffic_minute",
        "boardings",
        "alightings",
    }
    missing_columns = required_flow_columns - set(flow.columns)
    if missing_columns:
        raise RuntimeError(f"Stop-flow input is missing columns: {sorted(missing_columns)}")
    flow["stopcode"] = flow["stopcode"].astype(str)

    manifest.extend(
        [
            manifest_row("bus_stops", BUS_STOPS_CSV, len(bus_stops)),
            manifest_row("stop_level_night_flow", STOP_FLOW_PARQUET, len(flow)),
            manifest_row("lsoa21_boundaries", LSOA_GEOJSON, None),
        ]
    )
    stops = build_stop_crosswalk(points, areas, bus_stops, flow)
    if stops["STOP_CODE"].duplicated().any():
        raise RuntimeError("Generated stop crosswalk contains duplicate STOP_CODE values.")
    if set(flow["stopcode"].unique()) != set(stops["STOP_CODE"]):
        raise RuntimeError("Flow stops do not exactly match the generated stop crosswalk.")

    units = assign_units_to_lsoa(build_units(stops))
    stops = stops.merge(
        units[
            [
                "stoparea_unit_code",
                "representative_candidate_code",
                "unit_easting",
                "unit_northing",
                "coordinate_source",
                "stoparea_lsoa",
                "lsoa_match",
                "boundary_multiple_match",
            ]
        ],
        on="stoparea_unit_code",
        how="left",
        validate="many_to_one",
    )
    flow_with_unit = flow.merge(
        stops[["STOP_CODE", "stoparea_unit_code"]].rename(
            columns={"STOP_CODE": "stopcode"}
        ),
        on="stopcode",
        how="left",
        validate="many_to_one",
    )
    if flow_with_unit["stoparea_unit_code"].isna().any():
        raise RuntimeError("Some flow rows were not assigned to a StopArea unit.")

    unit_qhr_all = (
        flow_with_unit.groupby(
            ["stoparea_unit_code", "day_type", "traffic_minute"], as_index=False
        )[BUS_DIRECTIONS]
        .sum()
        .merge(
            units[
                [
                    "stoparea_unit_code",
                    "stoparea_unit_name",
                    "stoparea_lsoa",
                    "unit_easting",
                    "unit_northing",
                    "coordinate_source",
                ]
            ],
            on="stoparea_unit_code",
            how="left",
            validate="many_to_one",
        )
    )
    source_totals = flow[BUS_DIRECTIONS].sum()
    grouped_totals = unit_qhr_all[BUS_DIRECTIONS].sum()
    grouping_diff = float((source_totals - grouped_totals).abs().max())
    if grouping_diff > FLOAT_TOLERANCE:
        raise RuntimeError(f"StopArea aggregation failed demand conservation: {grouping_diff}")

    unit_qhr_london = unit_qhr_all.dropna(subset=["stoparea_lsoa"]).copy()
    unit_qhr_london["hour_bin"] = (unit_qhr_london["traffic_minute"] // 60) * 60
    lsoa_hourly = (
        unit_qhr_london.groupby(
            ["stoparea_lsoa", "day_type", "hour_bin"], as_index=False
        )[BUS_DIRECTIONS]
        .sum()
        .rename(columns={"stoparea_lsoa": "lsoa"})
    )
    lsoa_long = lsoa_hourly.melt(
        id_vars=["day_type", "lsoa", "hour_bin"],
        value_vars=BUS_DIRECTIONS,
        var_name="direction",
        value_name="count",
    )[["day_type", "direction", "lsoa", "hour_bin", "count"]]

    retained_stop_activity = float(
        stops.loc[stops["stoparea_lsoa"].notna(), "total_activity"].sum()
    )
    output_diff = abs(float(lsoa_long["count"].sum()) - retained_stop_activity)
    if output_diff > FLOAT_TOLERANCE:
        raise RuntimeError(f"LSOA output failed demand conservation: {output_diff}")

    totals = direction_totals(lsoa_long)
    has_area = stops["stop_area_code"].notna()
    summary_rows = [
        ("n_busto_used_stops", len(stops)),
        ("n_stoparea_units", len(units)),
        ("n_official_child_stopareas", int(stops["stop_area_code"].nunique())),
        ("n_singleton_stop_units", int((~has_area).sum())),
        (
            "n_units_official_child_coordinate",
            int((units["coordinate_source"] == "official_child_stoparea").sum()),
        ),
        (
            "n_units_stop_point_fallback",
            int((units["coordinate_source"] == "bus_stop_point_medoid_fallback").sum()),
        ),
        (
            "n_units_missing_coordinates",
            int((units["coordinate_source"] == "missing").sum()),
        ),
        ("n_units_assigned_london_lsoa", int(units["lsoa_match"].sum())),
        (
            "n_units_boundary_multiple_match",
            int(units["boundary_multiple_match"].sum()),
        ),
        ("n_lsoa_with_rows", int(totals["lsoa"].nunique())),
        (
            "n_lsoa_positive_activity",
            int((totals["total_activity"] > 0).sum()),
        ),
        (
            "n_lsoa_exact_direction_zero",
            int(totals["exact_direction_zero"].sum()),
        ),
        ("max_abs_demand_conservation_diff_before_lsoa", grouping_diff),
        ("abs_retained_demand_diff_in_lsoa_output", output_diff),
    ]
    summary = pd.DataFrame(summary_rows, columns=["metric", "value"])

    stops.to_csv(PRE / "stop_to_stoparea_crosswalk.csv", index=False)
    units.to_csv(PRE / "stoparea_unit_lsoa_crosswalk.csv", index=False)
    unit_qhr_all.to_parquet(PRE / "bus_stoparea_night_qhr_all.parquet", index=False)
    unit_qhr_london.to_parquet(
        PRE / "bus_stoparea_night_qhr_london.parquet", index=False
    )
    lsoa_long.to_parquet(PRE / "bus_lsoa_night_long.parquet", index=False)
    totals.to_csv(DATA / "lsoa_direction_totals.csv", index=False)
    summary.to_csv(DATA / "preprocessing_summary.csv", index=False)
    pd.DataFrame(manifest).to_csv(AUDIT / "input_manifest.csv", index=False)
    pd.DataFrame(
        [
            ("python", platform.python_version()),
            ("pandas", pd.__version__),
            ("numpy", np.__version__),
            ("geopandas", gpd.__version__),
            ("platform", platform.platform()),
        ],
        columns=["component", "version"],
    ).to_csv(AUDIT / "runtime_versions.csv", index=False)

    report = [
        "# Bus child-StopArea preprocessing",
        "",
        "## Method boundary",
        "",
        "- Grouping unit: NaPTAN child `StopAreaRef`; missing references use singleton stops.",
        "- `ParentStopAreaRef` is audit metadata only and is not followed.",
        "- Coordinates: official child StopArea, then member-stop medoid fallback.",
        "- LSOA assignment: London LSOA 2021, EPSG:27700, `intersects`.",
        "- No clustering, Bayesian smoothing, activity filtering, or feature normalization.",
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Conservation checks",
        "",
        f"- Maximum absolute direction difference before LSOA assignment: `{grouping_diff:.12g}`.",
        f"- Absolute retained-demand difference in LSOA output: `{output_diff:.12g}`.",
        "",
        "## Provenance",
        "",
        "Exact input paths, sizes and SHA-256 hashes are recorded in `../audit/input_manifest.csv`.",
    ]
    (REPORT / "STOPAREA_PREPROCESSING.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
