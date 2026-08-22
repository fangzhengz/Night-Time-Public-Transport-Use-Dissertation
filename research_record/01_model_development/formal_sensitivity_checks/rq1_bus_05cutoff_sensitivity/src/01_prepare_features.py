# -*- coding: utf-8 -*-
"""Build common min-direction-36 raw-share and CLR feature matrices.

05:00-cutoff sensitivity sidecar: identical to
`rq1_bus_stoparea_clustering/src/01_prepare_features.py` except the expected
feature-matrix shape is derived from `len(C.HOURS)` (66 = 11 hours x 2
directions x 3 day types) instead of the canonical hardcoded 72 (12 hours).
"""
from __future__ import annotations

import hashlib
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

EXPECTED_FEATURE_COLUMNS = len(C.HOURS) * len(C.DIRECTIONS) * len(C.DAY_TYPES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_input(long: pd.DataFrame) -> None:
    required = {"day_type", "direction", "lsoa", "hour_bin", "count"}
    missing = required - set(long.columns)
    if missing:
        raise RuntimeError(f"StopArea long table is missing columns: {sorted(missing)}")
    if long["count"].isna().any() or (long["count"] < 0).any():
        raise RuntimeError("StopArea long table contains missing or negative counts.")
    checks = {
        "day_type": (set(long["day_type"].astype(str)), set(C.DAY_TYPES)),
        "direction": (set(long["direction"].astype(str)), set(C.DIRECTIONS)),
        "hour_bin": (set(long["hour_bin"].astype(int)), set(C.HOURS)),
    }
    for label, (actual, expected) in checks.items():
        if actual != expected:
            raise RuntimeError(
                f"Unexpected {label} values: actual={sorted(actual)}, expected={sorted(expected)}"
            )


def build_raw_counts(grouped: pd.DataFrame, keep: pd.Index) -> pd.DataFrame:
    blocks: list[pd.DataFrame] = []
    for direction in C.DIRECTIONS:
        day_parts: list[pd.DataFrame] = []
        for day_type in C.DAY_TYPES:
            sub = grouped[
                (grouped["direction"] == direction)
                & (grouped["day_type"] == day_type)
            ]
            wide = sub.pivot_table(
                index="lsoa",
                columns="hour_bin",
                values="count",
                aggfunc="sum",
                fill_value=0.0,
            )
            wide = wide.reindex(index=keep, columns=C.HOURS, fill_value=0.0).astype(float)
            wide.columns = [f"{direction}_{day_type}_{hour}" for hour in C.HOURS]
            day_parts.append(wide)
        blocks.append(pd.concat(day_parts, axis=1))
    raw = pd.concat(blocks, axis=1)
    raw.index = pd.Index(raw.index.astype(str), name="lsoa")
    if raw.shape != (len(keep), EXPECTED_FEATURE_COLUMNS):
        raise RuntimeError(f"Unexpected raw-count feature shape: {raw.shape}")
    return raw


def build_raw_share(raw_counts: pd.DataFrame) -> pd.DataFrame:
    blocks: list[pd.DataFrame] = []
    for direction in C.DIRECTIONS:
        columns = [column for column in raw_counts if column.startswith(f"{direction}_")]
        counts = raw_counts[columns]
        totals = counts.sum(axis=1)
        if (totals <= 0).any():
            raise RuntimeError(f"Non-positive {direction} total after min-direction filtering.")
        block = counts.div(totals, axis=0)
        if not np.allclose(block.sum(axis=1), 1.0, atol=1e-10):
            raise RuntimeError(f"{direction} raw-share rows do not sum to one.")
        blocks.append(block)
    X = pd.concat(blocks, axis=1)
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise RuntimeError("Raw-share features contain non-finite values.")
    return X


def build_clr(raw_counts: pd.DataFrame) -> pd.DataFrame:
    blocks: list[pd.DataFrame] = []
    for direction in C.DIRECTIONS:
        columns = [column for column in raw_counts if column.startswith(f"{direction}_")]
        counts = raw_counts[columns].to_numpy(dtype=float)
        totals = counts.sum(axis=1)
        prior = counts.sum(axis=0) / counts.sum()
        posterior = (
            counts + C.CLR_PSEUDOCOUNT_ALPHA * prior
        ) / (totals[:, None] + C.CLR_PSEUDOCOUNT_ALPHA)
        if not np.all(posterior > 0):
            raise RuntimeError(f"Non-positive posterior share in {direction} block.")
        log_share = np.log(posterior)
        clr = log_share - log_share.mean(axis=1, keepdims=True)
        if not np.allclose(clr.sum(axis=1), 0.0, atol=1e-8):
            raise RuntimeError(f"{direction} CLR rows do not sum to zero.")
        blocks.append(pd.DataFrame(clr, index=raw_counts.index, columns=columns))
    X = pd.concat(blocks, axis=1)
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise RuntimeError("CLR features contain non-finite values.")
    return X


def build_metrics(long: pd.DataFrame, grouped: pd.DataFrame) -> pd.DataFrame:
    total = long.groupby("lsoa", observed=True)["count"].sum().rename("total_activity")
    direction = (
        grouped.groupby(["lsoa", "direction"], observed=True)["count"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=C.DIRECTIONS, fill_value=0.0)
    )
    # Range checks (not exact-set checks) -- they naturally adapt to whatever
    # hour_bin values are actually present, so no change needed for the
    # truncated 05:00 window: max hour_bin present is now 1680 (04:00-05:00)
    # instead of 1740 (05:00-06:00), and these .between() filters just see
    # fewer rows above 1440/1620.
    post_midnight = (
        long.loc[long["hour_bin"].between(1440, 1799)]
        .groupby("lsoa", observed=True)["count"]
        .sum()
        .reindex(total.index, fill_value=0.0)
    )
    deep_night = (
        long.loc[long["hour_bin"].between(1620, 1799)]
        .groupby("lsoa", observed=True)["count"]
        .sum()
        .reindex(total.index, fill_value=0.0)
    )
    evening = (
        long.loc[long["hour_bin"].between(1080, 1259)]
        .groupby("lsoa", observed=True)["count"]
        .sum()
        .reindex(total.index, fill_value=0.0)
    )
    day_total = (
        long.groupby(["lsoa", "day_type"], observed=True)["count"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(index=total.index, columns=C.DAY_TYPES, fill_value=0.0)
    )

    metrics = pd.DataFrame(index=pd.Index(total.index.astype(str), name="lsoa"))
    metrics["tot_boardings"] = direction["boardings"].reindex(metrics.index, fill_value=0.0)
    metrics["tot_alightings"] = direction["alightings"].reindex(metrics.index, fill_value=0.0)
    metrics["min_direction_activity"] = metrics[
        ["tot_boardings", "tot_alightings"]
    ].min(axis=1)
    metrics["total_activity"] = total.reindex(metrics.index, fill_value=0.0)
    metrics["log_total_activity"] = np.log1p(metrics["total_activity"])
    metrics["direction_balance"] = (
        metrics["tot_boardings"] - metrics["tot_alightings"]
    ) / metrics["total_activity"].replace(0.0, np.nan)
    metrics["post_midnight_share"] = post_midnight.reindex(metrics.index) / metrics[
        "total_activity"
    ].replace(0.0, np.nan)
    metrics["deep_night_share"] = deep_night.reindex(metrics.index) / metrics[
        "total_activity"
    ].replace(0.0, np.nan)
    metrics["post_midnight_persistence"] = post_midnight.reindex(
        metrics.index
    ) / evening.reindex(metrics.index).replace(0.0, np.nan)
    metrics["weekend_ratio"] = day_total[["Saturday", "Sunday"]].mean(
        axis=1
    ).reindex(metrics.index) / day_total["Weekday"].reindex(metrics.index).replace(
        0.0, np.nan
    )
    metrics["passes_both_directions_36"] = (
        metrics["min_direction_activity"] >= C.MIN_DIRECTION
    )
    metrics["retained_for_fit"] = metrics["passes_both_directions_36"]
    metrics["exclusion_reason"] = np.where(
        metrics["passes_both_directions_36"],
        "retained",
        "at_least_one_direction_below_36",
    )
    return metrics


def main() -> None:
    if not C.LONG_INPUT.exists():
        raise FileNotFoundError(C.LONG_INPUT)
    long = pd.read_parquet(C.LONG_INPUT).copy()
    long["lsoa"] = long["lsoa"].astype(str)
    long["day_type"] = long["day_type"].astype(str)
    long["direction"] = long["direction"].astype(str)
    long["hour_bin"] = long["hour_bin"].astype(int)
    validate_input(long)
    grouped = long.groupby(
        ["lsoa", "day_type", "direction", "hour_bin"],
        as_index=False,
        observed=True,
    )["count"].sum()

    metrics = build_metrics(long, grouped).sort_index()
    keep = pd.Index(metrics.index[metrics["retained_for_fit"]], name="lsoa")
    raw_counts = build_raw_counts(grouped, keep)
    X_raw = build_raw_share(raw_counts)
    X_clr = build_clr(raw_counts)

    for direction in C.DIRECTIONS:
        columns = [column for column in raw_counts if column.startswith(f"{direction}_")]
        reconstructed = raw_counts[columns].sum(axis=1)
        expected = metrics.loc[keep, f"tot_{direction}"]
        max_diff = float((reconstructed - expected).abs().max())
        if max_diff > 1e-6:
            raise RuntimeError(
                f"{direction} raw-count reconstruction failed conservation: {max_diff}"
            )

    raw_counts.to_parquet(C.FEATURES / "raw_counts_min36.parquet")
    X_raw.to_parquet(C.FEATURES / "X_bus_stoparea_raw_share_min36.parquet")
    X_clr.to_parquet(C.FEATURES / "X_bus_stoparea_clr_min36.parquet")
    metrics.reset_index().to_csv(C.FEATURES / "sample_metrics.csv", index=False)
    metrics.loc[metrics["retained_for_fit"]].reset_index().to_csv(
        C.FEATURES / "retained_lsoas.csv", index=False
    )
    metrics.loc[~metrics["retained_for_fit"]].reset_index().to_csv(
        C.FEATURES / "excluded_lsoas.csv", index=False
    )

    audit = pd.DataFrame(
        [
            ("input_lsoas", metrics.index.nunique()),
            ("retained_lsoas", len(keep)),
            ("excluded_lsoas", int((~metrics["retained_for_fit"]).sum())),
            ("feature_columns_per_variant", X_raw.shape[1]),
            ("raw_share_max_boarding_sum_error", float((X_raw.filter(like="boardings_").sum(axis=1) - 1).abs().max())),
            ("raw_share_max_alighting_sum_error", float((X_raw.filter(like="alightings_").sum(axis=1) - 1).abs().max())),
            ("clr_max_boarding_zero_sum_error", float(X_clr.filter(like="boardings_").sum(axis=1).abs().max())),
            ("clr_max_alighting_zero_sum_error", float(X_clr.filter(like="alightings_").sum(axis=1).abs().max())),
        ],
        columns=["metric", "value"],
    )
    audit.to_csv(C.FEATURES / "feature_preparation_audit.csv", index=False)

    manifest_rows = [
        {
            "role": "sensitivity_stoparea_lsoa_long_05cutoff",
            "path": str(C.LONG_INPUT.resolve()),
            "bytes": C.LONG_INPUT.stat().st_size,
            "sha256": sha256(C.LONG_INPUT),
        }
    ]
    if C.STOPAREA_SUMMARY.exists():
        manifest_rows.append(
            {
                "role": "stoparea_preprocessing_summary_05cutoff",
                "path": str(C.STOPAREA_SUMMARY.resolve()),
                "bytes": C.STOPAREA_SUMMARY.stat().st_size,
                "sha256": sha256(C.STOPAREA_SUMMARY),
            }
        )
    pd.DataFrame(manifest_rows).to_csv(C.FEATURES / "input_manifest.csv", index=False)

    report = [
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite/experiment-agent",
        "- Origin Mode: run + validate",
        "- Verification Status: ANALYZED",
        "- Version Label: stoparea_min36_raw_clr_05cutoff_sensitivity_v1",
        "",
        "# StopArea bus feature preparation -- 05:00-cutoff sensitivity sidecar",
        "",
        "## Fixed and changed factors",
        "",
        f"- Fixed: LSOA unit, three day types, min-direction threshold {C.MIN_DIRECTION:g} "
        f"(corrected from canonical's 36 to match the truncated window: "
        f"{len(C.HOURS)} hours x 3 day types = {len(C.HOURS)*3} intervals, "
        f">=1/interval average), "
        f"{len(C.HOURS) * len(C.DIRECTIONS)} bins per direction-pair.",
        "- Changed: night window truncated to 18:00-05:00 (11 hourly bins) instead "
        "of the canonical 18:00-06:00 (12 hourly bins); everything else "
        "(StopArea allocation, retention rule, CLR construction, GMM "
        "hyperparameters) is identical to the canonical pipeline.",
        "- Parallel variants: direction-wise raw shares and direction-wise CLR after alpha=1 empirical-prior zero handling.",
        "",
        "## Audit",
        "",
        audit.to_markdown(index=False, floatfmt=".12g"),
        "",
        "The raw-share and CLR matrices use exactly the same retained LSOAs and raw counts.",
        "Input hashes are stored in `outputs/features/input_manifest.csv`.",
        "",
        f"Runtime: Python {platform.python_version()}, pandas {pd.__version__}, NumPy {np.__version__}.",
    ]
    (C.REPORT / "FEATURE_PREPARATION.md").write_text("\n".join(report), encoding="utf-8")
    print(audit.to_string(index=False))


if __name__ == "__main__":
    main()
