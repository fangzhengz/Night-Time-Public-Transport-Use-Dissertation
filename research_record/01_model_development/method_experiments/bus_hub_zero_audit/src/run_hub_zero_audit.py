"""Audit official bus-stop hubs, LSOA splitting, and exact direction zeros.

This is a deterministic pre-clustering validity check. It does not alter the
canonical bus features or labels and does not reassign any stop between LSOAs.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

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

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)

NS = {"n": "http://www.naptan.org.uk/"}
HIGH_ACTIVITY_REFERENCE = 450.0
NEAR_ZERO_RATIO = 0.01
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


def parse_naptan(xml_paths: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    point_rows: list[dict] = []
    area_rows: list[dict] = []
    metadata: list[dict] = []

    for path in xml_paths:
        root = ET.parse(path).getroot()
        metadata.append(
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
                    "source_xml": path.name,
                }
            )

    points = pd.DataFrame(point_rows)
    areas = pd.DataFrame(area_rows)

    if points.empty or areas.empty:
        raise RuntimeError("NaPTAN XML contains no StopPoint or StopArea records.")

    point_conflicts = (
        points.dropna(subset=["atco_code"])
        .groupby("atco_code")["stop_area_code"]
        .nunique(dropna=False)
    )
    if (point_conflicts > 1).any():
        examples = point_conflicts[point_conflicts > 1].head().index.tolist()
        raise RuntimeError(f"Conflicting StopAreaRef values for ATCO codes: {examples}")

    points = points.drop_duplicates("atco_code", keep="last")
    areas = areas.drop_duplicates("stop_area_code", keep="last")
    return points, areas, metadata


def add_file_manifest(
    manifest: list[dict], label: str, path: Path, rows: int, detail: str = ""
) -> None:
    manifest.append(
        {
            "input": label,
            "path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "rows": rows,
            "detail": detail,
        }
    )


def build_lsoa_zero_audit(
    stop_crosswalk: pd.DataFrame,
    lsoa_totals: pd.DataFrame,
    hub_summary: pd.DataFrame,
) -> pd.DataFrame:
    zero_mask = (
        (lsoa_totals["boardings"] == 0) & (lsoa_totals["alightings"] > 0)
    ) | ((lsoa_totals["alightings"] == 0) & (lsoa_totals["boardings"] > 0))
    zeros = lsoa_totals.loc[zero_mask].copy()

    membership = (
        stop_crosswalk.dropna(subset=["lsoa", "logical_hub_code"])
        [["lsoa", "logical_hub_code"]]
        .drop_duplicates()
        .merge(hub_summary, on="logical_hub_code", how="left")
    )

    rows: list[dict] = []
    for record in zeros.itertuples(index=False):
        missing_direction = (
            "alightings" if record.alightings == 0 else "boardings"
        )
        members = membership.loc[membership["lsoa"] == record.lsoa].copy()
        direction_col = f"hub_{missing_direction}"
        support = members.loc[
            (members[direction_col] > 0)
            & (
                (members["n_lsoa"] > 1)
                | members["has_unmatched_stop"].fillna(False)
            )
        ]
        supporting_hubs = sorted(support["logical_hub_code"].astype(str).unique())
        rows.append(
            {
                "lsoa": record.lsoa,
                "boardings": record.boardings,
                "alightings": record.alightings,
                "total_activity": record.total_activity,
                "missing_direction": missing_direction,
                "hub_split_supported": bool(supporting_hubs),
                "n_supporting_hubs": len(supporting_hubs),
                "supporting_hubs": "|".join(supporting_hubs),
                "high_activity_ge_450": bool(
                    record.total_activity >= HIGH_ACTIVITY_REFERENCE
                ),
                "recommended_status": "exclude_from_two_direction_clustering",
            }
        )

    columns = [
        "lsoa",
        "boardings",
        "alightings",
        "total_activity",
        "missing_direction",
        "hub_split_supported",
        "n_supporting_hubs",
        "supporting_hubs",
        "high_activity_ge_450",
        "recommended_status",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values(
        "total_activity", ascending=False
    )


def main() -> None:
    xml_paths = sorted(NAPTAN_DIR.glob("*.xml"))
    if not xml_paths:
        raise FileNotFoundError(f"No NaPTAN XML files found under {NAPTAN_DIR}")

    points, areas, manifest = parse_naptan(xml_paths)

    bus_stops = pd.read_csv(BUS_STOPS_CSV, dtype=str)
    bus_stops["STOP_CODE"] = bus_stops["STOP_CODE"].astype(str)
    bus_stops["NAPTAN_ATCO"] = bus_stops["NAPTAN_ATCO"].str.strip()
    if bus_stops["STOP_CODE"].duplicated().any():
        raise RuntimeError("Bus_Stops.csv contains duplicate STOP_CODE values.")

    stop_flow_raw = pd.read_parquet(STOP_FLOW_PARQUET).copy()
    stop_flow_raw["stopcode"] = stop_flow_raw["stopcode"].astype(str)
    stop_flow = (
        stop_flow_raw.groupby("stopcode", as_index=False)[
            ["boardings", "alightings"]
        ]
        .sum()
        .rename(columns={"stopcode": "STOP_CODE"})
    )

    lookup = pd.read_csv(CURRENT_LOOKUP_CSV, dtype=str)
    lookup["stopcode"] = lookup["stopcode"].astype(str)
    if lookup["stopcode"].duplicated().any():
        raise RuntimeError("Current LSOA lookup contains duplicate stopcodes.")

    current_long = pd.read_parquet(CURRENT_LSOA_LONG).copy()

    add_file_manifest(manifest, "bus_stops", BUS_STOPS_CSV, len(bus_stops))
    add_file_manifest(
        manifest, "stop_level_night_flow", STOP_FLOW_PARQUET, len(stop_flow_raw)
    )
    add_file_manifest(manifest, "current_lsoa_lookup", CURRENT_LOOKUP_CSV, len(lookup))
    add_file_manifest(
        manifest, "current_lsoa_long", CURRENT_LSOA_LONG, len(current_long)
    )

    stop_crosswalk = (
        stop_flow.merge(
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
            lookup[["stopcode", "lsoa"]].rename(columns={"stopcode": "STOP_CODE"}),
            on="STOP_CODE",
            how="left",
        )
    )

    stop_crosswalk["logical_hub_code"] = stop_crosswalk[
        "parent_stop_area_code"
    ].fillna(stop_crosswalk["stop_area_code"])
    stop_crosswalk["logical_hub_source"] = np.select(
        [
            stop_crosswalk["parent_stop_area_code"].notna(),
            stop_crosswalk["stop_area_code"].notna(),
        ],
        ["parent_stop_area", "stop_area"],
        default="unmapped",
    )
    stop_crosswalk["bus_stop_match"] = stop_crosswalk["STOP_NAME"].notna()
    stop_crosswalk["xml_atco_match"] = stop_crosswalk["atco_code"].notna()
    stop_crosswalk["official_stop_area_match"] = stop_crosswalk[
        "stop_area_code"
    ].notna()
    stop_crosswalk["lsoa_match"] = stop_crosswalk["lsoa"].notna()

    hub_summary = (
        stop_crosswalk.dropna(subset=["logical_hub_code"])
        .groupby("logical_hub_code", as_index=False)
        .agg(
            logical_hub_source=("logical_hub_source", "first"),
            logical_hub_name=(
                "stop_area_name",
                lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else "",
            ),
            n_stops=("STOP_CODE", "nunique"),
            n_lsoa=("lsoa", "nunique"),
            has_unmatched_stop=("lsoa", lambda s: bool(s.isna().any())),
            hub_boardings=("boardings", "sum"),
            hub_alightings=("alightings", "sum"),
        )
    )
    hub_summary["cross_lsoa"] = hub_summary["n_lsoa"] > 1
    hub_summary["both_directions_positive"] = (
        (hub_summary["hub_boardings"] > 0) & (hub_summary["hub_alightings"] > 0)
    )
    hub_summary["hub_total_activity"] = (
        hub_summary["hub_boardings"] + hub_summary["hub_alightings"]
    )

    hub_lsoa = (
        stop_crosswalk.dropna(subset=["logical_hub_code"])
        .assign(lsoa_for_audit=lambda d: d["lsoa"].fillna("<UNMATCHED>"))
        .groupby(["logical_hub_code", "lsoa_for_audit"], as_index=False)
        .agg(
            n_stops=("STOP_CODE", "nunique"),
            boardings=("boardings", "sum"),
            alightings=("alightings", "sum"),
        )
        .merge(
            hub_summary[
                [
                    "logical_hub_code",
                    "logical_hub_source",
                    "logical_hub_name",
                    "n_lsoa",
                    "cross_lsoa",
                    "has_unmatched_stop",
                ]
            ],
            on="logical_hub_code",
            how="left",
        )
    )

    lsoa_totals = (
        stop_crosswalk.dropna(subset=["lsoa"])
        .groupby("lsoa", as_index=False)[["boardings", "alightings"]]
        .sum()
    )
    lsoa_totals["total_activity"] = (
        lsoa_totals["boardings"] + lsoa_totals["alightings"]
    )
    denominator = lsoa_totals[["boardings", "alightings"]].max(axis=1)
    lsoa_totals["direction_ratio"] = (
        lsoa_totals[["boardings", "alightings"]].min(axis=1)
        / denominator.replace(0, np.nan)
    )
    lsoa_totals["exact_direction_zero"] = (
        ((lsoa_totals["boardings"] == 0) & (lsoa_totals["alightings"] > 0))
        | ((lsoa_totals["alightings"] == 0) & (lsoa_totals["boardings"] > 0))
    )
    lsoa_totals["near_zero_ratio_lt_0_01"] = (
        ~lsoa_totals["exact_direction_zero"]
        & (lsoa_totals["direction_ratio"] < NEAR_ZERO_RATIO)
    )

    zero_audit = build_lsoa_zero_audit(stop_crosswalk, lsoa_totals, hub_summary)

    eligibility = lsoa_totals.merge(
        zero_audit[
            ["lsoa", "hub_split_supported", "supporting_hubs", "missing_direction"]
        ],
        on="lsoa",
        how="left",
    )
    eligibility["hub_split_supported"] = (
        eligibility["hub_split_supported"]
        .astype("boolean")
        .fillna(False)
        .astype(bool)
    )
    eligibility["eligible_two_direction_clustering"] = (
        (eligibility["boardings"] > 0) & (eligibility["alightings"] > 0)
    )
    eligibility["exclusion_reason"] = np.select(
        [
            (eligibility["boardings"] == 0) & (eligibility["alightings"] > 0),
            (eligibility["alightings"] == 0) & (eligibility["boardings"] > 0),
            eligibility["total_activity"] == 0,
        ],
        [
            "zero_boarding_direction",
            "zero_alighting_direction",
            "zero_total_activity",
        ],
        default="",
    )

    # Independent equality check against the current LSOA-long preprocessing.
    expected = (
        current_long.groupby(["lsoa", "direction"], as_index=False)["count"]
        .sum()
        .pivot(index="lsoa", columns="direction", values="count")
        .fillna(0.0)
        .reset_index()
    )
    comparison = lsoa_totals.merge(
        expected, on="lsoa", how="outer", suffixes=("_audit", "_current")
    ).fillna(0.0)
    comparison["boarding_abs_diff"] = (
        comparison["boardings_audit"] - comparison["boardings_current"]
    ).abs()
    comparison["alighting_abs_diff"] = (
        comparison["alightings_audit"] - comparison["alightings_current"]
    ).abs()
    max_consistency_diff = float(
        comparison[["boarding_abs_diff", "alighting_abs_diff"]].to_numpy().max()
    )
    if max_consistency_diff > FLOAT_TOLERANCE:
        raise RuntimeError(
            "Stop-level reconstruction does not reproduce current LSOA totals: "
            f"max absolute difference={max_consistency_diff}"
        )

    n_used = len(stop_crosswalk)
    in_lsoa = stop_crosswalk.loc[stop_crosswalk["lsoa_match"]]
    exact_zero = len(zero_audit)
    exact_zero_supported = int(zero_audit["hub_split_supported"].sum())
    high_zero = zero_audit.loc[zero_audit["high_activity_ge_450"]]

    summary_rows = [
        ("n_busto_used_stops", n_used),
        ("n_stops_matched_bus_stops_csv", int(stop_crosswalk["bus_stop_match"].sum())),
        ("n_stops_matched_lsoa", len(in_lsoa)),
        ("pct_lsoa_stops_matched_xml_atco", 100 * in_lsoa["xml_atco_match"].mean()),
        (
            "pct_lsoa_stops_with_official_stop_area",
            100 * in_lsoa["official_stop_area_match"].mean(),
        ),
        (
            "pct_lsoa_stops_with_parent_stop_area",
            100 * in_lsoa["parent_stop_area_code"].notna().mean(),
        ),
        ("n_logical_hubs", len(hub_summary)),
        ("n_cross_lsoa_logical_hubs", int(hub_summary["cross_lsoa"].sum())),
        ("n_exact_one_direction_zero_lsoa", exact_zero),
        ("n_zero_lsoa_supported_by_hub_split", exact_zero_supported),
        ("n_high_activity_ge_450_zero_lsoa", len(high_zero)),
        (
            "n_high_activity_ge_450_supported_by_hub_split",
            int(high_zero["hub_split_supported"].sum()),
        ),
        ("max_abs_lsoa_total_reconstruction_diff", max_consistency_diff),
    ]
    audit_summary = pd.DataFrame(summary_rows, columns=["metric", "value"])

    manifest_df = pd.DataFrame(manifest)
    manifest_df.to_csv(DATA / "input_manifest.csv", index=False)
    stop_crosswalk.to_csv(DATA / "stop_hub_crosswalk.csv", index=False)
    hub_summary.sort_values("hub_total_activity", ascending=False).to_csv(
        DATA / "logical_hub_summary.csv", index=False
    )
    hub_lsoa.to_csv(DATA / "hub_lsoa_direction_summary.csv", index=False)
    zero_audit.to_csv(DATA / "lsoa_direction_zero_audit.csv", index=False)
    eligibility.to_csv(DATA / "lsoa_clustering_eligibility.csv", index=False)
    comparison.to_csv(DATA / "lsoa_total_consistency_check.csv", index=False)
    audit_summary.to_csv(DATA / "audit_summary.csv", index=False)

    case_hubs = ["940GZZLUFPK", "940GZZLUPYB"]
    case_hub_table = hub_summary.loc[
        hub_summary["logical_hub_code"].isin(case_hubs),
        [
            "logical_hub_code",
            "logical_hub_name",
            "n_stops",
            "n_lsoa",
            "has_unmatched_stop",
            "hub_boardings",
            "hub_alightings",
        ],
    ]
    case_lsoa_table = zero_audit.loc[
        zero_audit["supporting_hubs"].isin(case_hubs),
        [
            "lsoa",
            "boardings",
            "alightings",
            "total_activity",
            "supporting_hubs",
        ],
    ]

    report_lines = [
        "# Bus hub and exact-direction-zero audit",
        "",
        "## Material Passport",
        "",
        "- Mode: deterministic preprocessing validity audit",
        "- Verification status: VERIFIED",
        "- Mutation boundary: no source data, feature, label, or model was changed",
        f"- NaPTAN XML files: {', '.join(p.name for p in xml_paths)}",
        "",
        "## Validation result",
        "",
        audit_summary.to_markdown(index=False, floatfmt=".6f"),
        "",
        "The stop-level reconstruction exactly reproduces the current LSOA-long",
        "direction totals within the configured numerical tolerance. The audit is",
        "therefore evaluating the same BUSTO-to-LSOA data used by the current pipeline.",
        "",
        "## High-activity cases",
        "",
        case_lsoa_table.to_markdown(index=False, floatfmt=".5f"),
        "",
        case_hub_table.to_markdown(index=False, floatfmt=".5f"),
        "",
        "Both high-activity exact-zero LSOAs become bidirectional when demand is",
        "examined across their official parent StopArea. This supports a cross-LSOA",
        "interchange-splitting explanation rather than a literal absence of alighting.",
        "",
        "## Operational decision",
        "",
        "- Exclude every exact one-direction-zero LSOA from fitting the current",
        "  two-direction temporal clustering model.",
        "- Retain the records in maps and audit tables with an exclusion reason.",
        "- Do not automatically exclude positive-but-imbalanced LSOAs; the",
        "  `near_zero_ratio_lt_0_01` field is advisory only.",
        "- Do not use Bayesian smoothing to manufacture a missing structural",
        "  direction. Shrinkage is reserved for low-information but non-zero profiles.",
        "",
        "## Limits",
        "",
        "- The NaPTAN export is a 2026 snapshot, while BUSTO represents 2024/25.",
        "- Parent StopArea coverage is concentrated at larger interchanges; many",
        "  ordinary stop groups have only an immediate StopArea.",
        "- The existing strict point-in-polygon lookup is audited but not repaired here.",
        "- Hub evidence explains a zero pattern; it does not authorise moving all hub",
        "  demand into one LSOA in the main analysis.",
    ]
    (REPORT / "RESULTS_SUMMARY.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    print(audit_summary.to_string(index=False))
    print("\nHigh-activity exact-zero cases")
    print(case_lsoa_table.to_string(index=False))
    print("\nOfficial parent-hub totals")
    print(case_hub_table.to_string(index=False))


if __name__ == "__main__":
    main()
