"""Continuous descriptors and internal cluster-coherence tests for the
adopted Rail K=5 and Bus StopArea CLR K=4 solutions.

Fixed cluster labels are joined, never refit. Rail metrics are recomputed
from the all-modes raw long table (same window definitions as canonical).
Bus metrics are not recomputed -- ``sample_metrics_min72.csv`` already
carries them (built by ``analysis/02_mode_specific_clustering/bus/src/01_prepare_features.py``);
this script only joins them to the K=4 labels and restricts to the retained
sample.
"""

from __future__ import annotations

import json
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
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

START = time.time()

# 2026-08-01: widened to a common 18:00-05:00 window for every day type, to
# match analysis/02_mode_specific_clustering/rail/src/02_build_features_allmodes.py after the same
# change there. These MUST agree: `check_meta_total` below compares the sum
# over these windows against `rail_allmodes_feature_meta.csv`, so a mismatch
# fails the run rather than producing silently mis-scoped metrics.
RAIL_WINDOWS = {day: (1080, 1740) for day in ["MON", "TWT", "FRI", "SAT", "SUN"]}
RAIL_DAYS = list(RAIL_WINDOWS)

# 2026-08-06, user decision. Use one post-23:00 share for both modes so the
# behavioural panels carry the same timing threshold. Both source windows are
# now 18:00-05:00, but mode-native activity definitions still make this a
# descriptive alignment rather than a pooled comparison.
#
# The former four night metrics were an artefact of unequal day-type windows:
# `midnight_share_common_window` and `common_window_persistence` were scoped to
# the 18:00-01:00 "common window" precisely because MON/TWT/SUN stopped there,
# and `night_tube_extension_share` was restricted to FRI/SAT because only those
# days had 01:00-05:00 bins at all. With one 18:00-05:00 window for every day
# type those constructions no longer have a reason to exist.
#
# The retired Rail metrics, including post_0100_share, remain computed and are
# still written to `rail_unit_metrics.csv`; Bus's former post_midnight_share
# remains in its upstream sample table. Only the formal analysis lists change,
# so the replacement is reversible without refitting either clustering.
#
# One thing to know if it is ever revisited: the four were two pairs, not one
# family. post_0100_share correlates 0.992 with night_tube_extension_share and
# 0.990 links midnight_share to persistence, but ACROSS the pairs the Spearman
# correlation is only ~0.60. Dropping the midnight pair therefore gives up a
# partly separate dimension ("how strong is the midnight hour relative to the
# evening") rather than a redundant one.
RAIL_METRICS = [
    "log_total_activity",
    "direction_balance",
    "post_2300_share",
    "weekend_common_ratio",
]
# Formal Bus behavioural descriptor set used by the dissertation analysis.
BUS_METRICS = [
    "log_total_activity",
    "direction_balance",
    "post_2300_share",
    "post_midnight_persistence",
    "weekend_ratio",
]


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    aligned = numerator.reindex(denominator.index, fill_value=0)
    return aligned.div(denominator.replace(0, np.nan))


def sum_window(frame, unit, bin_column, lower, upper, days=None):
    mask = frame[bin_column].between(lower, upper - 1)
    if days is not None:
        mask &= frame["day_type"].isin(days)
    return frame.loc[mask].groupby(unit)["count"].sum()


def direction_balance(frame, unit, positive, negative):
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


def robust_signature(frame, cluster, metrics):
    medians = frame.groupby(cluster)[metrics].median()
    overall_median = frame[metrics].median()
    iqr = frame[metrics].quantile(0.75) - frame[metrics].quantile(0.25)
    return medians.sub(overall_median).div(iqr.replace(0, np.nan)).fillna(0)


def metric_summary(frame, cluster, metrics):
    rows = []
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


def check_meta_total(calculated, meta, key, tolerance=1e-6):
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


def kruskal_epsilon_squared(values: pd.Series, groups: pd.Series):
    frame = pd.DataFrame({"value": values, "group": groups}).dropna()
    samples = [g["value"].values for _, g in frame.groupby("group")]
    h_stat, p_value = stats.kruskal(*samples)
    n = len(frame)
    k = len(samples)
    epsilon_sq = (h_stat - k + 1) / (n - k) if n > k else float("nan")
    return float(h_stat), float(p_value), float(epsilon_sq), n, k


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    ranked = p_values.rank(method="first")
    n = len(p_values)
    adjusted = p_values * n / ranked
    order = p_values.sort_values().index
    running_min = adjusted.loc[order][::-1].cummin()[::-1]
    return running_min.reindex(p_values.index).clip(upper=1.0)


