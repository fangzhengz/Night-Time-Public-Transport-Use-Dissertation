"""Add volume, direction and timing context to the fixed RQ1 cluster labels."""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]
RQ1 = FYP / "cluster_clean_version_fullweek"
PRE = FYP / "cluster_clean_version_grouped" / "outputs" / "preprocessed"

RAIL_RAW = FYP / "outputs" / "preprocessed_numbat" / "numbat_lu_station_qhr_all_daytypes.parquet"
BUS_LONG = PRE / "bus_lsoa_night_long.parquet"
RAIL_LABELS = RQ1 / "outputs" / "labels" / "rail_k5_labels.csv"
BUS_LABELS = RQ1 / "outputs" / "labels" / "bus_k3_labels.csv"
RAIL_META = RQ1 / "outputs" / "features" / "rail_meta.csv"
BUS_META = RQ1 / "outputs" / "features" / "bus_meta.csv"

OUT = ROOT / "outputs"
DATA = OUT / "data"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
WORKBOOK = OUT / "workbook"
for directory in (DATA, FIGURES, REPORT, WORKBOOK):
    directory.mkdir(parents=True, exist_ok=True)

RAIL_WINDOWS = {
    "MON": (1080, 1500),
    "TWT": (1080, 1500),
    "FRI": (1080, 1740),
    "SAT": (1080, 1740),
    "SUN": (1080, 1500),
}
RAIL_DAYS = list(RAIL_WINDOWS)
BUS_DAYS = ["Weekday", "Saturday", "Sunday"]
START = time.time()


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    aligned_numerator = numerator.reindex(denominator.index, fill_value=0)
    return aligned_numerator.div(denominator.replace(0, np.nan))


def sum_window(
    frame: pd.DataFrame,
    unit: str,
    bin_column: str,
    lower: int,
    upper: int,
    days: list[str] | None = None,
) -> pd.Series:
    mask = frame[bin_column].between(lower, upper - 1)
    if days is not None:
        mask &= frame["day_type"].isin(days)
    return frame.loc[mask].groupby(unit)["count"].sum()


def direction_balance(
    frame: pd.DataFrame,
    unit: str,
    positive: str,
    negative: str,
) -> pd.Series:
    totals = (
        frame.groupby([unit, "direction"])["count"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=[positive, negative], fill_value=0)
    )
    return safe_divide(totals[positive] - totals[negative], totals.sum(axis=1))


def volume_tertiles(series: pd.Series) -> pd.Categorical:
    ranks = series.rank(method="first")
    return pd.qcut(ranks, 3, labels=["low", "medium", "high"])


def robust_signature(frame: pd.DataFrame, cluster: str, metrics: list[str]) -> pd.DataFrame:
    medians = frame.groupby(cluster)[metrics].median()
    overall_median = frame[metrics].median()
    iqr = frame[metrics].quantile(0.75) - frame[metrics].quantile(0.25)
    return medians.sub(overall_median).div(iqr.replace(0, np.nan)).fillna(0)


