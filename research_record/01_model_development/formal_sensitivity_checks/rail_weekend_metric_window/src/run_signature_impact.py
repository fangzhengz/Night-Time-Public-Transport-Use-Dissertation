# -*- coding: utf-8 -*-
"""Does the weekend-window/Friday-grouping choice change the actual
post-clustering descriptor chart (rail_cluster_signature_z.csv -> the
"Post-clustering behavioural descriptors" figure in the dissertation)?

Unlike run_weekend_window_sensitivity.py (which tested whether the metric
still separates the K=5 clusters -- the wrong question, since these four
metrics are posterior descriptors used to characterise already-fitted
clusters, not clustering features being validated), this script reproduces
the exact robust_signature() computation used by
rq2_new_clusters_analysis/src/run_context_metrics.py and the exact chart
style used by dissertation_working/scripts/build_ch4_final_figures.py's
night_behaviour_z(), then swaps in the alternative weekend metric to see
whether the plotted bars -- and the one written claim tied to this metric
("C0 has the weakest relative weekend activity", main body para 269) --
would change.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
for d in (DATA_OUT, FIGURE_OUT):
    d.mkdir(parents=True, exist_ok=True)

RAIL_DAYS = ["MON", "TWT", "FRI", "SAT", "SUN"]
RAIL_WINDOWS = {day: (1080, 1740) for day in RAIL_DAYS}  # canonical padded window, all metrics but weekend
COMMON_WINDOW = (1080, 1499)  # 18:00-01:00
FULL_WINDOW = (1080, 1739)

PALETTE = {0: "#4C93D3", 1: "#D1284B", 2: "#00A6A6", 3: "#1B3A6B", 4: "#7FCFCB"}
LABELS = {
    "log_total_activity": "Night-time activity (log)",
    "direction_balance": "Directional balance",
    "post_2300_share": "Post-23:00 share",
    "weekend_common_ratio": "Weekend-to-weekday ratio",
}


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    aligned = numerator.reindex(denominator.index, fill_value=0)
    return aligned.div(denominator.replace(0, np.nan))


def sum_window(frame, lower, upper, days=None):
    mask = frame["extended_minute"].between(lower, upper - 1)
    if days is not None:
        mask &= frame["day_type"].isin(days)
    return frame.loc[mask].groupby("NLC")["count"].sum()


def day_totals(raw: pd.DataFrame, lower: int, upper: int) -> pd.DataFrame:
    windowed = raw.loc[raw["extended_minute"].between(lower, upper)]
    return (
        windowed.groupby(["NLC", "day_type"], observed=True)["count"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=RAIL_DAYS, fill_value=0.0)
    )


def robust_signature(frame: pd.DataFrame, cluster: str, metrics: list[str]) -> pd.DataFrame:
    """Exact copy of run_context_metrics.py's robust_signature: median
    deviation from the overall median, scaled by the overall IQR."""
    medians = frame.groupby(cluster)[metrics].median()
    overall_median = frame[metrics].median()
    iqr = frame[metrics].quantile(0.75) - frame[metrics].quantile(0.25)
    return medians.sub(overall_median).div(iqr.replace(0, np.nan)).fillna(0)


def build_base_frame(raw: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    """Reproduces log_total_activity, direction_balance and post_2300_share
    exactly as run_context_metrics.py's build_rail_metrics() does, over the
    canonical padded 18:00-05:00 window for every day type. Only the
    weekend metric is left to be attached separately per variant."""
    windowed = pd.concat(
        [raw.loc[(raw["day_type"] == day) & raw["extended_minute"].between(lower, upper - 1)]
         for day, (lower, upper) in RAIL_WINDOWS.items()],
        ignore_index=True,
    )
    total = windowed.groupby("NLC")["count"].sum()
    post_2300 = sum_window(windowed, 1380, 1740)

    direction = (
        windowed.groupby(["NLC", "direction"])["count"].sum().unstack(fill_value=0)
        .reindex(columns=["entry", "exit"], fill_value=0)
    )
    frame = pd.DataFrame(index=total.index)
    frame["total_activity"] = total
    frame["log_total_activity"] = np.log1p(total)
    frame["direction_balance"] = safe_divide(
        direction["entry"] - direction["exit"], direction["entry"] + direction["exit"]
    )
    frame["post_2300_share"] = safe_divide(post_2300, total)
    frame.index.name = "NLC"
    return frame.join(labels.set_index("NLC")[["cluster"]], how="inner")


def main() -> None:
    raw = pd.read_parquet(RAIL_RAW_LONG)
    raw["NLC"] = raw["NLC"].astype(int)
    raw["day_type"] = raw["day_type"].astype(str)

    labels = pd.read_csv(RAIL_LABELS).rename(columns={"unit": "NLC"})
    labels["NLC"] = labels["NLC"].astype(int)

    base = build_base_frame(raw, labels)

    common = day_totals(raw, *COMMON_WINDOW)
    full = day_totals(raw, *FULL_WINDOW)
    weekend_variants = {
        "canonical": safe_divide(common[["SAT", "SUN"]].mean(axis=1), common[["MON", "TWT"]].mean(axis=1)),
        "full_window_fri_excluded": safe_divide(full[["SAT", "SUN"]].mean(axis=1), full[["MON", "TWT"]].mean(axis=1)),
        "full_window_bus_aligned": safe_divide(full[["SAT", "SUN"]].mean(axis=1), full[["MON", "TWT", "FRI"]].mean(axis=1)),
    }

    metrics = ["log_total_activity", "direction_balance", "post_2300_share", "weekend_common_ratio"]
    signatures = {}
    weekend_rows = {}
    for name, series in weekend_variants.items():
        frame = base.copy()
        frame["weekend_common_ratio"] = series.reindex(frame.index)
        sig = robust_signature(frame, "cluster", metrics)
        signatures[name] = sig
        weekend_rows[name] = sig["weekend_common_ratio"]
        sig.to_csv(DATA_OUT / f"rail_cluster_signature_z_{name}.csv")

    weekend_compare = pd.DataFrame(weekend_rows).round(3)
    weekend_compare.index.name = "cluster"
    weekend_compare.to_csv(DATA_OUT / "weekend_row_comparison.csv")
    print(weekend_compare.to_string())

    # --- reproduce the exact chart style, canonical vs bus-aligned side by side ---
    n_clusters = len(base["cluster"].unique())
    for name in ("canonical", "full_window_bus_aligned"):
        sig = signatures[name]
        lim = max(1.0, float(np.abs(sig.to_numpy(dtype=float)).max()) * 1.08)
        fig, axes = plt.subplots(n_clusters, 1, figsize=(8.8, 1.45 * n_clusters + 0.7), sharex=True)
        for c, ax in zip(sorted(sig.index), axes):
            values = sig.loc[c, metrics]
            pos = np.arange(len(values))[::-1]
            ax.barh(pos, values.to_numpy(), color=["#C64036" if v > 0 else "#2878B5" for v in values], height=0.62)
            ax.axvline(0, color="#333", lw=1.6)
            ax.grid(axis="x", alpha=0.22)
            ax.set_axisbelow(True)
            ax.set_yticks(pos, [LABELS[m] for m in values.index], fontsize=8)
            ax.set_xlim(-lim, lim)
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.set_title(f"C{c}", loc="left", color=PALETTE[int(c)], weight="bold", fontsize=10)
        axes[-1].set_xlabel("Z-score relative to Rail-wide mean")
        subtitle = "canonical (18:00-01:00 window, Friday excluded)" if name == "canonical" else "full 18:00-05:00 window, Friday folded into weekday (bus-aligned)"
        fig.suptitle(f"Post-clustering behavioural descriptors -- weekend metric: {subtitle}", weight="bold", y=0.995, fontsize=11)
        fig.tight_layout(rect=(0, 0, 1, 0.97))
        fig.savefig(FIGURE_OUT / f"signature_reproduction_{name}.png", dpi=220, bbox_inches="tight")
        plt.close(fig)

    # --- direct side-by-side of just the weekend row, the one that changes definition ---
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(n_clusters)
    width = 0.25
    variant_order = ["canonical", "full_window_fri_excluded", "full_window_bus_aligned"]
    variant_colours = ["#333333", "#00A6A6", "#D1284B"]
    variant_display = ["Canonical\n(18:00-01:00, FRI excluded)", "Full window,\nFRI excluded", "Full window,\nbus-aligned (FRI in weekday)"]
    for i, (name, colour, disp) in enumerate(zip(variant_order, variant_colours, variant_display)):
        ax.bar(x + (i - 1) * width, weekend_compare[name].reindex(sorted(sig.index)), width, label=disp, color=colour)
    ax.axhline(0, color="#333", lw=1)
    ax.set_xticks(x, [f"C{c}" for c in sorted(sig.index)])
    ax.set_ylabel("Weekend-to-weekday ratio\n(z-score relative to Rail-wide mean)")
    ax.set_title("Impact of window/day-grouping choice on the plotted weekend-ratio row", loc="left", weight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.22)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIGURE_OUT / "weekend_row_direct_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # --- check the one written claim: "C0 has the weakest relative weekend activity" ---
    ranks = weekend_compare.rank(axis=0)
    claim_holds = (ranks.loc[0] == 1).all()
    print()
    print("Claim check -- 'C0 has the weakest relative weekend activity among the five clusters':")
    print(weekend_compare)
    print(f"C0 is the minimum in all three variants: {claim_holds}")


if __name__ == "__main__":
    main()