def build_rail_metrics() -> tuple[pd.DataFrame, float]:
    raw_full = pd.read_parquet(C.RAIL_RAW_LONG).copy()
    raw_full["NLC"] = raw_full["NLC"].astype(int)
    raw_full["day_type"] = raw_full["day_type"].astype(str)

    labels = pd.read_csv(C.RAIL_LABELS).rename(columns={"unit": "NLC"})
    labels["NLC"] = labels["NLC"].astype(int)
    meta = pd.read_csv(C.RAIL_META)
    meta["NLC"] = meta["NLC"].astype(int)

    raw = pd.concat(
        [
            raw_full.loc[(raw_full["day_type"] == day) & raw_full["extended_minute"].between(lower, upper - 1)]
            for day, (lower, upper) in RAIL_WINDOWS.items()
        ],
        ignore_index=True,
    )

    # meta is rail_allmodes_feature_meta.csv (built by
    # analysis/02_mode_specific_clustering/rail/src/02_build_features_allmodes.py using the
    # exact same RAIL_WINDOWS-equivalent day windows), so it is already
    # night-window scoped -- compare the windowed sum directly, not a
    # full-extract one (an earlier, differently-scoped meta source needed
    # the opposite comparison; see project memory for that history).
    total = raw.groupby("NLC")["count"].sum()
    meta_error = check_meta_total(total, meta, "NLC")
    common_total = sum_window(raw, "NLC", "extended_minute", 1080, 1500)
    evening = sum_window(raw, "NLC", "extended_minute", 1080, 1260)
    post_2300 = sum_window(raw, "NLC", "extended_minute", 1380, 1740)
    midnight = sum_window(raw, "NLC", "extended_minute", 1440, 1500)
    # night_tube_extension_share keeps its FRI/SAT-only definition on purpose.
    # It measures the Night Tube phenomenon specifically -- how far a station's
    # Friday/Saturday activity runs past the normal 01:00 close. Widening it to
    # all day types would dilute that with the 0.18-0.24% of MON/TWT/SUN
    # activity that other operators run after 01:00, and would break
    # comparability with every number computed before 2026-08-01.
    extension = sum_window(raw, "NLC", "extended_minute", 1500, 1740, ["FRI", "SAT"])
    fri_sat_total = sum_window(raw, "NLC", "extended_minute", 1080, 1740, ["FRI", "SAT"])
    # post_0100_share is the all-day-type counterpart, newly available because
    # every day type now carries 01:00-05:00 bins. Reported alongside rather
    # than instead of the above, so the two questions stay separable:
    # "does this station have Night Tube" vs "how much of its week is after 1am".
    post_0100 = sum_window(raw, "NLC", "extended_minute", 1500, 1740)

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
    metrics["post_2300_share"] = safe_divide(post_2300, total)
    metrics["midnight_share_common_window"] = safe_divide(midnight, common_total)
    metrics["night_tube_extension_share"] = safe_divide(extension, fri_sat_total)
    metrics["post_0100_share"] = safe_divide(post_0100, total)
    metrics["common_window_persistence"] = safe_divide(midnight, evening)
    metrics["weekend_common_ratio"] = safe_divide(weekend_common, weekday_common)
    metrics["volume_band"] = volume_tertiles(metrics["total_activity"])
    metrics.index.name = "NLC"
    metrics = metrics.reset_index().merge(labels[["NLC", "cluster"]], on="NLC", validate="one_to_one")
    metrics = metrics.merge(
        meta[["NLC", "Station", "mode_label", "tot_entry", "tot_exit"]],
        on="NLC",
        validate="one_to_one",
    )
    return metrics, meta_error