def metric_summary(frame: pd.DataFrame, cluster: str, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for cluster_value, group in frame.groupby(cluster):
        for metric in metrics:
            values = group[metric].dropna()
            rows.append(
                {
                    "cluster": int(cluster_value),
                    "metric": metric,
                    "n": int(len(values)),
                    "median": float(values.median()),
                    "q25": float(values.quantile(0.25)),
                    "q75": float(values.quantile(0.75)),
                    "mean": float(values.mean()),
                }
            )
    return pd.DataFrame(rows)


def check_meta_total(
    calculated: pd.Series,
    meta: pd.DataFrame,
    key: str,
    tolerance: float = 1e-6,
) -> float:
    expected = meta.set_index(key)["total_activity"].astype(float)
    aligned = pd.concat([calculated.rename("calculated"), expected.rename("expected")], axis=1)
    relative = (
        (aligned["calculated"] - aligned["expected"]).abs()
        / aligned["expected"].replace(0, np.nan)
    ).fillna(0)
    maximum = float(relative.max())
    if maximum > tolerance:
        raise AssertionError(f"{key} total_activity mismatch: max relative error {maximum}")
    return maximum


def build_rail_metrics() -> tuple[pd.DataFrame, list[str], float]:
    raw = pd.read_parquet(RAIL_RAW).copy()
    raw["NLC"] = raw["NLC"].astype(int)
    raw["day_type"] = raw["day_type"].astype(str)
    raw = pd.concat(
        [
            raw.loc[
                (raw["day_type"] == day)
                & raw["extended_minute"].between(lower, upper - 1)
            ]
            for day, (lower, upper) in RAIL_WINDOWS.items()
        ],
        ignore_index=True,
    )

    labels = pd.read_csv(RAIL_LABELS).rename(columns={"unit": "NLC"})
    labels["NLC"] = labels["NLC"].astype(int)
    meta = pd.read_csv(RAIL_META)
    meta["NLC"] = meta["NLC"].astype(int)

    total = raw.groupby("NLC")["count"].sum()
    meta_error = check_meta_total(total, meta, "NLC")
    common_total = sum_window(raw, "NLC", "extended_minute", 1080, 1500)
    evening = sum_window(raw, "NLC", "extended_minute", 1080, 1260)
    midnight = sum_window(raw, "NLC", "extended_minute", 1440, 1500)
    extension = sum_window(
        raw, "NLC", "extended_minute", 1500, 1740, ["FRI", "SAT"]
    )
    fri_sat_total = sum_window(
        raw, "NLC", "extended_minute", 1080, 1740, ["FRI", "SAT"]
    )

    day_common = (
        raw.loc[raw["extended_minute"].between(1080, 1499)]
        .groupby(["NLC", "day_type"])["count"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=RAIL_DAYS, fill_value=0)
    )
    weekday_common = day_common[["MON", "TWT"]].mean(axis=1)
    weekend_common = day_common[["SAT", "SUN"]].mean(axis=1)

    metrics = pd.DataFrame(index=total.index)
    metrics["total_activity"] = total
    metrics["log_total_activity"] = np.log1p(total)
    metrics["direction_balance"] = direction_balance(raw, "NLC", "entry", "exit")
    metrics["midnight_share_common_window"] = safe_divide(midnight, common_total)
    metrics["night_tube_extension_share"] = safe_divide(extension, fri_sat_total)
    metrics["common_window_persistence"] = safe_divide(midnight, evening)
    metrics["weekend_common_ratio"] = safe_divide(weekend_common, weekday_common)
    metrics["volume_band"] = volume_tertiles(metrics["total_activity"])
    metrics.index.name = "NLC"
    metrics = metrics.reset_index().merge(labels, on="NLC", validate="one_to_one")
    metrics = metrics.merge(
        meta[["NLC", "tot_entry", "tot_exit"]],
        on="NLC",
        validate="one_to_one",
    )

    analysis_metrics = [
        "log_total_activity",
        "direction_balance",
        "midnight_share_common_window",
        "night_tube_extension_share",
        "weekend_common_ratio",
    ]
    return metrics, analysis_metrics, meta_error


def build_bus_metrics() -> tuple[pd.DataFrame, list[str], float]:
    raw = pd.read_parquet(BUS_LONG).copy()
    raw["lsoa"] = raw["lsoa"].astype(str)
    labels = pd.read_csv(BUS_LABELS).rename(columns={"unit": "lsoa"})
    labels["lsoa"] = labels["lsoa"].astype(str)
    meta = pd.read_csv(BUS_META)
    meta["lsoa"] = meta["lsoa"].astype(str)

    total = raw.groupby("lsoa")["count"].sum()
    meta_error = check_meta_total(total, meta, "lsoa")
    evening = sum_window(raw, "lsoa", "hour_bin", 1080, 1260)
    post_midnight = sum_window(raw, "lsoa", "hour_bin", 1440, 1800)
    deep_night = sum_window(raw, "lsoa", "hour_bin", 1620, 1800)
    day_total = (
        raw.groupby(["lsoa", "day_type"])["count"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=BUS_DAYS, fill_value=0)
    )
    weekend_mean = day_total[["Saturday", "Sunday"]].mean(axis=1)

    metrics = pd.DataFrame(index=total.index)
    metrics["total_activity"] = total
    metrics["log_total_activity"] = np.log1p(total)
    metrics["direction_balance"] = direction_balance(
        raw, "lsoa", "boardings", "alightings"
    )
    metrics["post_midnight_share"] = safe_divide(post_midnight, total)
    metrics["deep_night_share"] = safe_divide(deep_night, total)
    metrics["post_midnight_persistence"] = safe_divide(post_midnight, evening)
    metrics["weekend_ratio"] = safe_divide(weekend_mean, day_total["Weekday"])
    metrics["volume_band"] = volume_tertiles(metrics["total_activity"])
    metrics.index.name = "lsoa"
    metrics = metrics.reset_index().merge(labels, on="lsoa", validate="one_to_one")
    metrics = metrics.merge(
        meta[["lsoa", "tot_boardings", "tot_alightings"]],
        on="lsoa",
        validate="one_to_one",
    )

    analysis_metrics = [
        "log_total_activity",
        "direction_balance",
        "post_midnight_share",
        "deep_night_share",
        "weekend_ratio",
    ]
    return metrics, analysis_metrics, meta_error


def make_dashboard(
    frame: pd.DataFrame,
    mode: str,
    metrics: list[str],
    signature: pd.DataFrame,
) -> None:
    palette = sns.color_palette("tab10", n_colors=frame["cluster"].nunique())
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    sns.boxplot(
        data=frame,
        x="cluster",
        y="log_total_activity",
        hue="cluster",
        legend=False,
        palette=palette,
        ax=axes[0, 0],
        showfliers=False,
    )
    axes[0, 0].set_title(f"{mode.title()}: activity volume by fixed RQ1 cluster")
    axes[0, 0].set_ylabel("log(1 + representative-night activity)")

    timing_metric = (
        "night_tube_extension_share" if mode == "rail" else "post_midnight_share"
    )
    sns.boxplot(
        data=frame,
        x="cluster",
        y=timing_metric,
        hue="cluster",
        legend=False,
        palette=palette,
        ax=axes[0, 1],
        showfliers=False,
    )
    axes[0, 1].set_title(f"{mode.title()}: late-night timing metric")
    axes[0, 1].set_ylabel(timing_metric)

    volume = (
        pd.crosstab(frame["cluster"], frame["volume_band"], normalize="index")
        .reindex(columns=["low", "medium", "high"], fill_value=0)
        .mul(100)
    )
    volume.plot(
        kind="bar",
        stacked=True,
        color=["#B8C4D4", "#6A8CAF", "#234F79"],
        ax=axes[1, 0],
    )
    axes[1, 0].set_title("Mode-specific volume tertiles within cluster")
    axes[1, 0].set_ylabel("% of units")
    axes[1, 0].legend(title="Volume band", frameon=False)
    axes[1, 0].tick_params(axis="x", rotation=0)

    sns.heatmap(
        signature[metrics],
        cmap="vlag",
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"label": "Cluster median deviation / overall IQR"},
        ax=axes[1, 1],
    )
    axes[1, 1].set_title("Robust cluster signature")
    axes[1, 1].set_xlabel("")
    axes[1, 1].set_ylabel("Cluster")
    axes[1, 1].tick_params(axis="x", rotation=35)
    plt.tight_layout()
    plt.savefig(FIGURES / f"{mode}_context_dashboard.png", dpi=220, bbox_inches="tight")
    plt.close()


