# -*- coding: utf-8 -*-
"""Exploratory second-stage screen of adopted bus C1 (high-flow,
night-persistent, n=1145, StopArea CLR K=4) -- the paper's headline cluster.

METHOD: same "screen every sub-K generically" protocol used for rail
(`numbat_all_area_test/cluster_substructure/03_c4_substructure.py`, itself
following the archived `rq1_rail_method_tests/08_substructure_screen.py`):
fit each candidate sub-K at 10 different seeds, take the mean pairwise ARI
across seed partitions as the stability score, and report the seed whose
partition agrees best with the other 9 (the consensus medoid) as the
representative split. No anchor stations are used -- unlike rail's West End
core, there is no known landmark LSOA group to target, so both/all
sub-clusters are characterised symmetrically.

FEATURE SPACE AND COVARIANCE: uses the exact adopted CLR feature matrix
(`X_bus_stoparea_clr_min36.parquet`, 72-dim: 2 directions x 3 day types x 12
hourly bins) and the adopted covariance family for that matrix, `full`
(picked by BIC over spherical/diag/tied at the parent K=4 level -- see
`outputs/clr/diagnostics/bic_grid.csv`). n=1145 vs p=72 here (n >> p),
unlike rail's 404 stations x 440 dims (n < p), so `full` covariance is far
better conditioned for this subset than it would be for rail.

n_init=100 per seed fit (not the parent pipeline's n_init=20) because the
open risk noted for the parent fit ("CLR BIC seed instability", see project
memory) is exactly the failure mode a stability check must not reproduce:
an under-optimised low-n_init fit would inflate apparent seed disagreement
with optimisation noise, not real instability.

STATUS: exploratory. This script only DESCRIBES -- it does not decide
whether a sub-K becomes an analytical variable, and emits no change to the
adopted `outputs/clr/labels/k4_labels.csv`.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
BUS_ROOT = HERE.parents[2]        # .../rq1_bus_stoparea_clustering
FYP = HERE.parents[3]             # .../FYP
OUT = HERE.parents[1] / "outputs"  # .../cluster_substructure/outputs
OUT.mkdir(parents=True, exist_ok=True)

CANON_X = BUS_ROOT / "outputs" / "features" / "X_bus_stoparea_clr_min36.parquet"
CANON_LABELS = BUS_ROOT / "outputs" / "clr" / "labels" / "k4_labels.csv"
SAMPLE_METRICS = BUS_ROOT / "outputs" / "features" / "sample_metrics.csv"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LSOA_LOOKUP = FYP / "IMDdata" / "ons_lsoa11_lsoa21_lad22_london_lookup.csv"

PARENT_CLUSTER = 1  # C1, high-flow night-persistent
SUB_KS = [2, 3]
N_INIT = 100
COVARIANCE_TYPE = "full"  # matches the adopted CLR K=4 winning family
REG_COVAR = 1e-6
MAX_ITER = 300
SEEDS = [42, 7, 123, 2026, 999, 55, 808, 1234, 31337, 64]
STABILITY_THRESHOLD = 0.90
CENTRE_BNG = (530034.0, 180381.0)  # Charing Cross, EPSG:27700 -- same anchor as rail

EXTERNAL = [
    "direction_balance", "post_midnight_share",
    "post_midnight_persistence", "weekend_ratio", "log_total_activity",
]


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = y.mean()
    total = float(((y - grand) ** 2).sum())
    if total <= 0:
        return float("nan")
    return float(
        sum(int((labels == c).sum()) * (y[labels == c].mean() - grand) ** 2
            for c in np.unique(labels)) / total
    )


def fit(X, k, seed):
    return GaussianMixture(
        k, covariance_type=COVARIANCE_TYPE, n_init=N_INIT,
        reg_covar=REG_COVAR, max_iter=MAX_ITER, random_state=seed,
    ).fit(X)


def consensus(X, members, k):
    labels = [pd.Series(fit(X, k, s).predict(X), index=members) for s in SEEDS]
    aris = np.zeros((len(SEEDS), len(SEEDS)))
    for i, j in combinations(range(len(SEEDS)), 2):
        value = adjusted_rand_score(labels[i], labels[j])
        aris[i, j] = aris[j, i] = value
    mean_pairwise = float(aris[np.triu_indices(len(SEEDS), 1)].mean())
    medoid = int(np.argmax(aris.sum(axis=1)))
    return labels[medoid], mean_pairwise


def main() -> None:
    X_frame = pd.read_parquet(CANON_X)
    X_frame.index = X_frame.index.astype(str)
    canon = pd.read_csv(CANON_LABELS, dtype={"lsoa": str}).set_index("lsoa")["cluster"]
    metrics = pd.read_csv(SAMPLE_METRICS, dtype={"lsoa": str}).set_index("lsoa")
    lookup = pd.read_csv(LSOA_LOOKUP, dtype=str).set_index("LSOA21CD")["LSOA21NM"]

    import geopandas as gpd

    boundaries = gpd.read_file(LSOA_GEOJSON)
    code_col = next(c for c in boundaries.columns if c.lower() == "lsoa21cd")
    boundaries = boundaries[[code_col, "geometry"]].rename(columns={code_col: "lsoa"}).set_index("lsoa")
    centroids_bng = boundaries.geometry.to_crs("EPSG:27700").centroid
    km_to_centre = pd.Series(
        np.hypot(centroids_bng.x - CENTRE_BNG[0], centroids_bng.y - CENTRE_BNG[1]) / 1000.0,
        index=boundaries.index,
    )

    members = [u for u in X_frame.index if canon.get(u) == PARENT_CLUSTER]
    X = X_frame.loc[members].to_numpy(dtype=float)
    print(f"C1 n={len(members)} (adopted CLR feature space, {COVARIANCE_TYPE} covariance)")

    screen_rows, roster_rows = [], []
    best_reproducible = None
    for k in SUB_KS:
        labels, stability = consensus(X, members, k)
        reproducible = stability >= STABILITY_THRESHOLD
        row = {"parent": "C1", "parent_n": len(members), "sub_k": k,
               "seed_ari_mean": stability, "reproducible": reproducible}
        for column in EXTERNAL:
            row[f"eta2_{column}"] = eta_squared(metrics[column].reindex(members), labels.to_numpy())
        row["eta2_km_to_centre"] = eta_squared(km_to_centre.reindex(members), labels.to_numpy())
        screen_rows.append(row)
        print(f"\nsub-K={k}: seed ARI mean = {stability:.3f} "
              f"({'REPRODUCIBLE' if reproducible else 'not reproducible'} at >= {STABILITY_THRESHOLD})")

        if reproducible:
            if best_reproducible is None or k > best_reproducible[0]:
                best_reproducible = (k, labels, stability)
            for sub in sorted(labels.unique()):
                part = labels.index[labels == sub]
                ordered = sorted(part, key=lambda u: -metrics["total_activity"].get(u, 0))
                entry = {
                    "sub_k": k, "sub": int(sub), "n": len(part),
                    "direction_balance": metrics["direction_balance"].reindex(part).mean(),
                    "post_midnight_share": metrics["post_midnight_share"].reindex(part).mean(),
                    "post_midnight_persistence": metrics["post_midnight_persistence"].reindex(part).mean(),
                    "weekend_ratio": metrics["weekend_ratio"].reindex(part).mean(),
                    "median_activity": metrics["total_activity"].reindex(part).median(),
                    "km_to_centre": km_to_centre.reindex(part).mean(),
                    "top_lsoas": ", ".join(f"{lookup.get(u, u)} ({u})" for u in ordered[:6]),
                }
                roster_rows.append(entry)
                print(f"  sub{sub}  n={len(part):4d}  dir_bal={entry['direction_balance']:+.3f}  "
                      f"post_mid={entry['post_midnight_share']:.3f}  persist={entry['post_midnight_persistence']:.3f}  "
                      f"wknd={entry['weekend_ratio']:.3f}  med_act={entry['median_activity']:>8,.0f}  "
                      f"km={entry['km_to_centre']:5.1f}")
                print(f"        {entry['top_lsoas']}")

    screen = pd.DataFrame(screen_rows)
    screen.to_csv(OUT / "c1_screen_table.csv", index=False)
    pd.DataFrame(roster_rows).to_csv(OUT / "c1_subcluster_rosters.csv", index=False)

    if best_reproducible is None:
        (OUT / "c1_summary.json").write_text(
            json.dumps({"parent_cluster": PARENT_CLUSTER, "parent_n": len(members),
                        "sub_ks_tested": SUB_KS, "any_reproducible": False,
                        "stability_threshold": STABILITY_THRESHOLD}, indent=2),
            encoding="utf-8",
        )
        print("\nNo reproducible split found at any tested sub-K. Stopping -- no labels/map emitted.")
        print("Saved to", OUT)
        return

    k, labels, stability = best_reproducible
    nested = canon.copy().rename("cluster").to_frame()
    nested["cluster_nested"] = nested["cluster"]
    base_new_id = 10  # clear of the adopted 0-3 and any future single-digit reservations
    for sub in sorted(labels.unique()):
        part = labels.index[labels == sub]
        nested.loc[part, "cluster_nested"] = base_new_id + int(sub)
    nested.reset_index().to_csv(OUT / "c1_nested_labels.csv", index=False)

    (OUT / "c1_summary.json").write_text(
        json.dumps(
            {"parent_cluster": PARENT_CLUSTER, "parent_n": len(members),
             "chosen_sub_k": k, "seed_ari_mean": stability,
             "stability_threshold": STABILITY_THRESHOLD,
             "nested_sizes": nested["cluster_nested"].value_counts().sort_index().to_dict(),
             "feature_source": str(CANON_X), "covariance": COVARIANCE_TYPE},
            indent=2, default=int,
        ),
        encoding="utf-8",
    )

    # `nested["cluster_nested"]` already carries every retained LSOA's status
    # (0/2/3 = other adopted clusters, -1 = excluded low-flow, 10+ = C1
    # sub-groups). Only LSOAs entirely outside the bus sample universe (not
    # in k4_labels.csv at all) are genuinely missing -- those are the true
    # "isna" grey background.
    frame = boundaries.copy()
    frame["nested"] = nested["cluster_nested"].reindex(frame.index)
    fig, ax = plt.subplots(figsize=(8, 8))
    background = frame[frame["nested"].isna() | (frame["nested"] < base_new_id)]
    if not background.empty:
        background.plot(ax=ax, color="#d9d9d9", linewidth=0.0)
    values = sorted(v for v in frame["nested"].dropna().unique() if v >= base_new_id)
    palette = matplotlib.colormaps["tab10"].resampled(max(len(values), 3))
    for i, value in enumerate(values):
        frame[frame["nested"] == value].plot(
            ax=ax, color=palette(i), linewidth=0.0,
            label=f"C1 sub{int(value) - base_new_id} (n={(frame['nested'] == value).sum()})",
        )
    ax.set_axis_off()
    ax.set_title(f"Bus StopArea CLR K=4 (adopted) -- nested C1 split at sub-K={k}\n"
                 f"seed ARI = {stability:.3f}  |  grey = other adopted clusters / excluded", fontsize=11)
    handles = [plt.Line2D([0], [0], marker="s", linestyle="", color=palette(i),
                           label=f"C1 sub{int(v) - base_new_id} (n={(frame['nested'] == v).sum()})")
               for i, v in enumerate(values)]
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "nested_c1_map.png", dpi=190, bbox_inches="tight")
    fig.savefig(OUT / "nested_c1_map.pdf", bbox_inches="tight")
    plt.close(fig)

    print("\nSaved to", OUT)


if __name__ == "__main__":
    main()