def build_bus_metrics() -> pd.DataFrame:
    sample = pd.read_csv(C.BUS_SAMPLE_METRICS)
    sample["lsoa"] = sample["lsoa"].astype(str)
    raw = pd.read_parquet(C.BUS_RAW_LONG, columns=["lsoa", "hour_bin", "count"])
    raw["lsoa"] = raw["lsoa"].astype(str)
    actual_bins = sorted(raw["hour_bin"].astype(int).unique().tolist())
    if actual_bins != C.BUS_HOUR_BINS:
        raise ValueError(
            f"Bus hour bins do not match the locked 18:00-05:00 window: "
            f"expected {C.BUS_HOUR_BINS}, got {actual_bins}"
        )
    post_2300 = (
        raw.loc[raw["hour_bin"] >= 1380]
        .groupby("lsoa")["count"]
        .sum()
    )
    sample["post_2300_share"] = (
        sample["lsoa"].map(post_2300).fillna(0)
        / sample["total_activity"].replace(0, np.nan)
    )
    labels = pd.read_csv(C.BUS_LABELS)
    labels["lsoa"] = labels["lsoa"].astype(str)

    metrics = sample.merge(
        labels[["lsoa", "cluster"]],
        on="lsoa",
        how="inner",
        validate="one_to_one",
    )
    metrics = metrics.loc[metrics["cluster"] != -1].copy()
    if len(metrics) != C.EXPECTED_BUS_UNITS:
        raise ValueError(
            f"Expected {C.EXPECTED_BUS_UNITS} fitted Bus units, got {len(metrics)}"
        )
    metrics["volume_band"] = volume_tertiles(metrics["total_activity"])
    return metrics


def make_dashboard(frame, mode, metrics, signature, timing_metric):
    n_clusters = frame["cluster"].nunique()
    # Bus uses the RQ1 bus palette so this dashboard matches the bus maps; rail
    # keeps a generic palette, since the two modes' cluster ids are unrelated.
    palette = (
        C.BUS_CLUSTER_COLOURS[:n_clusters]
        if mode == "bus"
        else sns.color_palette("tab10", n_colors=n_clusters)
    )
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    sns.boxplot(
        data=frame, x="cluster", y="log_total_activity", hue="cluster", legend=False,
        palette=palette, ax=axes[0, 0], showfliers=False,
    )
    axes[0, 0].set_title(f"{mode.title()}: activity volume by cluster")
    axes[0, 0].set_ylabel("log(1 + activity)")

    sns.boxplot(
        data=frame, x="cluster", y=timing_metric, hue="cluster", legend=False,
        palette=palette, ax=axes[0, 1], showfliers=False,
    )
    axes[0, 1].set_title(f"{mode.title()}: late-night timing metric")
    axes[0, 1].set_ylabel(timing_metric)

    volume = (
        pd.crosstab(frame["cluster"], frame["volume_band"], normalize="index")
        .reindex(columns=["low", "medium", "high"], fill_value=0)
        .mul(100)
    )
    volume.plot(kind="bar", stacked=True, color=["#B8C4D4", "#6A8CAF", "#234F79"], ax=axes[1, 0])
    axes[1, 0].set_title("Mode-specific volume tertiles within cluster")
    axes[1, 0].set_ylabel("% of units")
    axes[1, 0].legend(title="Volume band", frameon=False)
    axes[1, 0].tick_params(axis="x", rotation=0)

    sns.heatmap(
        signature[metrics], cmap="vlag", center=0, annot=True, fmt=".2f", linewidths=0.5,
        cbar_kws={"label": "Cluster median deviation / overall IQR"}, ax=axes[1, 1],
    )
    axes[1, 1].set_title("Robust cluster signature")
    axes[1, 1].set_xlabel("")
    axes[1, 1].set_ylabel("Cluster")
    axes[1, 1].tick_params(axis="x", rotation=35)
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / f"{mode}_context_dashboard.png", dpi=220, bbox_inches="tight")
    plt.close()


