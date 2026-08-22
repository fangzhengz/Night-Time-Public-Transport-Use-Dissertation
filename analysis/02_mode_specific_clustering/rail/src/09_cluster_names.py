# -*- coding: utf-8 -*-
"""09 - Emit the canonical rail cluster names, and verify them against the data.

WHY THIS EXISTS
---------------
Cluster names used to live as hardcoded dicts in three separate downstream
files (`analysis/05_reporting`, `analysis/04_urban_context`,
`analysis/05_reporting`). GMM component ids are arbitrary, so the 2026-08-01
window change renumbered every cluster and silently invalidated all three at
once - each would have kept running and kept attaching the wrong name to the
right cluster. Two of the names were also wrong on their own terms before the
renumbering: the night-persistent cluster was called "secondary DLR/inner
mixed", which does not mention its defining property, and the 12-station
residual was called "airport & major terminus hub" although only four of its
members are airports.

This script is now the single source. Downstream reads
`outputs/data/rail_cluster_names.csv`; nothing hardcodes a name again.

VERIFICATION, NOT DECORATION
----------------------------
A name that merely sits in a file can still drift out of alignment with the
data. Every name here carries a machine-checkable claim, asserted on each run:

  night-persistent          must have the highest post-01:00 share
  central departure         must have the highest direction balance and be
                            the most central
  outer arrival             must have the lowest direction balance and be
                            the most peripheral
  central balanced          must have the direction balance closest to zero

If a refit breaks any of these the run fails, which is the intended behaviour:
the names must be re-derived rather than carried forward on trust.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_samples

ROOT = Path(__file__).resolve().parents[1]
FYP = Path(__file__).resolve().parents[4]
DATA = ROOT / "outputs" / "data"
X_PATH = DATA / "X_rail_allmodes.parquet"
LABELS = DATA / "rail_allmodes_k5_labels.csv"
RAW_LONG = (FYP / "analysis" / "01_data_preparation" / "rail" / "outputs" / "preprocessed"
            / "numbat_allmodes_station_qhr_all_daytypes_final.parquet")
COORDS = (FYP / "analysis" / "01_data_preparation" / "rail" / "outputs" / "data"
          / "rail_allmodes_coords.csv")
OUTPUT = DATA / "rail_cluster_names.csv"

WINDOW = (1080, 1740)          # unified 18:00-05:00
CENTRE = (530034.0, 180381.0)  # Charing Cross, BNG

# role -> (english, chinese, short). Roles are assigned from the data below;
# the mapping from role to cluster id is never written by hand.
# Updated 2026-08-08, user decision: aligned to the wording already used in
# the Results write-up (结果部分整理.docx), English labels for figures/tables.
NAMES = {
    "night_persistent": ("late-night, extended-duration persistent", "深夜长时间持续型", "late-night persistent"),
    "central_departure": ("central departure-oriented", "中心区出发倾向型", "central departure"),
    "central_balanced": ("central interchange, direction-balanced", "中心换乘与方向相对均衡型", "central balanced"),
    "outer_arrival": ("outer arrival-oriented", "外围到达倾向型", "outer arrival"),
    "inner_arrival": ("inner-middle ring mixed", "内-中圈混合型", "inner-middle mixed"),
}


def main() -> None:
    X = pd.read_parquet(X_PATH)
    X.index = X.index.astype(str)
    labels = pd.read_csv(LABELS, dtype={"unit": str}).set_index("unit")["cluster"]
    labels = labels.reindex(X.index)
    coords = pd.read_csv(COORDS, dtype={"unit": str}).set_index("unit")

    raw = pd.read_parquet(RAW_LONG)
    raw["NLC"] = raw["NLC"].astype(str)
    raw = raw[raw["extended_minute"].between(*[WINDOW[0], WINDOW[1] - 1])]

    def window_sum(low, high):
        mask = raw["extended_minute"].between(low, high - 1)
        return raw.loc[mask].groupby("NLC")["count"].sum()

    total = window_sum(*WINDOW)
    post = window_sum(1500, WINDOW[1])
    entry = raw[raw.direction == "entry"].groupby("NLC")["count"].sum()
    exit_ = raw[raw.direction == "exit"].groupby("NLC")["count"].sum()
    km = pd.Series(
        np.hypot(coords["easting"] - CENTRE[0], coords["northing"] - CENTRE[1]) / 1000.0,
        index=coords.index,
    )
    silhouette = pd.Series(
        silhouette_samples(X.to_numpy(float), labels.to_numpy()), index=X.index
    )

    frame = pd.DataFrame({
        "cluster": labels,
        "post_0100_share": (post / total).reindex(X.index),
        "direction_balance": ((entry - exit_) / (entry + exit_)).reindex(X.index),
        "km_to_centre": km.reindex(X.index),
        "silhouette": silhouette,
    }).dropna(subset=["cluster"])
    summary = frame.groupby("cluster").agg(
        n=("silhouette", "size"),
        post_0100_share=("post_0100_share", "mean"),
        direction_balance=("direction_balance", "mean"),
        km_to_centre=("km_to_centre", "mean"),
        mean_silhouette=("silhouette", "mean"),
    )

    # --- assign roles from the data ------------------------------------------
    role = {}
    role["night_persistent"] = int(summary["post_0100_share"].idxmax())
    remaining = summary.drop(index=role["night_persistent"])
    role["central_departure"] = int(summary["direction_balance"].idxmax())
    remaining = remaining.drop(index=role["central_departure"])
    role["outer_arrival"] = int(summary["direction_balance"].idxmin())
    remaining = remaining.drop(index=role["outer_arrival"])
    role["central_balanced"] = int(remaining["direction_balance"].abs().idxmin())
    remaining = remaining.drop(index=role["central_balanced"])
    if len(remaining) != 1:
        raise RuntimeError(f"Expected one cluster left, got {list(remaining.index)}")
    role["inner_arrival"] = int(remaining.index[0])

    # --- assert the names actually describe their clusters --------------------
    checks = [
        ("night-persistent has the highest post-01:00 share",
         summary["post_0100_share"].idxmax() == role["night_persistent"]),
        ("central departure has the highest direction balance",
         summary["direction_balance"].idxmax() == role["central_departure"]),
        ("central departure is the most central",
         summary["km_to_centre"].idxmin() == role["central_departure"]),
        ("outer arrival has the lowest direction balance",
         summary["direction_balance"].idxmin() == role["outer_arrival"]),
        ("outer arrival is the most peripheral",
         summary["km_to_centre"].idxmax() == role["outer_arrival"]),
        ("central balanced has direction balance closest to zero",
         summary["direction_balance"].abs().idxmin() == role["central_balanced"]),
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
        english, chinese, short = NAMES[key]
        member = frame.index[frame["cluster"] == cluster]
        top = ", ".join(
            str(coords["Station"].get(u, u))
            for u in sorted(member, key=lambda u: -total.get(u, 0))[:4]
        )
        rows.append({
            "cluster": cluster, "role": key,
            "name_en": f"C{cluster} {english}", "name_zh": f"C{cluster} {chinese}",
            "short": short, "n": int(summary.loc[cluster, "n"]),
            "post_0100_share": round(float(summary.loc[cluster, "post_0100_share"]), 4),
            "direction_balance": round(float(summary.loc[cluster, "direction_balance"]), 4),
            "km_to_centre": round(float(summary.loc[cluster, "km_to_centre"]), 2),
            "mean_silhouette": round(float(summary.loc[cluster, "mean_silhouette"]), 4),
            "example_stations": top,
        })
    names = pd.DataFrame(rows).sort_values("cluster")
    # utf-8-sig: name_zh is genuine Chinese text; without a BOM, Excel on a
    # Chinese-locale Windows machine defaults to GBK and garbles it.
    names.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print()
    print(names.to_string(index=False))
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
