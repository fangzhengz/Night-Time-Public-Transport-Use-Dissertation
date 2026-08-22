# -*- coding: utf-8 -*-
"""06 - Emit the canonical bus cluster names, and verify them against the data.

WHY THIS EXISTS
---------------
Rail went through exactly this problem in 2026-08: cluster names lived as
hardcoded dicts copy-pasted into three separate downstream files
(analysis/05_reporting, analysis/04_urban_context, analysis/05_reporting).
GMM component ids are arbitrary, so any refit silently invalidates every copy
at once -- each keeps running and keeps attaching the wrong name to the wrong
cluster. Bus has never been refit since the names were first coined, so this
has not yet caused a wrong number in a report, but it is the same latent risk
analysis/02_mode_specific_clustering/rail/src/09_cluster_names.py was written to close for rail.
This script closes it for bus.

This script is the single source. Downstream code reads
`outputs_1805_min33/data/bus_cluster_names.csv`; cluster names are not
duplicated by hand.

VERIFICATION, NOT DECORATION
-----------------------------
Every name here carries a machine-checkable claim, asserted on each run:

  night-persistent      must have the highest mean activity, post-midnight
                        share, post-midnight persistence AND weekend ratio
                        (it currently wins on all four simultaneously)
  peripheral, low-flow   must have the lowest mean activity, post-midnight
                        share, post-midnight persistence AND weekend ratio
                        (the mirror image of night-persistent)
  moderate, directional  of the two clusters left once the extremes above are
                        removed, must have the more negative direction
                        balance
  moderate-to-high flow  of the same two, must have the higher mean activity

If a refit breaks any of these the run fails, which is the intended
behaviour: the names must be re-derived rather than carried forward on trust.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_samples

# Adopted 18:00-05:00, minimum-direction 33 output layer.
ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "outputs_1805_min33" / "clr" / "labels" / "k4_labels.csv"
METRICS = ROOT / "outputs_1805_min33" / "features" / "sample_metrics.csv"
X_PATH = ROOT / "outputs_1805_min33" / "features" / "X_bus_stoparea_clr_min33.parquet"
DATA_OUT = ROOT / "outputs_1805_min33" / "data"
OUTPUT = DATA_OUT / "bus_cluster_names.csv"

# role -> (english, short). Roles are assigned from the data below; the
# mapping from role to cluster id is never written by hand.
# Updated 2026-08-08, user decision: aligned to the wording already used in
# the Results write-up (结果部分整理.docx).
# "short" for moderate_directional updated 2026-08-20, user decision: was
# "moderate, destination-leaning", changed to "moderate alighting-oriented"
# after being patched piecemeal into several presentation figures first.
NAMES = {
    "night_persistent": ("relatively high activity, stronger night-persistence", "night-persistent"),
    "peripheral_low_flow": ("low activity, weak night-persistence", "low activity"),
    "moderate_directional": ("moderate activity with destination characteristics", "moderate alighting-oriented"),
    "moderate_to_high_flow": ("moderate activity and persistence, transitional", "moderate, transitional"),
}


def main() -> None:
    labels = pd.read_csv(LABELS, dtype={"lsoa": str})
    labels = labels.loc[labels["cluster"] != -1, ["lsoa", "cluster"]].set_index("lsoa")

    metrics = pd.read_csv(METRICS, dtype={"lsoa": str}).set_index("lsoa")

    X = pd.read_parquet(X_PATH)
    X.index = X.index.astype(str)
    X = X.reindex(labels.index)

    silhouette = pd.Series(
        silhouette_samples(X.to_numpy(float), labels["cluster"].to_numpy()),
        index=X.index,
    )

    frame = labels.join(metrics[[
        "log_total_activity", "direction_balance", "post_midnight_share",
        "post_midnight_persistence", "weekend_ratio",
    ]])
    frame["silhouette"] = silhouette
    summary = frame.groupby("cluster").agg(
        n=("silhouette", "size"),
        log_total_activity=("log_total_activity", "mean"),
        direction_balance=("direction_balance", "mean"),
        post_midnight_share=("post_midnight_share", "mean"),
        post_midnight_persistence=("post_midnight_persistence", "mean"),
        weekend_ratio=("weekend_ratio", "mean"),
        mean_silhouette=("silhouette", "mean"),
    )

    # --- assign roles from the data ------------------------------------------
    role = {}
    role["night_persistent"] = int(summary["log_total_activity"].idxmax())
    remaining = summary.drop(index=role["night_persistent"])
    role["peripheral_low_flow"] = int(remaining["log_total_activity"].idxmin())
    remaining = remaining.drop(index=role["peripheral_low_flow"])
    role["moderate_directional"] = int(remaining["direction_balance"].idxmin())
    remaining = remaining.drop(index=role["moderate_directional"])
    if len(remaining) != 1:
        raise RuntimeError(f"Expected one cluster left, got {list(remaining.index)}")
    role["moderate_to_high_flow"] = int(remaining.index[0])

    # --- assert the names actually describe their clusters --------------------
    checks = [
        ("night-persistent has the highest activity",
         summary["log_total_activity"].idxmax() == role["night_persistent"]),
        ("night-persistent has the highest post-midnight share",
         summary["post_midnight_share"].idxmax() == role["night_persistent"]),
        ("night-persistent has the highest post-midnight persistence",
         summary["post_midnight_persistence"].idxmax() == role["night_persistent"]),
        ("night-persistent has the highest weekend ratio",
         summary["weekend_ratio"].idxmax() == role["night_persistent"]),
        ("peripheral low-flow has the lowest activity",
         summary["log_total_activity"].idxmin() == role["peripheral_low_flow"]),
        ("peripheral low-flow has the lowest post-midnight share",
         summary["post_midnight_share"].idxmin() == role["peripheral_low_flow"]),
        ("peripheral low-flow has the lowest post-midnight persistence",
         summary["post_midnight_persistence"].idxmin() == role["peripheral_low_flow"]),
        ("peripheral low-flow has the lowest weekend ratio",
         summary["weekend_ratio"].idxmin() == role["peripheral_low_flow"]),
        ("moderate-directional has a more negative direction balance than "
         "moderate-to-high-flow",
         summary.loc[role["moderate_directional"], "direction_balance"]
         < summary.loc[role["moderate_to_high_flow"], "direction_balance"]),
        ("moderate-to-high-flow has higher activity than moderate-directional",
         summary.loc[role["moderate_to_high_flow"], "log_total_activity"]
         > summary.loc[role["moderate_directional"], "log_total_activity"]),
    ]
    failed = [message for message, ok in checks if not ok]
    for message, ok in checks:
        print(f"  [{'ok ' if ok else 'FAIL'}] {message}")
    if failed:
        raise RuntimeError(
            "Cluster names no longer match the data; re-derive them rather than "
            "carrying them forward. Failed: " + "; ".join(failed)
        )

    rows = []
    for key, cluster in role.items():
        english, short = NAMES[key]
        rows.append({
            "cluster": cluster, "role": key,
            "name_en": f"C{cluster} {english}",
            "short": short, "n": int(summary.loc[cluster, "n"]),
            "log_total_activity": round(float(summary.loc[cluster, "log_total_activity"]), 4),
            "direction_balance": round(float(summary.loc[cluster, "direction_balance"]), 4),
            "post_midnight_share": round(float(summary.loc[cluster, "post_midnight_share"]), 4),
            "post_midnight_persistence": round(
                float(summary.loc[cluster, "post_midnight_persistence"]), 4),
            "weekend_ratio": round(float(summary.loc[cluster, "weekend_ratio"]), 4),
            "mean_silhouette": round(float(summary.loc[cluster, "mean_silhouette"]), 4),
        })
    names = pd.DataFrame(rows).sort_values("cluster")
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    names.to_csv(OUTPUT, index=False)
    print()
    print(names.to_string(index=False))
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
