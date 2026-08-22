# -*- coding: utf-8 -*-
"""Second-stage screen of adopted rail C4 (inner/mid arrival-dominant,
Night-Tube served, n=166) -- the largest of the five clusters.

METHOD: same protocol as the archived `08_substructure_screen.py` (which
screened every level-one cluster generically), run specifically against the
CURRENTLY adopted padded 440-dim matrix and current C4 id. That screen was
run pre-relabel/pre-padding (old id C3, n=163, on the 344-dim unpadded
matrix) and found sub-K=2 reproducible (seed ARI 1.000) but sub-K=3 not
(0.494). This script re-checks that finding against the current data rather
than assuming it survived the relabel (16/404 stations, 4.0%, changed
cluster during that relabel -- old C3 gained 3 net members becoming new C4).

STABILITY: mean pairwise ARI across 10 seed fits at each sub-K, using a
consensus medoid (the seed whose partition agrees best with the other 9) as
the reported partition -- an actual realisable fit, not an average. Called
reproducible at seed_ari_mean >= STABILITY_THRESHOLD.

This script only DESCRIBES: it does not decide whether a sub-K becomes an
analytical variable. If reproducible, membership + characterisation + a map
are saved so that decision can be made from real numbers.
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
NUMBAT = HERE.parents[2]
FYP = HERE.parents[3]
OUT = HERE.parents[1] / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

CANON_X = NUMBAT / "outputs" / "data" / "X_rail_allmodes.parquet"
CANON_K5_LABELS = NUMBAT / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
RAIL_UNIT_METRICS = FYP / "rq2_new_clusters_analysis" / "outputs" / "data" / "rail_unit_metrics.csv"
COORDS = FYP / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"
LSOA_MAP = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

PARENT_CLUSTER = 4
SUB_KS = [2, 3]
N_INIT = 100
COVARIANCE_TYPE = "diag"
REG_COVAR = 1e-6
MAX_ITER = 300
SEEDS = [42, 7, 123, 2026, 999, 55, 808, 1234, 31337, 64]
STABILITY_THRESHOLD = 0.90
CENTRE = (530034.0, 180381.0)

EXTERNAL = {
    "dir_balance": "direction_balance",
    "nt_extension": "night_tube_extension_share",
    "weekend": "weekend_common_ratio",
    "log_activity": "log_total_activity",
}


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
    canon = pd.read_csv(CANON_K5_LABELS, dtype={"unit": str}).set_index("unit")["cluster"]
    metrics = pd.read_csv(RAIL_UNIT_METRICS, dtype={"NLC": str}).set_index("NLC")
    coords = pd.read_csv(COORDS, dtype={"unit": str}).set_index("unit")
    km = pd.Series(
        np.hypot(coords["easting"] - CENTRE[0], coords["northing"] - CENTRE[1]) / 1000.0,
        index=coords.index,
    )

    members = [u for u in X_frame.index if canon.get(u) == PARENT_CLUSTER]
    X = X_frame.loc[members].to_numpy(dtype=float)
    print(f"C4 n={len(members)} (current adopted padded matrix)")

    screen_rows, roster_rows = [], []
    best_reproducible = None  # (k, labels, stability)
    for k in SUB_KS:
        labels, stability = consensus(X, members, k)
        reproducible = stability >= STABILITY_THRESHOLD
        row = {"parent": "C4", "parent_n": len(members), "sub_k": k,
               "seed_ari_mean": stability, "reproducible": reproducible}
        for short, column in EXTERNAL.items():
            row[f"eta2_{short}"] = eta_squared(metrics[column].reindex(members), labels.to_numpy())
        row["eta2_km_to_centre"] = eta_squared(km.reindex(members), labels.to_numpy())
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
                    "dir_balance": metrics["direction_balance"].reindex(part).mean(),
                    "nt_extension": metrics["night_tube_extension_share"].reindex(part).mean(),
                    "weekend": metrics["weekend_common_ratio"].reindex(part).mean(),
                    "median_activity": metrics["total_activity"].reindex(part).median(),
                    "km_to_centre": km.reindex(part).mean(),
                    "pct_LU": 100 * coords["is_lu"].reindex(part).mean(),
                    "top_stations": ", ".join(str(coords["Station"].get(u, u)) for u in ordered[:6]),
                }
                roster_rows.append(entry)
                print(f"  sub{sub}  n={len(part):3d}  dir_bal={entry['dir_balance']:+.3f}  "
                      f"nt_ext={entry['nt_extension']:.3f}  wknd={entry['weekend']:.3f}  "
                      f"med_act={entry['median_activity']:>9,.0f}  km={entry['km_to_centre']:5.1f}  "
                      f"LU={entry['pct_LU']:5.1f}%")
                print(f"        {entry['top_stations']}")

    screen = pd.DataFrame(screen_rows)
    screen.to_csv(OUT / "c4_screen_table.csv", index=False)
    pd.DataFrame(roster_rows).to_csv(OUT / "c4_subcluster_rosters.csv", index=False)

    if best_reproducible is None:
        (OUT / "c4_summary.json").write_text(
            json.dumps({"parent_cluster": PARENT_CLUSTER, "parent_n": len(members),
                        "sub_ks_tested": SUB_KS, "any_reproducible": False,
                        "stability_threshold": STABILITY_THRESHOLD}, indent=2),
            encoding="utf-8",
        )
        print("\nNo reproducible split found at any tested sub-K. Stopping -- no labels/map emitted.")
        print("Saved to", OUT)
        return

    k, labels, stability = best_reproducible
    nested = canon.copy().astype(int).rename("cluster").to_frame()
    nested["cluster_nested"] = nested["cluster"]
    base_new_id = 7  # 5 is taken by C2's core in the sibling nested-labels file
    for sub in sorted(labels.unique()):
        part = labels.index[labels == sub]
        nested.loc[part, "cluster_nested"] = base_new_id + int(sub)
    nested.reset_index().rename(columns={"index": "unit"}).to_csv(
        OUT / "c4_nested_labels.csv", index=False
    )

    (OUT / "c4_summary.json").write_text(
        json.dumps(
            {"parent_cluster": PARENT_CLUSTER, "parent_n": len(members),
             "chosen_sub_k": k, "seed_ari_mean": stability,
             "stability_threshold": STABILITY_THRESHOLD,
             "nested_sizes": nested["cluster_nested"].value_counts().sort_index().to_dict(),
             "feature_source": str(CANON_X)},
            indent=2, default=int,
        ),
        encoding="utf-8",
    )

    import geopandas as gpd

    base = gpd.read_file(LSOA_MAP).to_crs("EPSG:27700")
    frame = coords.loc[coords.index.intersection(X_frame.index),
                       ["Station", "is_lu", "easting", "northing"]].copy()
    frame["nested"] = nested["cluster_nested"].reindex(frame.index)
    frame = frame.dropna(subset=["easting", "nested"])
    values = sorted(frame["nested"].unique())
    palette = matplotlib.colormaps["tab10"].resampled(max(len(values), 3))
    fig, ax = plt.subplots(figsize=(10.5, 10.5))
    base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
    for i, value in enumerate(values):
        subset = frame[frame["nested"] == value]
        is_split = value >= base_new_id
        label = f"C4 sub{int(value) - base_new_id}" if is_split else f"C{int(value)}"
        ax.scatter(
            subset.easting, subset.northing, s=45 if is_split else 22,
            marker="^" if is_split else "o", color=palette(i),
            edgecolor="black" if is_split else "white",
            linewidth=0.6, zorder=5 if is_split else 3,
            label=f"{label} (n={len(subset)})",
        )
    ax.set_title(f"Rail K=5 (adopted) with the nested C4 split at sub-K={k}\n"
                 f"seed ARI = {stability:.3f}", fontsize=12)
    ax.legend(loc="lower right", fontsize=8)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT / "nested_c4_map.png", dpi=190, bbox_inches="tight")
    fig.savefig(OUT / "nested_c4_map.pdf", bbox_inches="tight")
    plt.close(fig)

    print("\nSaved to", OUT)


if __name__ == "__main__":
    main()