def describe_cluster(
    mode: str,
    cluster: int,
    group: pd.DataFrame,
    timing_metric: str,
    weekend_metric: str,
) -> str:
    dominant_band = group["volume_band"].value_counts().idxmax()
    balance = group["direction_balance"].median()
    direction_text = (
        "entry/boarding leaning"
        if balance > 0.05
        else "exit/alighting leaning"
        if balance < -0.05
        else "directionally balanced"
    )
    return (
        f"- Cluster {cluster} (n={len(group)}): median total activity "
        f"{group['total_activity'].median():,.1f}; predominant volume band "
        f"`{dominant_band}`; {direction_text} (median balance {balance:.3f}); "
        f"median {timing_metric}={group[timing_metric].median():.3f}; "
        f"median {weekend_metric}={group[weekend_metric].median():.3f}."
    )


def main() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    required = [RAIL_RAW, BUS_LONG, RAIL_LABELS, BUS_LABELS, RAIL_META, BUS_META]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing inputs: {missing}")

    rail, rail_metrics, rail_error = build_rail_metrics()
    bus, bus_metrics, bus_error = build_bus_metrics()

    audit_rows = []
    for mode, frame, metrics, error in (
        ("rail", rail, rail_metrics, rail_error),
        ("bus", bus, bus_metrics, bus_error),
    ):
        frame.to_csv(DATA / f"{mode}_unit_metrics.csv", index=False)
        summary = metric_summary(frame, "cluster", metrics)
        summary.to_csv(DATA / f"{mode}_cluster_metric_summary.csv", index=False)
        signature = robust_signature(frame, "cluster", metrics)
        signature.to_csv(DATA / f"{mode}_cluster_signature_z.csv")
        volume = (
            pd.crosstab(frame["cluster"], frame["volume_band"], normalize="index")
            .reindex(columns=["low", "medium", "high"], fill_value=0)
            .mul(100)
        )
        volume.to_csv(DATA / f"{mode}_cluster_volume_band_pct.csv")
        make_dashboard(frame, mode, metrics, signature)
        audit_rows.extend(
            [
                {"mode": mode, "metric": "rows", "value": len(frame)},
                {
                    "mode": mode,
                    "metric": "clusters",
                    "value": frame["cluster"].nunique(),
                },
                {
                    "mode": mode,
                    "metric": "max_meta_total_relative_error",
                    "value": error,
                },
                {
                    "mode": mode,
                    "metric": "missing_primary_metrics",
                    "value": int(frame[metrics].isna().sum().sum()),
                },
            ]
        )
    pd.DataFrame(audit_rows).to_csv(DATA / "data_audit.csv", index=False)

    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# RQ1 volume and context interpretation — provisional results",
        "",
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite / experiment-agent",
        "- Origin Mode: run",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "- Version Label: rq1_context_metrics_v1",
        "",
        "## Method boundary",
        "",
        "The fixed RQ1 GMM labels are retained. Volume is added after clustering, not used to refit the clusters.",
        "Rail metrics separate the 18:00–01:00 common window from the Friday/Saturday 01:00–05:00 Night Tube extension.",
        "Bus metrics remain LSOA-level area-use measures.",
        "",
        "## Rail cluster context",
        "",
    ]
    for cluster, group in rail.groupby("cluster"):
        lines.append(
            describe_cluster(
                "rail",
                int(cluster),
                group,
                "night_tube_extension_share",
                "weekend_common_ratio",
            )
        )
    lines.extend(["", "## Bus cluster context", ""])
    for cluster, group in bus.groupby("cluster"):
        lines.append(
            describe_cluster(
                "bus",
                int(cluster),
                group,
                "post_midnight_share",
                "weekend_ratio",
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- Volume bands are mode-specific tertiles and are not cross-mode equivalents.",
            "- A high volume or late-night share is observed use, not evidence of unmet demand.",
            "- Direction balance does not identify trip purpose or passenger occupation.",
            "- Rail late-night extension partly reflects service availability; it is not a pure behavioural measure.",
        ]
    )
    (REPORT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    metadata = {
        "generated_utc": generated,
        "duration_seconds": time.time() - START,
        "command": "py -3 src/run_rq1_context_analysis.py",
        "python": sys.version,
        "platform": platform.platform(),
        "parameters": {"rail_k": 5, "bus_k": 3},
    }
    (REPORT / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(
        f"Completed RQ1 context analysis in {metadata['duration_seconds']:.1f}s; "
        f"rail={len(rail)}, bus={len(bus)}."
    )


if __name__ == "__main__":
    main()