def significance_test(frame: pd.DataFrame, mode: str, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for metric in metrics:
        h_stat, p_value, epsilon2, n, k = kruskal_epsilon_squared(frame[metric], frame["cluster"])
        rows.append(
            {
                "mode": mode, "metric": metric, "n": n, "n_clusters": k,
                "kruskal_H": h_stat, "kruskal_p": p_value, "epsilon_squared": epsilon2,
            }
        )
    result = pd.DataFrame(rows)
    result["p_bh"] = benjamini_hochberg(result["kruskal_p"])
    return result


def main() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    required = [
        C.RAIL_RAW_LONG,
        C.RAIL_LABELS,
        C.RAIL_META,
        C.BUS_SAMPLE_METRICS,
        C.BUS_RAW_LONG,
        C.BUS_LABELS,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing inputs: {missing}")

    rail, rail_meta_error = build_rail_metrics()
    bus = build_bus_metrics()
    if len(rail) != C.EXPECTED_RAIL_UNITS:
        raise ValueError(
            f"Expected {C.EXPECTED_RAIL_UNITS} fitted Rail units, got {len(rail)}"
        )

    audit_rows = []
    significance_frames = []
    for mode, frame, metrics, timing_metric, meta_error in (
        ("rail", rail, RAIL_METRICS, "post_2300_share", rail_meta_error),
        ("bus", bus, BUS_METRICS, "post_2300_share", np.nan),
    ):
        frame.to_csv(C.DATA_OUT / f"{mode}_unit_metrics.csv", index=False)
        summary = metric_summary(frame, "cluster", metrics)
        summary.to_csv(C.DATA_OUT / f"{mode}_cluster_metric_summary.csv", index=False)
        signature = robust_signature(frame, "cluster", metrics)
        signature.to_csv(C.DATA_OUT / f"{mode}_cluster_signature_z.csv")
        volume = (
            pd.crosstab(frame["cluster"], frame["volume_band"], normalize="index")
            .reindex(columns=["low", "medium", "high"], fill_value=0)
            .mul(100)
        )
        volume.to_csv(C.DATA_OUT / f"{mode}_cluster_volume_band_pct.csv")
        make_dashboard(frame, mode, metrics, signature, timing_metric)

        sig = significance_test(frame, mode, metrics)
        significance_frames.append(sig)
        sig.to_csv(C.DATA_OUT / f"{mode}_cluster_metric_significance.csv", index=False)

        audit_rows.extend(
            [
                {"mode": mode, "metric": "rows", "value": len(frame)},
                {"mode": mode, "metric": "clusters", "value": frame["cluster"].nunique()},
                {"mode": mode, "metric": "max_meta_total_relative_error", "value": meta_error},
                {"mode": mode, "metric": "missing_primary_metrics", "value": int(frame[metrics].isna().sum().sum())},
            ]
        )

    pd.DataFrame(audit_rows).to_csv(C.DATA_OUT / "data_audit.csv", index=False)
    significance = pd.concat(significance_frames, ignore_index=True)
    significance.to_csv(C.DATA_OUT / "cluster_metric_significance.csv", index=False)

    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Adopted clusters -- continuous variable layer + internal coherence",
        "",
        "## Material Passport",
        "",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "- Version Label: final_context_v1",
        "",
        "## Scope",
        "",
        f"- Rail: all-modes merged clustering, K={C.RAIL_K} ({len(rail)} stations).",
        f"- Bus: StopArea CLR clustering, K={C.BUS_K} ({len(bus)} LSOAs).",
        "- The fixed GMM labels are retained as-is; volume/timing context is added after clustering, not used to refit it.",
        "",
        "## Does the cluster label explain its own continuous profile? (Kruskal-Wallis + epsilon-squared, BH-corrected within mode)",
        "",
        significance.to_markdown(index=False),
        "",
        "## Interpretation limits",
        "",
        "- `post_2300_share` uses 23:00-05:00 over 18:00-05:00 for both modes. The time threshold and window are aligned, but the mode-native activity definitions still preclude a pooled comparison.",
        "- Volume bands are mode-specific tertiles and are not cross-mode equivalents.",
        "- A high volume or late-night share is observed use, not evidence of unmet demand.",
        "- Rail late-night extension partly reflects service availability, not a pure behavioural measure.",
        "- Bus `post_2300_share` is recomputed here from the audited StopArea long table; its other continuous metrics are taken as-is from `analysis/02_mode_specific_clustering/bus`'s feature-preparation audit.",
    ]
    (C.REPORT_OUT / "CONTEXT_METRICS.md").write_text("\n".join(lines), encoding="utf-8")

    metadata = {
        "generated_utc": generated,
        "duration_seconds": time.time() - START,
        "command": "py -3 src/run_context_metrics.py",
        "python": sys.version,
        "platform": platform.platform(),
        "parameters": {"rail_k": C.RAIL_K, "bus_k": C.BUS_K},
    }
    (C.REPORT_OUT / "run_metadata_context.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Completed context metrics in {metadata['duration_seconds']:.1f}s; rail={len(rail)}, bus={len(bus)}.")


if __name__ == "__main__":
    main()
