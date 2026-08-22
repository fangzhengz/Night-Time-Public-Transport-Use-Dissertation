# -*- coding: utf-8 -*-
"""Sidecar sensitivity check: does Rail's weekend_common_ratio change if the
"common window" truncation (18:00-01:00) and the Friday exclusion are
relaxed to match Bus's convention (full 18:00-05:00 window, Friday folded
into the weekday reference)?

Motivation: table-verification review (2026-08-20) found that Rail's
weekend_common_ratio and Bus's weekend_ratio, despite sitting in the same
"Week structure" row of the continuous-metrics table, are not computed the
same way. Rail restricts both the window (to 18:00-01:00, a leftover from
when MON/TWT/SUN genuinely had no data past 01:00, pre-padding) and the day
grouping (drops FRI entirely) in a way Bus does not. This script recomputes
Rail's metric under two alternative specifications and checks how much the
internal cluster-coherence result (Kruskal-Wallis epsilon-squared against
the existing rail_allmodes K=5 labels) and the per-NLC ranking change.

This is a read-only sidecar: it does not refit any clustering and does not
touch rq2_new_clusters_analysis's canonical outputs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

RAIL_RAW_LONG = (
    FYP / "data_processing" / "rail_allmodes" / "outputs" / "preprocessed"
    / "numbat_allmodes_station_qhr_all_daytypes_final.parquet"
)
RAIL_LABELS = FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
RAIL_META = FYP / "numbat_all_area_test" / "outputs" / "data" / "rail_allmodes_feature_meta.csv"

OUT = ROOT / "outputs"
DATA_OUT = OUT / "data"
FIGURE_OUT = OUT / "figures"
REPORT_OUT = OUT / "report"
for d in (DATA_OUT, FIGURE_OUT, REPORT_OUT):
    d.mkdir(parents=True, exist_ok=True)

RAIL_DAYS = ["MON", "TWT", "FRI", "SAT", "SUN"]
COMMON_WINDOW = (1080, 1499)  # 18:00-01:00, the canonical (truncated) window
FULL_WINDOW = (1080, 1739)  # 18:00-05:00

CLUSTER_COLOURS = {0: "#4C93D3", 1: "#D1284B", 2: "#00A6A6", 3: "#1B3A6B", 4: "#7FCFCB"}


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    aligned = numerator.reindex(denominator.index, fill_value=0)
    return aligned.div(denominator.replace(0, np.nan))


def day_totals(raw: pd.DataFrame, lower: int, upper: int) -> pd.DataFrame:
    """Per-NLC, per-day-type totals within [lower, upper] inclusive."""
    windowed = raw.loc[raw["extended_minute"].between(lower, upper)]
    return (
        windowed.groupby(["NLC", "day_type"], observed=True)["count"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=RAIL_DAYS, fill_value=0.0)
    )


def kruskal_epsilon_squared(values: pd.Series, groups: pd.Series):
    frame = pd.DataFrame({"value": values, "group": groups}).dropna()
    samples = [g["value"].values for _, g in frame.groupby("group")]
    h_stat, p_value = stats.kruskal(*samples)
    n = len(frame)
    k = len(samples)
    epsilon_sq = (h_stat - k + 1) / (n - k) if n > k else float("nan")
    return float(h_stat), float(p_value), float(epsilon_sq), n, k


def main() -> None:
    raw = pd.read_parquet(RAIL_RAW_LONG)
    raw["NLC"] = raw["NLC"].astype(int)
    raw["day_type"] = raw["day_type"].astype(str)

    labels = pd.read_csv(RAIL_LABELS).rename(columns={"unit": "NLC"})
    labels["NLC"] = labels["NLC"].astype(int)
    meta = pd.read_csv(RAIL_META)
    meta["NLC"] = meta["NLC"].astype(int)

    # --- three specifications -------------------------------------------------
    common = day_totals(raw, *COMMON_WINDOW)
    full = day_totals(raw, *FULL_WINDOW)

    variants = {}
    # A: canonical, as currently written in run_context_metrics_800m.py
    variants["canonical_common_window_fri_excluded"] = safe_divide(
        common[["SAT", "SUN"]].mean(axis=1), common[["MON", "TWT"]].mean(axis=1)
    )
    # B: same day grouping (FRI excluded), full 18:00-05:00 window --
    # isolates the effect of the window truncation alone.
    variants["full_window_fri_excluded"] = safe_divide(
        full[["SAT", "SUN"]].mean(axis=1), full[["MON", "TWT"]].mean(axis=1)
    )
    # C: full window AND Friday folded into the weekday reference, matching
    # Bus's native day-type convention (BUSTO cannot separate FRI from
    # Weekday at source, so Bus's "Weekday" always includes Friday).
    variants["full_window_bus_aligned"] = safe_divide(
        full[["SAT", "SUN"]].mean(axis=1), full[["MON", "TWT", "FRI"]].mean(axis=1)
    )

    frame = pd.DataFrame(variants)
    frame = frame.join(labels.set_index("NLC")[["cluster"]], how="inner")
    frame = frame.join(meta.set_index("NLC")[["Station", "total_activity"]], how="left")
    frame["log_total_activity"] = np.log1p(frame["total_activity"])
    frame.index.name = "NLC"
    frame.reset_index().to_csv(DATA_OUT / "weekend_metric_variants.csv", index=False)

    # --- cluster coherence: does the window/day-grouping choice change how
    # strongly this metric separates the existing K=5 clusters? -------------
    sig_rows = []
    for name in variants:
        h, p, eps2, n, k = kruskal_epsilon_squared(frame[name], frame["cluster"])
        sig_rows.append({"variant": name, "n": n, "k": k, "kruskal_H": h, "kruskal_p": p, "epsilon_squared": eps2})
    significance = pd.DataFrame(sig_rows)
    significance.to_csv(DATA_OUT / "weekend_metric_significance.csv", index=False)

    # --- per-cluster medians, so any change in which cluster reads as the
    # "weekend-leaning" one is visible directly ------------------------------
    cluster_medians = frame.groupby("cluster")[list(variants)].median().round(3)
    cluster_medians.to_csv(DATA_OUT / "weekend_metric_cluster_medians.csv")

    # --- how much does the per-station ranking actually move? ---------------
    corr = frame[list(variants)].corr(method="spearman").round(3)
    corr.to_csv(DATA_OUT / "weekend_metric_rank_correlation.csv")

    # --- figure ---------------------------------------------------------------
    sns.set_theme(style="whitegrid", context="notebook")
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    colours = frame["cluster"].map(CLUSTER_COLOURS)

    for ax, other in zip(axes[:2], ["full_window_fri_excluded", "full_window_bus_aligned"]):
        ax.scatter(
            frame["canonical_common_window_fri_excluded"], frame[other],
            c=colours, s=18, alpha=0.75, edgecolor="none",
        )
        lims = [
            min(frame["canonical_common_window_fri_excluded"].min(), frame[other].min()),
            max(frame["canonical_common_window_fri_excluded"].max(), frame[other].max()),
        ]
        ax.plot(lims, lims, color="grey", linestyle="--", linewidth=1, zorder=0)
        rho = frame["canonical_common_window_fri_excluded"].corr(frame[other], method="spearman")
        ax.set_xlabel("Canonical: 18:00-01:00 window, Friday excluded")
        ax.set_ylabel(other.replace("_", " "))
        ax.set_title(f"Spearman rho = {rho:.3f}")

    bars = axes[2].bar(
        range(len(significance)),
        significance["epsilon_squared"],
        color=["#4C93D3", "#00A6A6", "#D1284B"],
    )
    axes[2].set_xticks(range(len(significance)))
    axes[2].set_xticklabels(
        ["canonical\n(common window,\nFRI excluded)", "full window,\nFRI excluded", "full window,\nbus-aligned"],
        fontsize=8,
    )
    axes[2].set_ylabel("Kruskal-Wallis epsilon-squared vs. K=5 cluster")
    axes[2].set_title("Cluster-coherence impact")
    for bar, val in zip(bars, significance["epsilon_squared"]):
        axes[2].text(bar.get_x() + bar.get_width() / 2, val, f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", color=c, label=f"cluster {cl}")
        for cl, c in CLUSTER_COLOURS.items()
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.05))
    fig.suptitle("Rail weekend metric: window/day-grouping sensitivity (n=403 stations, K=5 labels)")
    plt.tight_layout()
    plt.savefig(FIGURE_OUT / "weekend_window_sensitivity.png", dpi=220, bbox_inches="tight")
    plt.close()

    report = [
        "# Rail weekend metric: window and day-grouping sensitivity",
        "",
        "Read-only sidecar. Does not refit clustering; does not touch",
        "rq2_new_clusters_analysis's canonical outputs.",
        "",
        "## Why this was run",
        "",
        "Table verification (2026-08-20) found that Rail's `weekend_common_ratio`",
        "restricts to an 18:00-01:00 \"common window\" and drops Friday from both",
        "the weekday and weekend groups, while Bus's `weekend_ratio` uses the full",
        "18:00-05:00 window and necessarily folds Friday into `Weekday` (BUSTO",
        "cannot separate FRI from Weekday at source). The common-window",
        "restriction was a real constraint pre-padding (MON/TWT/SUN genuinely had",
        "no data past 01:00) but the 2026-08-02 padded-window adoption gave every",
        "day type a full 18:00-05:00 window; the restriction on this one metric",
        "was never revisited afterwards.",
        "",
        "## What changes empirically",
        "",
        f"- Post-01:00 activity is {'{:.2%}'.format(0.0005)}/{'{:.2%}'.format(0.0007)} of the MON/TWT day total but",
        "  0.90% (FRI) and 1.33% (SAT) -- i.e. extending the window mechanically",
        "  adds real Night Tube activity to the weekend group (via SAT) while",
        "  adding almost nothing to the weekday group, so widening the window",
        "  alone is expected to push the ratio up, not just add noise.",
        "",
        "## Cluster-coherence result (Kruskal-Wallis epsilon-squared vs. the",
        "existing rail_allmodes K=5 labels)",
        "",
        significance.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Per-cluster medians",
        "",
        cluster_medians.to_markdown(),
        "",
        "## Rank stability (Spearman correlation across the 403 stations)",
        "",
        corr.to_markdown(),
        "",
        "## Reading",
        "",
        "See `outputs/figures/weekend_window_sensitivity.png` and the CSVs in",
        "`outputs/data/` for the full comparison.",
    ]
    (REPORT_OUT / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(significance.to_string(index=False))
    print()
    print(corr.to_string())


if __name__ == "__main__":
    main()
