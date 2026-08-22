"""K-diagnostics figure for the literature mean->=1/hour threshold (36),
matching the style of 02_bottom20_excluded_bic.py's
`bottom20_excluded_k_diagnostics.png` panel so the two thresholds are
visually comparable, as 05_bottom20_cluster_homogeneity.py's docstring
already anticipated but this side never got.

Read-only: 01_threshold_screen.py already computed and saved the K=2..12
scan (full covariance, low n_init, threshold=36 fixed) to
outputs/data/threshold_k_scan_literature_mean1ph.csv, and the K=3
confirmatory full-n_init deepdive to
outputs/data/threshold_k_deepdive_literature_mean1ph.csv. Nothing is refit
here -- this script only plots what is already on disk.

bottom20_excluded's panel 2 (bootstrap ARI / min-cluster Jaccard) has no
equivalent here because 01_threshold_screen.py never ran a bootstrap for
this threshold; panel 2 here uses min_cluster_pct vs K instead, which the
scan already computed and is a relevant window into how degenerate the
solution gets at higher K.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DATA = ROOT / "outputs" / "data"
FIGURES = ROOT / "outputs" / "figures"


def log(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    scan = pd.read_csv(DATA / "threshold_k_scan_literature_mean1ph.csv")
    scan = scan.sort_values("k")
    deepdive = pd.read_csv(DATA / "threshold_k_deepdive_literature_mean1ph.csv")
    best_k = int(deepdive.loc[deepdive["is_bic_best_k"], "k"].iloc[0])

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), constrained_layout=True)

    axes[0].plot(scan["k"], scan["bic_within_threshold"], marker="o", color="#500778")
    axes[0].axvline(best_k, color="#9A3D3D", ls="--", lw=1, label=f"BIC-best K={best_k} (deepdive-confirmed)")
    axes[0].set_title("BIC within threshold=36 (lower=better)")
    axes[0].legend(fontsize=8)

    axes[1].plot(scan["k"], scan["activity_eta2"], marker="o", label="activity eta2")
    axes[1].plot(scan["k"], scan["timing_mean_eta2"], marker="s", label="timing mean eta2")
    axes[1].axvline(best_k, color="#9A3D3D", ls="--", lw=1)
    axes[1].set_title("Activity vs timing eta2")
    axes[1].legend(fontsize=8)

    axes[2].plot(scan["k"], scan["min_cluster_pct"], marker="o", color="#2F6B4F")
    axes[2].axvline(best_k, color="#9A3D3D", ls="--", lw=1)
    axes[2].set_title("Smallest cluster, % of core (higher=less degenerate)")

    for ax in axes:
        ax.set_xlabel("K")
        ax.grid(alpha=0.25)

    fig.suptitle(
        "Literature mean>=1/hour threshold (min(boardings,alightings)>=36) — K-diagnostics\n"
        f"n_core={int(scan['n_core'].iloc[0]):,} ({scan['pct_core'].iloc[0]:.2f}% retained), full covariance, exploratory scan (low n_init) + deepdive at K={best_k}",
        fontsize=12,
    )
    out = FIGURES / "literature_mean1ph_k_diagnostics.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    log(f"wrote {out}")


if __name__ == "__main__":
    main()
