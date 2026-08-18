# -*- coding: utf-8 -*-
"""Second-stage split of adopted rail C1 (central departure-dominant, night
origin, n=82): a nested sub-clustering that isolates a West End "night-origin
core" within it.

WHY A NESTED LABEL RATHER THAN A NEW TOP-LEVEL CLUSTERING
-----------------------------------------------------------
The core is a real structure -- its stations occupy the top of the network on
direction_balance and weekend_common_ratio -- but no single-stage GMM over all
404 stations isolates it reproducibly: at K=6 only 1 of 8 seeds finds it, at
K=7 only 2 of 10. It is 16 stations, 3.2% of 404, so absorbing it into a
neighbouring cluster costs the likelihood almost nothing and EM has no reason
to carve it out on its own.

After the 2026-08-07 Paddington correction, the top-level GMM partition was
refit and the former broad central-departure parent became C1. This runner
therefore resolves the parent from the current C1 label rather than reusing
the historical C2 id.

Splitting C1 in a documented second stage tests whether this group remains
separable without touching
the adopted five-cluster result: the primary K=5 typology (`cluster` column,
`rail_allmodes_k5_labels.csv`) is read-only here and never modified. This
folder only adds a nested label that downstream analysis can switch on or
off.

STATUS: this supersedes an earlier attempt (`rq1_rail_method_tests/
outputs/c4_substructure/`, now under `FYP/旧分析归档/`) that ran before the
2026-08-02 padded-window adoption and cluster renumbering, against the old
344-dim unpadded matrix with the old cluster id (4, not 2). That version's
core was n=13; this one, run against the currently adopted padded 440-dim
matrix and current C2 id, gives n=16.

CAVEAT TO CARRY: the core is 16 stations. That is ample for description and
for the narrative, but thin for catchment-based association tests -- an
800m catchment aggregate over 16 stations has wide uncertainty. Report
effect sizes for it descriptively; do not lean on significance.

OUTPUT SCHEMA (`rail_allmodes_k5_nested_labels.csv`)
  unit                 station NLC, matching rail_allmodes_k5_labels.csv
  cluster              adopted 0-4, copied through unchanged
  cluster_nested       0-4 as adopted; 5 = C1 night-origin core (West End)
  west_end_core        boolean convenience flag
  core_seed_support     fraction of seeds placing the station with the core
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.mixture import GaussianMixture

warnings.filterwarnings("ignore", category=ConvergenceWarning)

HERE = Path(__file__).resolve()
NUMBAT = HERE.parents[2]          # .../numbat_all_area_test
FYP = HERE.parents[3]             # .../FYP
OUT = HERE.parents[1] / "outputs"  # .../cluster_substructure/outputs
OUT.mkdir(parents=True, exist_ok=True)

CANON_X = NUMBAT / "outputs" / "data" / "X_rail_allmodes.parquet"
CANON_K5_LABELS = NUMBAT / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
RAIL_UNIT_METRICS = FYP / "rq2_new_clusters_analysis" / "outputs" / "data" / "rail_unit_metrics.csv"
COORDS = FYP / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"
LSOA_MAP = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

PARENT_CLUSTER = 1
NEW_CORE_ID = 5
SUB_K = 3
N_INIT = 100
COVARIANCE_TYPE = "diag"
REG_COVAR = 1e-6
MAX_ITER = 300
SEEDS = [42, 7, 123, 2026, 999, 55, 808, 1234, 31337, 64]
CONSENSUS_THRESHOLD = 0.8
ANCHORS = ["Tottenham Court Road", "Oxford Circus", "Leicester Square"]


def main() -> None:
    X_frame = pd.read_parquet(CANON_X)
    X_frame.index = X_frame.index.astype(str)
    canon = pd.read_csv(CANON_K5_LABELS, dtype={"unit": str}).set_index("unit")["cluster"]
    coords = pd.read_csv(COORDS, dtype={"unit": str}).set_index("unit")
    metrics = pd.read_csv(RAIL_UNIT_METRICS, dtype={"NLC": str}).set_index("NLC")

    members = [u for u in X_frame.index if canon.get(u) == PARENT_CLUSTER]
    X = X_frame.loc[members].to_numpy(dtype=float)
    names = coords["Station"].reindex(members)
    anchors = [u for u in members if names[u] in ANCHORS]
    if len(anchors) != len(ANCHORS):
        raise RuntimeError(f"Expected {len(ANCHORS)} anchors in current C1, found {len(anchors)}.")

    support = pd.Series(0.0, index=members)
    split_seeds = 0
    for seed in SEEDS:
        model = GaussianMixture(
            SUB_K, covariance_type=COVARIANCE_TYPE, n_init=N_INIT,
            reg_covar=REG_COVAR, max_iter=MAX_ITER, random_state=seed,
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
    print(f"C1 n={len(members)}; anchors co-clustered in {usable}/{len(SEEDS)} seeds")
    print(f"consensus core: n={len(core_members)} at threshold {CONSENSUS_THRESHOLD}")
    print(f"stations with partial support (0 < s < {CONSENSUS_THRESHOLD}): "
          f"{int(((support > 0) & (support < CONSENSUS_THRESHOLD)).sum())}")

    nested = canon.copy().astype(int).rename("cluster").to_frame()
    nested["cluster_nested"] = nested["cluster"]
    nested.loc[core_members, "cluster_nested"] = NEW_CORE_ID
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
            f"C1b night-origin core (n={len(core_members)})": metrics.loc[core_members, cols].mean(),
            f"C1a remainder (n={len(rest)})": metrics.loc[rest, cols].mean(),
            f"all {len(metrics)} stations": metrics[cols].mean(),
        }
    ).T
    table.to_csv(OUT / "c1_split_metrics.csv")

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
    roster.to_csv(OUT / "c1b_core_roster.csv", index=False)

    import geopandas as gpd

    base = gpd.read_file(LSOA_MAP).to_crs("EPSG:27700")
    frame = coords.loc[coords.index.intersection(X_frame.index),
                       ["Station", "is_lu", "easting", "northing"]].copy()
    frame["nested"] = nested["cluster_nested"].reindex(frame.index)
    frame = frame.dropna(subset=["easting", "nested"])
    palette = matplotlib.colormaps["tab10"].resampled(6)
    fig, ax = plt.subplots(figsize=(10.5, 10.5))
    base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
    labels_text = {0: "C0", 1: "C1a remainder", 2: "C2", 3: "C3", 4: "C4",
                   NEW_CORE_ID: "C1b night-origin core"}
    for value in [0, 1, 2, 3, 4, NEW_CORE_ID]:
        subset = frame[frame["nested"] == value]
        if subset.empty:
            continue
        is_core = value == NEW_CORE_ID
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
        "Rail K=5 (adopted) with the nested C1 split\n"
        f"C1b = {len(core_members)}-station night-origin core, consensus of "
        f"{usable}/{len(SEEDS)} seeds at sub-K={SUB_K}",
        fontsize=12,
    )
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT / "nested_c2_map.png", dpi=190, bbox_inches="tight")
    fig.savefig(OUT / "nested_c2_map.pdf", bbox_inches="tight")
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
                "feature_source": str(CANON_X),
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
