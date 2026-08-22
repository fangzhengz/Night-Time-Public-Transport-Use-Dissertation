# -*- coding: utf-8 -*-
"""Five-panel K-diagnostics figure matching the canonical house style.

Calinski-Harabasz was not in the sidecar's `kdiag.csv` -- the canonical
StopArea runner does not compute it either, it comes from the older
`cluster_clean_version_fullweek` figure set. It is recomputed here from the
saved feature matrix and saved labels, so no model is refitted and the labels
are exactly the ones every other sidecar output was built from.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import calinski_harabasz_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

HIGHLIGHT = "#C2185B"
LINE = "#4A148C"
GREEN = "#2E7D57"
RED = "#B23A2E"


def collect(variant: str) -> pd.DataFrame:
    X_frame = pd.read_parquet(C.FEATURES / f"X_{variant}.parquet")
    X_frame.index = pd.Index(X_frame.index.astype(str), name="lsoa")
    X = X_frame.to_numpy(dtype=float)

    kdiag = pd.read_csv(C.OUT / variant / "diagnostics" / "kdiag.csv")
    ch = []
    for k in kdiag["K"]:
        frame = pd.read_csv(
            C.OUT / variant / "labels" / f"k{int(k)}_labels.csv", dtype={"lsoa": str}
        ).set_index("lsoa")
        labels = frame.loc[X_frame.index, "cluster"].to_numpy(dtype=int)
        ch.append(float(calinski_harabasz_score(X, labels)))
    kdiag["calinski_harabasz"] = ch
    return kdiag


def panel(ax, kdiag, column, title, colour, highlight_k, lower_better=False, err=None):
    x = kdiag["K"].to_numpy()
    y = kdiag[column].to_numpy()
    if err is not None:
        e = kdiag[err].to_numpy()
        mask = np.isfinite(y)
        ax.errorbar(
            x[mask], y[mask], yerr=np.nan_to_num(e[mask]), marker="o", markersize=6,
            color=colour, capsize=3, linewidth=1.6,
        )
    else:
        ax.plot(x, y, marker="o", markersize=6, color=colour, linewidth=1.6)
    if highlight_k in set(x):
        value = float(y[list(x).index(highlight_k)])
        if np.isfinite(value):
            ax.scatter(
                [highlight_k], [value], s=190, facecolor="none",
                edgecolor=HIGHLIGHT, linewidth=2.2, zorder=5,
            )
            ax.annotate(
                f"K={highlight_k}\n{value:,.4g}",
                xy=(highlight_k, value), xytext=(6, 10),
                textcoords="offset points", fontsize=8.5,
                color=HIGHLIGHT, fontweight="bold",
            )
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("K")
    ax.set_xticks(list(x))
    ax.grid(alpha=0.18)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="daytype_raw_share", choices=sorted(C.VARIANTS))
    parser.add_argument("--highlight", type=int, default=4)
    args = parser.parse_args()

    kdiag = collect(args.variant)
    out = C.OUT / args.variant / "figures"
    out.mkdir(parents=True, exist_ok=True)
    kdiag.to_csv(C.OUT / args.variant / "diagnostics" / "kdiag_with_ch.csv", index=False)

    fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.2))
    panel(axes[0, 0], kdiag, "silhouette", "Silhouette (higher=better)", LINE, args.highlight)
    panel(axes[0, 1], kdiag, "calinski_harabasz", "Calinski-Harabasz (higher=better)", GREEN, args.highlight)
    panel(axes[0, 2], kdiag, "davies_bouldin", "Davies-Bouldin (lower=better)", RED, args.highlight)
    panel(axes[1, 0], kdiag, "BIC", "BIC (lower=better)", LINE, args.highlight)
    panel(
        axes[1, 1], kdiag, "bootstrap_ari_mean", "Bootstrap stability ARI (higher=better)",
        LINE, args.highlight, err="bootstrap_ari_sd",
    )
    panel(axes[1, 2], kdiag, "zero_bin_eta2", "Zero-bin eta² (lower=better)", "#8D6E63", args.highlight)

    spec = C.VARIANTS[args.variant]
    fig.suptitle(
        f"bus (StopArea allocation, DAY-TYPE closure, both directions >=36, "
        f"{spec['kind']}) - K-diagnostics\n"
        f"same {len(pd.read_parquet(C.FEATURES / f'X_{args.variant}.parquet')):,}-LSOA "
        f"sample, full-covariance reporting family ({args.variant}, GMM)",
        fontsize=13,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out / "k_diagnostics_panel.png", dpi=180, bbox_inches="tight")
    fig.savefig(out / "k_diagnostics_panel.pdf", bbox_inches="tight")
    plt.close(fig)

    columns = [
        "K", "BIC", "silhouette", "calinski_harabasz", "davies_bouldin",
        "bootstrap_ari_mean", "bootstrap_ari_sd", "bootstrap_min_cluster_jaccard_mean",
        "zero_bin_eta2", "activity_eta2", "timing_mean_eta2",
    ]
    print(kdiag[columns].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print()
    print("Saved:", out / "k_diagnostics_panel.png")


if __name__ == "__main__":
    main()
