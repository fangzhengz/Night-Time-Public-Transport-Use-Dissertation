# -*- coding: utf-8 -*-
"""The padded window as a ROBUSTNESS CHECK against the adopted native result.

Why this script exists separately from 02/04
--------------------------------------------
`02_run_clustering.py` fits every cell of the 2x2 at n_init=20, matching the
adopted pipeline's setting. On the PADDED matrix that turned out to be too few
restarts: n_init=20 lands on a local optimum whose BIC is 709.7 worse than the
one n_init=100 and n_init=300 both reach, and whose cluster structure looks
materially different (smallest cluster 19 vs 12). Every padded figure produced
by 04 is therefore a picture of an inferior solution and must not be used.

This script refits the padded matrix at n_init=100, verifies against n_init=300,
writes the labels separately from 02's, and renders the comparison that the
robustness claim actually rests on.

Cluster ids are arbitrary per fit, so the padded partition is relabelled onto
the adopted numbering by Hungarian matching on the contingency table BEFORE
plotting. Without that the two maps would differ only by a colour permutation
and would read as a large disagreement.
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
from scipy.optimize import linear_sum_assignment
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

warnings.filterwarnings("ignore", category=ConvergenceWarning)

VARIANT = "fullweek_padded"
K = 5
N_INIT = 100
VERIFY_N_INIT = 300
LSOA_GEOJSON = C.FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
OUT = C.OUT / VARIANT
FIGURES = OUT / "figures_robustness"
MOVED_COLOUR = "#D55E00"


def fit(X, n_init, seed=C.SEED):
    return GaussianMixture(
        n_components=K, covariance_type=C.PRIMARY_COVARIANCE, n_init=n_init,
        reg_covar=C.REG_COVAR, max_iter=C.MAX_ITER, random_state=seed,
    ).fit(X)


def align_to(reference: pd.Series, other: pd.Series) -> pd.Series:
    """Relabel `other` onto `reference`'s cluster numbering."""
    levels = sorted(reference.unique())
    contingency = pd.crosstab(other, reference).reindex(
        index=levels, columns=levels, fill_value=0
    )
    rows, columns = linear_sum_assignment(-contingency.to_numpy())
    mapping = {
        int(contingency.index[r]): int(contingency.columns[c])
        for r, c in zip(rows, columns)
    }
    return other.map(mapping)


def draw(ax, frame, base, column, title, palette, highlight=None):
    base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
    for cluster in sorted(frame[column].dropna().unique()):
        subset = frame[frame[column] == cluster]
        lu = subset[subset["is_lu"]]
        other = subset[~subset["is_lu"]]
        ax.scatter(lu.easting, lu.northing, s=34, marker="o", color=palette(int(cluster)),
                   edgecolor="white", linewidth=0.5,
                   label=f"C{int(cluster)} (n={len(subset)})", zorder=3)
        if len(other):
            ax.scatter(other.easting, other.northing, s=42, marker="^",
                       color=palette(int(cluster)), edgecolor="black",
                       linewidth=0.4, zorder=4)
    if highlight is not None and len(highlight):
        ax.scatter(highlight.easting, highlight.northing, s=150, marker="o",
                   facecolor="none", edgecolor=MOVED_COLOUR, linewidth=1.7, zorder=6,
                   label=f"changed cluster (n={len(highlight)})")
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()
    ax.legend(loc="lower right", fontsize=7.5, framealpha=0.9)
    ax.set_xlim(frame.easting.min() - 3000, frame.easting.max() + 3000)
    ax.set_ylim(frame.northing.min() - 3000, frame.northing.max() + 3000)


