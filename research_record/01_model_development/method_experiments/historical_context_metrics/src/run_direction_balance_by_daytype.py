"""Break direction_balance down by day-type, per RQ1 cluster.

The main context-metrics script (run_rq1_context_analysis.py) computes
direction_balance once over the whole week per unit. That single number is a
volume-weighted average across day-types, so it can hide real weekday/weekend
asymmetry within a cluster (e.g. a cluster whose entry/exit imbalance is
purely a commute effect and collapses at the weekend, vs one whose imbalance
persists all week). This script recomputes direction_balance separately for
each (cluster, day_type) pair, pooling counts across all units in the
cluster first (volume-weighted), so the day-type pattern within each cluster
is visible.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]
RQ1 = FYP / "cluster_clean_version_fullweek"
PRE = FYP / "cluster_clean_version_grouped" / "outputs" / "preprocessed"

RAIL_RAW = FYP / "outputs" / "preprocessed_numbat" / "numbat_lu_station_qhr_all_daytypes.parquet"
BUS_LONG = PRE / "bus_lsoa_night_long.parquet"
RAIL_LABELS = RQ1 / "outputs" / "labels" / "rail_k5_labels.csv"
BUS_LABELS = RQ1 / "outputs" / "labels" / "bus_k3_labels.csv"

OUT = ROOT / "outputs"
DATA = OUT / "data"
FIGURES = OUT / "figures"
for directory in (DATA, FIGURES):
    directory.mkdir(parents=True, exist_ok=True)

RAIL_WINDOWS = {
    "MON": (1080, 1500),
    "TWT": (1080, 1500),
    "FRI": (1080, 1740),
    "SAT": (1080, 1740),
    "SUN": (1080, 1500),
}
RAIL_DAY_ORDER = list(RAIL_WINDOWS)
BUS_DAY_ORDER = ["Weekday", "Saturday", "Sunday"]


def pooled_direction_balance(
    frame: pd.DataFrame, group_cols: list[str], positive: str, negative: str
) -> pd.DataFrame:
    """Sum counts within each group first, then take one (pos-neg)/(pos+neg)
    ratio per group -- a volume-weighted balance, not a mean of per-unit ratios."""
    totals = (
        frame.groupby(group_cols + ["direction"])["count"]
        .sum()
        .unstack("direction", fill_value=0)
        .reindex(columns=[positive, negative], fill_value=0)
    )
    out = totals.copy()
    out["direction_balance"] = (totals[positive] - totals[negative]) / (
        totals[positive] + totals[negative]
    )
    return out.reset_index()


def build_rail() -> pd.DataFrame:
    raw = pd.read_parquet(RAIL_RAW).copy()
    raw["NLC"] = raw["NLC"].astype(int)
    raw["day_type"] = raw["day_type"].astype(str)
    raw = pd.concat(
        [
            raw.loc[(raw["day_type"] == day) & raw["extended_minute"].between(lower, upper - 1)]
            for day, (lower, upper) in RAIL_WINDOWS.items()
        ],
        ignore_index=True,
    )

    labels = pd.read_csv(RAIL_LABELS).rename(columns={"unit": "NLC"})
    labels["NLC"] = labels["NLC"].astype(int)
    raw = raw.merge(labels[["NLC", "cluster"]], on="NLC", how="left")

    result = pooled_direction_balance(raw, ["cluster", "day_type"], "entry", "exit")
    result["mode"] = "rail"
    return result


def build_bus() -> pd.DataFrame:
    long = pd.read_parquet(BUS_LONG).copy()
    long["lsoa"] = long["lsoa"].astype(str)

    labels = pd.read_csv(BUS_LABELS).rename(columns={"unit": "lsoa"})
    labels["lsoa"] = labels["lsoa"].astype(str)
    long = long.merge(labels[["lsoa", "cluster"]], on="lsoa", how="left")

    result = pooled_direction_balance(long, ["cluster", "day_type"], "boardings", "alightings")
    result["mode"] = "bus"
    return result


def plot(rail: pd.DataFrame, bus: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for cluster, group in rail.groupby("cluster"):
        group = group.set_index("day_type").reindex(RAIL_DAY_ORDER)
        axes[0].plot(RAIL_DAY_ORDER, group["direction_balance"], marker="o", label=f"C{cluster}")
    axes[0].axhline(0, color="grey", linewidth=0.8)
    axes[0].set_title("Rail: direction_balance by day-type, per cluster")
    axes[0].set_ylabel("direction_balance (entry-dominant > 0)")
    axes[0].legend(fontsize=8, ncols=2)

    for cluster, group in bus.groupby("cluster"):
        group = group.set_index("day_type").reindex(BUS_DAY_ORDER)
        axes[1].plot(BUS_DAY_ORDER, group["direction_balance"], marker="o", label=f"C{cluster}")
    axes[1].axhline(0, color="grey", linewidth=0.8)
    axes[1].set_title("Bus: direction_balance by day-type, per cluster")
    axes[1].legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(FIGURES / "direction_balance_by_daytype.png", dpi=150)
    plt.close(fig)


def main() -> None:
    rail = build_rail()
    bus = build_bus()

    combined = pd.concat([rail, bus], ignore_index=True)
    combined = combined[["mode", "cluster", "day_type", "direction_balance"]]
    combined.to_csv(DATA / "direction_balance_by_daytype.csv", index=False)

    rail_wide = rail.pivot(index="cluster", columns="day_type", values="direction_balance")[
        RAIL_DAY_ORDER
    ]
    bus_wide = bus.pivot(index="cluster", columns="day_type", values="direction_balance")[
        BUS_DAY_ORDER
    ]
    rail_wide.round(3).to_csv(DATA / "rail_direction_balance_by_daytype_wide.csv")
    bus_wide.round(3).to_csv(DATA / "bus_direction_balance_by_daytype_wide.csv")

    plot(rail, bus)

    print("Rail direction_balance by day-type:")
    print(rail_wide.round(3))
    print("\nBus direction_balance by day-type:")
    print(bus_wide.round(3))
    print(f"\nSaved: {DATA / 'direction_balance_by_daytype.csv'}")
    print(f"Saved: {FIGURES / 'direction_balance_by_daytype.png'}")


if __name__ == "__main__":
    main()
