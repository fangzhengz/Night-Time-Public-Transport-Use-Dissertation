# -*- coding: utf-8 -*-
"""Entry/exit temporal-shape comparison between C1a (remainder) and C1b
(West End night-origin core), on the same feature matrix and nested labels
that 01_c2_substructure.py produced.

Each station's entry_* row sums to 1 across the full week (same for exit_*),
so the group mean is the average share-of-week-entries (or exits) per
15-minute bin -- exactly what the GMM clustered on. Comparing these means is
what the split's scalar metrics (direction_balance, weekend_common_ratio,
...) are summarising; this makes the underlying curves visible.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve()
NUMBAT = HERE.parents[2]
OUT = HERE.parents[1] / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

CANON_X = NUMBAT / "outputs" / "data" / "X_rail_allmodes.parquet"
DAYS = ["MON", "TWT", "FRI", "SAT", "SUN"]


def minute_to_label(m: int) -> str:
    h, mm = divmod(m, 60)
    return f"{h % 24:02d}:{mm:02d}"


def main() -> None:
    X = pd.read_parquet(CANON_X)
    X.index = X.index.astype(str)
    nested = pd.read_csv(
        OUT / "rail_allmodes_k5_nested_labels.csv", dtype={"unit": str}
    ).set_index("unit")["cluster_nested"]

    core = nested.index[nested == 5]
    remainder = nested.index[nested == 1]
    groups = {
        f"C1b night-origin core (n={len(core)})": core,
        f"C1a remainder (n={len(remainder)})": remainder,
    }

    fig, axes = plt.subplots(len(DAYS), 2, figsize=(12, 14), sharex=True)
    colors = dict(zip(groups, ["#c0392b", "#2874a6"], strict=True))

    crossover_rows = []
    for row, day in enumerate(DAYS):
        for col, direction in enumerate(["entry", "exit"]):
            ax = axes[row, col]
            cols = [c for c in X.columns if c.startswith(f"{direction}_{day}_")]
            minutes = sorted(int(c.rsplit("_", 1)[1]) for c in cols)
            ordered_cols = [f"{direction}_{day}_{m}" for m in minutes]
            for label, members in groups.items():
                curve = X.loc[members, ordered_cols].mean(axis=0)
                ax.plot(minutes, curve.to_numpy(), label=label, color=colors[label], linewidth=1.6)
            ax.set_title(f"{day}  {direction}", fontsize=9, loc="left")
            ax.axvline(1500, color="grey", linewidth=0.6, linestyle=":")  # 01:00
            if row == len(DAYS) - 1:
                ticks = [m for m in minutes if m % 60 == 0]
                ax.set_xticks(ticks)
                ax.set_xticklabels([minute_to_label(m) for m in ticks], rotation=45, fontsize=7)
        for label, members in groups.items():
            entry_cols = [f"entry_{day}_{m}" for m in minutes]
            exit_cols = [f"exit_{day}_{m}" for m in minutes]
            entry_curve = X.loc[members, entry_cols].mean(axis=0).to_numpy()
            exit_curve = X.loc[members, exit_cols].mean(axis=0).to_numpy()
            diff = exit_curve - entry_curve
            after_2100 = [i for i, m in enumerate(minutes) if m >= 1260]
            cross_minute = None
            for i in after_2100:
                if diff[i] > 0:
                    cross_minute = minutes[i]
                    break
            crossover_rows.append(
                {"day": day, "group": label,
                 "exit_over_entry_from": minute_to_label(cross_minute) if cross_minute else "never (by window end)"}
            )

    axes[0, 0].legend(loc="upper right", fontsize=8)
    fig.suptitle("C1 nested split: entry/exit share-of-week profile, C1a vs C1b", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(OUT / "c1ab_temporal_profile.png", dpi=170, bbox_inches="tight")
    fig.savefig(OUT / "c1ab_temporal_profile.pdf", bbox_inches="tight")
    plt.close(fig)

    crossover = pd.DataFrame(crossover_rows)
    crossover.to_csv(OUT / "c1ab_exit_over_entry_crossover.csv", index=False)

    post_rows = []
    for day in DAYS:
        for direction in ["entry", "exit"]:
            cols_all = [c for c in X.columns if c.startswith(f"{direction}_{day}_")]
            cols_post = [c for c in cols_all if int(c.rsplit("_", 1)[1]) >= 1500]
            for label, members in groups.items():
                share = X.loc[members, cols_post].sum(axis=1).mean()
                post_rows.append({"day": day, "direction": direction, "group": label,
                                   "mean_post_0100_share_of_week": share})
    post_df = pd.DataFrame(post_rows)
    post_df.to_csv(OUT / "c1ab_post0100_by_daytype.csv", index=False)

    print(crossover.to_string(index=False))
    print()
    pivot = post_df.pivot_table(index=["day", "direction"], columns="group",
                                 values="mean_post_0100_share_of_week")
    print(pivot.to_string(float_format=lambda x: f"{x:.5f}"))
    print()
    print("Saved to", OUT)


if __name__ == "__main__":
    main()
