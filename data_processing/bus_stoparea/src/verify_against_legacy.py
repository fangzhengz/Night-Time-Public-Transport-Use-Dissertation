# -*- coding: utf-8 -*-
"""Compare canonical StopArea data products with the previous isolated test."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[3]
NEW_PRE = ROOT / "outputs" / "preprocessed"
AUDIT = ROOT / "outputs" / "audit"
REPORT = ROOT / "outputs" / "report"
LEGACY_PRE = (
    FYP / "rq1_bus_stoparea_only_isolated_test" / "outputs" / "preprocessed"
)
FLOAT_TOLERANCE = 1e-6


def compare_frame(
    name: str,
    new: pd.DataFrame,
    legacy: pd.DataFrame,
    keys: list[str],
) -> dict:
    new = new.sort_values(keys).reset_index(drop=True)
    legacy = legacy.sort_values(keys).reset_index(drop=True)
    same_columns = list(new.columns) == list(legacy.columns)
    same_shape = new.shape == legacy.shape
    max_numeric_diff = np.nan
    values_equal = False
    detail = ""
    if same_columns and same_shape:
        numeric = new.select_dtypes(include=[np.number]).columns.tolist()
        if numeric:
            left = new[numeric].to_numpy(dtype=float)
            right = legacy[numeric].to_numpy(dtype=float)
            max_numeric_diff = float(
                np.nanmax(np.abs(left - right))
                if left.size
                else 0.0
            )
        nonnumeric = [column for column in new.columns if column not in numeric]
        numeric_equal = (
            True
            if not numeric
            else np.allclose(
                new[numeric].to_numpy(dtype=float),
                legacy[numeric].to_numpy(dtype=float),
                rtol=0,
                atol=FLOAT_TOLERANCE,
                equal_nan=True,
            )
        )
        text_equal = (
            True
            if not nonnumeric
            else new[nonnumeric].fillna("<NA>").astype(str).equals(
                legacy[nonnumeric].fillna("<NA>").astype(str)
            )
        )
        values_equal = numeric_equal and text_equal
        if not values_equal:
            detail = "At least one aligned value differs."
    else:
        detail = (
            f"new_shape={new.shape}; legacy_shape={legacy.shape}; "
            f"new_columns={list(new.columns)}; legacy_columns={list(legacy.columns)}"
        )
    return {
        "comparison": name,
        "same_columns": same_columns,
        "same_shape": same_shape,
        "values_equal_within_1e-6": values_equal,
        "max_abs_numeric_diff": max_numeric_diff,
        "detail": detail,
    }


def main() -> None:
    for directory in [AUDIT, REPORT]:
        directory.mkdir(parents=True, exist_ok=True)
    for directory in [NEW_PRE, LEGACY_PRE]:
        if not directory.exists():
            raise FileNotFoundError(directory)

    results: list[dict] = []
    for filename, keys in [
        (
            "bus_lsoa_night_long.parquet",
            ["day_type", "direction", "lsoa", "hour_bin"],
        ),
        (
            "bus_stoparea_night_qhr_all.parquet",
            ["stoparea_unit_code", "day_type", "traffic_minute"],
        ),
        (
            "bus_stoparea_night_qhr_london.parquet",
            ["stoparea_unit_code", "day_type", "traffic_minute"],
        ),
    ]:
        results.append(
            compare_frame(
                filename,
                pd.read_parquet(NEW_PRE / filename),
                pd.read_parquet(LEGACY_PRE / filename),
                keys,
            )
        )

    unit_filename = "stoparea_unit_lsoa_crosswalk.csv"
    results.append(
        compare_frame(
            unit_filename,
            pd.read_csv(NEW_PRE / unit_filename, dtype={"stoparea_unit_code": str}),
            pd.read_csv(LEGACY_PRE / unit_filename, dtype={"stoparea_unit_code": str}),
            ["stoparea_unit_code"],
        )
    )

    new_stops = pd.read_csv(
        NEW_PRE / "stop_to_stoparea_crosswalk.csv", dtype={"STOP_CODE": str}
    )
    legacy_stops = pd.read_csv(
        LEGACY_PRE / "stop_to_stoparea_crosswalk.csv", dtype={"STOP_CODE": str}
    ).rename(
        columns={
            "representative_candidate_code_y": "representative_candidate_code",
            "coordinate_source_y": "coordinate_source",
            "boundary_multiple_match_y": "boundary_multiple_match",
        }
    )
    stop_columns = [
        "STOP_CODE",
        "stop_area_code",
        "old_lsoa",
        "boardings",
        "alightings",
        "total_activity",
        "stoparea_unit_code",
        "representative_candidate_code",
        "unit_easting",
        "unit_northing",
        "coordinate_source",
        "stoparea_lsoa",
        "lsoa_match",
        "boundary_multiple_match",
        "changed_vs_original",
        "newly_included_vs_original",
        "newly_excluded_vs_original",
    ]
    results.append(
        compare_frame(
            "stop_to_stoparea_crosswalk_core_fields",
            new_stops[stop_columns],
            legacy_stops[stop_columns],
            ["STOP_CODE"],
        )
    )

    result = pd.DataFrame(results)
    result.to_csv(AUDIT / "legacy_comparison.csv", index=False)
    all_equal = bool(result["values_equal_within_1e-6"].all())
    report = [
        "# Legacy StopArea equivalence check",
        "",
        f"Overall result: **{'PASS' if all_equal else 'FAIL'}**.",
        "",
        "The canonical child-StopArea data products were compared with the previous",
        "isolated StopArea test. Parent-hub-only columns were excluded from the stop",
        "crosswalk comparison because they are intentionally absent from the new pipeline.",
        "",
        result.to_markdown(index=False, floatfmt=".12g"),
        "",
    ]
    (REPORT / "LEGACY_EQUIVALENCE_CHECK.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(result.to_string(index=False))
    if not all_equal:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