def main() -> None:
    import geopandas as gpd

    FIGURES.mkdir(parents=True, exist_ok=True)
    X_frame = pd.read_parquet(C.FEATURES / f"X_{VARIANT}.parquet")
    X_frame.index = X_frame.index.astype(str)
    X = X_frame.to_numpy(dtype=float)

    model = fit(X, N_INIT)
    padded = pd.Series(model.predict(X), index=X_frame.index, name="cluster")

    check = fit(X, VERIFY_N_INIT)
    verify_ari = adjusted_rand_score(padded, check.predict(X))
    if verify_ari < 0.999:
        raise RuntimeError(
            f"n_init={N_INIT} and {VERIFY_N_INIT} disagree (ARI {verify_ari:.4f}); "
            "the optimum is not converged, raise N_INIT before using these labels."
        )

    canon = pd.read_csv(C.CANON_K5_LABELS, dtype={"unit": str}).set_index("unit")["cluster"]
    shared = X_frame.index.intersection(canon.index)
    aligned = align_to(canon.loc[shared], padded.loc[shared])

    raw_ari = adjusted_rand_score(canon.loc[shared], padded.loc[shared])
    moved = shared[(aligned != canon.loc[shared]).to_numpy()]

    (OUT / "labels_robustness").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {"unit": shared, "cluster_raw": padded.loc[shared].to_numpy(),
         "cluster_aligned_to_canonical": aligned.to_numpy(),
         "canonical_cluster": canon.loc[shared].to_numpy(),
         "changed": (aligned != canon.loc[shared]).to_numpy()}
    ).to_csv(OUT / "labels_robustness" / f"k{K}_labels_ninit{N_INIT}.csv", index=False)

    coords = pd.read_csv(
        C.FYP / "data_processing" / "rail_allmodes" / "outputs" / "data"
        / "rail_allmodes_coords.csv", dtype={"unit": str},
    ).set_index("unit")
    frame = coords.loc[coords.index.intersection(shared),
                       ["Station", "mode_label", "is_lu", "easting", "northing"]].copy()
    frame["canonical"] = canon.reindex(frame.index)
    frame["padded"] = aligned.reindex(frame.index)
    frame = frame.dropna(subset=["easting", "canonical", "padded"])
    base = gpd.read_file(LSOA_GEOJSON).to_crs(C.CRS_BNG if hasattr(C, "CRS_BNG") else "EPSG:27700")
    palette = matplotlib.colormaps["tab10"].resampled(max(K, 3))
    highlight = frame.loc[frame.index.intersection(moved)]

    fig, axes = plt.subplots(1, 2, figsize=(17, 8.6))
    draw(axes[0], frame, base, "canonical",
         f"ADOPTED — native windows, 344 features, K={K}", palette)
    draw(axes[1], frame, base, "padded",
         f"ROBUSTNESS — all days padded to 18:00-05:00, 440 features, K={K}",
         palette, highlight=highlight)
    fig.suptitle(
        f"Rail K=5: adopted vs padded-window robustness check (both at the converged optimum)\n"
        f"ARI = {raw_ari:.4f} · {len(moved)} of {len(shared)} stations change cluster "
        f"({len(moved)/len(shared):.1%}) · cluster ids Hungarian-matched so colours correspond",
        fontsize=12, y=1.0,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "canonical_vs_padded_k5.png", dpi=190, bbox_inches="tight")
    fig.savefig(FIGURES / "canonical_vs_padded_k5.pdf", bbox_inches="tight")
    plt.close(fig)

    summary = {
        "variant": VARIANT, "K": K, "n_init": N_INIT,
        "verify_n_init": VERIFY_N_INIT, "verify_ari": verify_ari,
        "bic_n_init_100": float(model.bic(X)),
        "ari_vs_canonical": raw_ari,
        "n_stations": int(len(shared)),
        "n_changed": int(len(moved)),
        "share_changed": float(len(moved) / len(shared)),
        "canonical_sizes": canon.loc[shared].value_counts().sort_index().to_dict(),
        "padded_sizes": aligned.value_counts().sort_index().to_dict(),
    }
    (OUT / "labels_robustness" / "summary.json").write_text(
        json.dumps(summary, indent=2, default=int), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=int))
    print()
    print("changed stations:")
    for unit in moved:
        print(f"  {coords['Station'].get(unit, unit)[:34]:36s} "
              f"C{int(canon[unit])} -> C{int(aligned[unit])}")


if __name__ == "__main__":
    main()
