# -*- coding: utf-8 -*-
"""Second-stage split of the adopted C4, emitted as a usable downstream label.

WHY A NESTED LABEL RATHER THAN A NEW CLUSTERING
-----------------------------------------------
The night-origin core (West End, Strand, Shoreditch) is a real structure: its
stations occupy ranks 7-22 of 404 on direction balance. But no single-stage GMM
isolates it reproducibly -- padded K=7 finds it in 2 of 10 seeds, and the padded
K=5 fit that appeared to find it was simply not converged (BIC 709.7 worse than
the n_init>=50 optimum, see 06).

Splitting C4 in a documented second stage gets the same group at 10/10 seed
reproducibility, on the UNCHANGED canonical feature matrix, without touching the
adopted five-cluster result. The primary typology stays exactly as adopted; this
adds a nested level that downstream analysis can switch on or off.

MEMBERSHIP IS A CROSS-SEED CONSENSUS, not one fit. A station joins the core only
if it lands with the core in at least CONSENSUS_THRESHOLD of SEEDS fits, so the
emitted label does not inherit any single run's luck.

OUTPUT SCHEMA (`rail_allmodes_k5_nested_labels.csv`)
  unit                 station NLC, matching rail_allmodes_k5_labels.csv
  cluster              adopted 0-4, copied through unchanged
  cluster_nested       0-3 as adopted; 4 = C4 remainder; 5 = night-origin core
  west_end_core        boolean convenience flag
  core_seed_support    fraction of seeds placing the station with the core

Downstream folders can keep using `cluster` and ignore the rest, or switch to
`cluster_nested` and set RAIL_K = 6. Both are reproducible from this file.

CAVEAT TO CARRY: the core is 13 stations. That is ample for description and for
the narrative, but thin for catchment-based association tests -- an 800 m
catchment aggregate over 13 stations has wide uncertainty. Report effect sizes
for it descriptively; do not lean on significance.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

warnings.filterwarnings("ignore", category=ConvergenceWarning)

PARENT_CLUSTER = 4
SUB_K = 3
N_INIT = 100
SEEDS = [42, 7, 123, 2026, 999, 55, 808, 1234, 31337, 64]
CONSENSUS_THRESHOLD = 0.8
# Three unambiguous anchors used only to identify WHICH sub-cluster is the core
# in each fit; they do not decide membership.
ANCHORS = ["Tottenham Court Road", "Oxford Circus", "Leicester Square"]

OUT = C.OUT / "c4_substructure"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    X_frame = pd.read_parquet(C.FEATURES / "X_fullweek_unpadded.parquet")
    X_frame.index = X_frame.index.astype(str)
    canon = pd.read_csv(C.CANON_K5_LABELS, dtype={"unit": str}).set_index("unit")["cluster"]
    coords = pd.read_csv(
        C.FYP / "data_processing" / "rail_allmodes" / "outputs" / "data"
        / "rail_allmodes_coords.csv", dtype={"unit": str},
    ).set_index("unit")
    metrics = pd.read_csv(C.RAIL_UNIT_METRICS, dtype={"NLC": str}).set_index("NLC")

    members = [u for u in X_frame.index if canon.get(u) == PARENT_CLUSTER]
    X = X_frame.loc[members].to_numpy(dtype=float)
    names = coords["Station"].reindex(members)
    anchors = [u for u in members if names[u] in ANCHORS]
    if len(anchors) != len(ANCHORS):
        raise RuntimeError(f"Expected {len(ANCHORS)} anchors in C4, found {len(anchors)}.")

    support = pd.Series(0.0, index=members)
    split_seeds = 0
    for seed in SEEDS:
        model = GaussianMixture(
            SUB_K, covariance_type=C.PRIMARY_COVARIANCE, n_init=N_INIT,
            reg_covar=C.REG_COVAR, max_iter=C.MAX_ITER, random_state=seed,
        ).fit(X)
        labels = pd.Series(model.predict(X), index=members)
        anchor_clusters = set(labels.reindex(anchors))
        if len(anchor_clusters) != 1:
            split_seeds += 1
            continue
        core = anchor_clusters.pop()
        support[labels == core] += 1
    usable = len(SEEDS) - split_seeds
    if usable == 0:
        raise RuntimeError("Anchors never co-clustered; the core is not identifiable.")
    support /= usable

    core_members = support.index[support >= CONSENSUS_THRESHOLD]
    print(f"C4 n={len(members)}; anchors co-clustered in {usable}/{len(SEEDS)} seeds")
    print(f"consensus core: n={len(core_members)} at threshold {CONSENSUS_THRESHOLD}")
    print(f"stations with partial support (0 < s < {CONSENSUS_THRESHOLD}): "
          f"{int(((support > 0) & (support < CONSENSUS_THRESHOLD)).sum())}")

    nested = canon.copy().astype(int).rename("cluster").to_frame()
    nested["cluster_nested"] = nested["cluster"]
    nested.loc[nested["cluster"] == PARENT_CLUSTER, "cluster_nested"] = 4
    nested.loc[core_members, "cluster_nested"] = 5
    nested["west_end_core"] = nested.index.isin(core_members)
    nested["core_seed_support"] = support.reindex(nested.index).fillna(0.0)
    nested.reset_index().rename(columns={"index": "unit"}).to_csv(
        OUT / "rail_allmodes_k5_nested_labels.csv", index=False
    )

    cols = ["direction_balance", "weekend_common_ratio",
            "night_tube_extension_share", "common_window_persistence", "total_activity"]
    rest = [u for u in members if u not in set(core_members)]
    table = pd.DataFrame(
        {
            f"C4a night-origin core (n={len(core_members)})": metrics.loc[core_members, cols].mean(),
            f"C4b remainder (n={len(rest)})": metrics.loc[rest, cols].mean(),
            "all 404 stations": metrics[cols].mean(),
        }
    ).T
    table.to_csv(OUT / "c4_split_metrics.csv")

    roster = pd.DataFrame(
        {
            "unit": core_members,
            "station": coords["Station"].reindex(core_members).to_numpy(),
            "mode": coords["mode_label"].reindex(core_members).to_numpy(),
            "direction_balance": metrics["direction_balance"].reindex(core_members).to_numpy(),
            "night_activity": metrics["total_activity"].reindex(core_members).to_numpy(),
            "seed_support": support.reindex(core_members).to_numpy(),
        }
    ).sort_values("direction_balance", ascending=False)
    roster.to_csv(OUT / "c4a_core_roster.csv", index=False)

    import geopandas as gpd

    base = gpd.read_file(C.FYP / "map" / "London_LSOA_2021_Boundaries.geojson").to_crs("EPSG:27700")
    frame = coords.loc[coords.index.intersection(X_frame.index),
                       ["Station", "is_lu", "easting", "northing"]].copy()
    frame["nested"] = nested["cluster_nested"].reindex(frame.index)
    frame = frame.dropna(subset=["easting", "nested"])
    palette = matplotlib.colormaps["tab10"].resampled(6)
    fig, ax = plt.subplots(figsize=(10.5, 10.5))
    base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
    labels_text = {0: "C0", 1: "C1", 2: "C2", 3: "C3",
                   4: "C4b remainder", 5: "C4a night-origin core"}
    for value in [0, 1, 2, 3, 4, 5]:
        subset = frame[frame["nested"] == value]
        if subset.empty:
            continue
        is_core = value == 5
        ax.scatter(
            subset.easting, subset.northing,
            s=110 if is_core else 30,
            marker="*" if is_core else "o",
            color=palette(int(value)),
            edgecolor="black" if is_core else "white",
            linewidth=0.8 if is_core else 0.4,
            zorder=6 if is_core else 3,
            label=f"{labels_text[value]} (n={len(subset)})",
        )
    ax.set_title(
        "Rail K=5 with the nested C4 split\n"
        f"C4a = {len(core_members)}-station night-origin core, consensus of "
        f"{usable}/{len(SEEDS)} seeds at sub-K={SUB_K}",
        fontsize=12,
    )
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT / "nested_c4_map.png", dpi=190, bbox_inches="tight")
    fig.savefig(OUT / "nested_c4_map.pdf", bbox_inches="tight")
    plt.close(fig)

    (OUT / "summary.json").write_text(
        json.dumps(
            {
                "parent_cluster": PARENT_CLUSTER, "parent_n": len(members),
                "sub_k": SUB_K, "n_init": N_INIT, "seeds": SEEDS,
                "anchors_coclustered_seeds": usable,
                "consensus_threshold": CONSENSUS_THRESHOLD,
                "core_n": int(len(core_members)),
                "nested_sizes": nested["cluster_nested"].value_counts().sort_index().to_dict(),
            },
            indent=2, default=int,
        ),
        encoding="utf-8",
    )
    print()
    print(roster.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
    print()
    print(table.to_string(float_format=lambda x: f"{x:,.3f}"))
    print()
    print("Saved to", OUT)


if __name__ == "__main__":
    main()
