# -*- coding: utf-8 -*-
"""Cross-variant diagnostic figures for the rail 2x2.

Encoding is chosen so the 2x2 reads off the page without a lookup table:

    hue      = closure   (purple = full-week, green = day-type)
    linestyle= window    (solid = native 344, dashed = padded 440)

so a vertical gap between colours is the closure effect and a gap between line
styles within a colour is the padding effect. Every figure keeps that mapping.

BIC IS NOT COMPARED ACROSS VARIANTS. The four feature matrices live in
different spaces (different closure, different dimensionality), so their
absolute BIC values are not commensurable -- only the SHAPE of each curve and
the location of its own minimum mean anything. Each BIC panel is therefore
drawn on its own axis and centred on its own minimum, never overlaid.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

PURPLE, GREEN, GREY = "#500778", "#2F6B4F", "#9A9A9A"
FIGURES = C.OUT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

STYLE = {
    "fullweek_unpadded": {"color": PURPLE, "ls": "-", "label": "full-week, native (adopted)"},
    "fullweek_padded": {"color": PURPLE, "ls": "--", "label": "full-week, padded"},
    "daytype_unpadded": {"color": GREEN, "ls": "-", "label": "day-type, native"},
    "daytype_padded": {"color": GREEN, "ls": "--", "label": "day-type, padded"},
}
ORDER = ["fullweek_unpadded", "fullweek_padded", "daytype_unpadded", "daytype_padded"]


def load_kdiag() -> dict[str, pd.DataFrame]:
    return {
        variant: pd.read_csv(C.OUT / variant / "diagnostics" / "kdiag.csv")
        for variant in ORDER
    }


def load_grid() -> dict[str, pd.DataFrame]:
    return {
        variant: pd.read_csv(C.OUT / variant / "diagnostics" / "bic_grid.csv")
        for variant in ORDER
    }


def figure_bic(grids) -> None:
    """One panel per variant, each on its own scale, minimum marked."""
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.6))
    for axis, variant in zip(axes.flat, ORDER):
        grid = grids[variant]
        for covariance, colour, marker in [
            (C.PRIMARY_COVARIANCE, STYLE[variant]["color"], "o"),
            ("full", GREY, "s"),
        ]:
            sub = grid[grid["covariance"] == covariance].dropna(subset=["BIC"])
            if sub.empty:
                continue
            axis.plot(sub["K"], sub["BIC"] / 1000, marker=marker, ms=3.5, lw=1.3,
                      color=colour, ls=STYLE[variant]["ls"], label=covariance)
        diag = grid[grid["covariance"] == C.PRIMARY_COVARIANCE].dropna(subset=["BIC"])
        best = diag.loc[diag["BIC"].idxmin()]
        axis.axvline(best["K"], color=STYLE[variant]["color"], lw=0.8, ls=":")
        axis.annotate(
            f"diag min K={int(best['K'])}",
            xy=(best["K"], best["BIC"] / 1000),
            xytext=(4, 8), textcoords="offset points",
            fontsize=8, color=STYLE[variant]["color"], fontweight="bold",
        )
        axis.set_title(STYLE[variant]["label"], fontsize=10)
        axis.set_xlabel("K")
        axis.set_ylabel("BIC (thousands)")
        axis.set_xticks(C.K_RANGE)
        axis.grid(color="#eee")
        axis.spines[["top", "right"]].set_visible(False)
        axis.legend(fontsize=8, frameon=False)
    fig.suptitle(
        "Rail 2x2 — BIC over K, each variant on its own scale\n"
        "absolute BIC is NOT comparable between panels (different feature spaces); "
        "only curve shape and the location of each minimum are",
        fontsize=11, y=1.0,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "01_bic_grid_2x2.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGURES / "01_bic_grid_2x2.pdf", bbox_inches="tight")
    plt.close(fig)


def figure_kdiag(kdiags) -> None:
    panels = [
        ("silhouette", "Silhouette (higher = better separated)", None),
        ("activity_eta2", "activity eta² (volume domination)", None),
        ("zero_bin_eta2", "zero-bin eta² (service-continuity domination)", None),
        ("night_tube_extension_share_eta2", "night-tube extension eta² (the night signal)", None),
        ("timing_mean_eta2", "timing mean eta²", None),
        ("min_cluster_n", "smallest cluster size (n)", None),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for axis, (column, title, _) in zip(axes.flat, panels):
        for variant in ORDER:
            frame = kdiags[variant]
            axis.plot(frame["K"], frame[column], marker="o", ms=3.2, lw=1.4,
                      color=STYLE[variant]["color"], ls=STYLE[variant]["ls"],
                      label=STYLE[variant]["label"])
        axis.axvline(5, color="#cccccc", lw=0.8, zorder=0)
        axis.set_title(title, fontsize=9.5)
        axis.set_xlabel("K")
        axis.set_xticks(C.K_RANGE)
        axis.grid(color="#eee")
        axis.spines[["top", "right"]].set_visible(False)
    axes.flat[0].legend(fontsize=7.5, frameon=False, loc="upper right")
    fig.suptitle(
        "Rail 2x2 — K diagnostics (diag GMM). Purple = full-week closure, green = day-type; "
        "solid = native window, dashed = padded.\n"
        "Colour gaps are the closure effect; line-style gaps within a colour are the padding effect.",
        fontsize=11, y=1.01,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "02_k_diagnostics_2x2.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGURES / "02_k_diagnostics_2x2.pdf", bbox_inches="tight")
    plt.close(fig)


def figure_stability(kdiags) -> None:
    panels = [
        ("seed_ari_mean", "Random-seed ARI (20 refits, n_init=20)"),
        ("bootstrap_ari_mean", "Bootstrap ARI (20 replicates)"),
        ("bootstrap_min_jaccard_mean", "Weakest matched cluster (min Jaccard)"),
        ("ari_vs_canon_k5", "ARI against the adopted K=5 labels"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.1))
    width = 0.2
    for axis, (column, title) in zip(axes, panels):
        frame_ks = kdiags[ORDER[0]]["K"]
        candidates = [k for k in C.CANDIDATE_KS if k in set(frame_ks)]
        positions = np.arange(len(candidates))
        for offset, variant in enumerate(ORDER):
            frame = kdiags[variant].set_index("K")
            values = [frame.loc[k, column] if k in frame.index else np.nan for k in candidates]
            axis.bar(
                positions + (offset - 1.5) * width, values, width,
                color=STYLE[variant]["color"],
                alpha=1.0 if STYLE[variant]["ls"] == "-" else 0.45,
                edgecolor="white", linewidth=0.6, label=STYLE[variant]["label"],
            )
        axis.set_xticks(positions, [f"K={k}" for k in candidates])
        axis.set_title(title, fontsize=9.5)
        axis.grid(axis="y", color="#eee")
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_ylim(0, 1.0)
    axes[0].legend(fontsize=7.5, frameon=False, loc="lower left")
    fig.suptitle(
        "Rail 2x2 — stability. Solid fill = native window, faded = padded. "
        "The adopted run's own numbers (seed ARI 0.894 at K=5, 0.703 at K=7) are "
        "reproduced by the purple solid bars.",
        fontsize=11, y=1.03,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "03_stability_2x2.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGURES / "03_stability_2x2.pdf", bbox_inches="tight")
    plt.close(fig)


def figure_coupling(kdiags) -> None:
    """The interpretive crux: night-tube signal vs zero-structure.

    Day-type closure raises both. If the points move up the 1:1 diagonal the
    'night signal' gain is just the zero structure renamed; if they move above
    it, the partition is picking up more night behaviour than zero pattern.
    """
    fig, axis = plt.subplots(figsize=(7.2, 6.6))
    for variant in ORDER:
        frame = kdiags[variant]
        axis.plot(
            frame["zero_bin_eta2"], frame["night_tube_extension_share_eta2"],
            marker="o", ms=4, lw=1.1, color=STYLE[variant]["color"],
            ls=STYLE[variant]["ls"], label=STYLE[variant]["label"], alpha=0.85,
        )
        for _, row in frame[frame["K"].isin([5, 9])].iterrows():
            axis.annotate(
                f"K={int(row['K'])}",
                xy=(row["zero_bin_eta2"], row["night_tube_extension_share_eta2"]),
                xytext=(5, -3), textcoords="offset points", fontsize=7.5,
                color=STYLE[variant]["color"],
            )
    limit = 0.8
    axis.plot([0, limit], [0, limit], color="#cccccc", lw=1.0, ls=":")
    axis.annotate("1:1 — gain is the zero structure renamed", xy=(0.52, 0.52),
                  fontsize=7.5, color="#999999", rotation=38)
    axis.set_xlabel("zero-bin eta²  (how much of the partition is service continuity)")
    axis.set_ylabel("night-tube extension eta²  (how much is the night signal)")
    axis.set_title(
        "Rail — is the night signal real, or the zero structure renamed?\n"
        "points above the diagonal mean the partition explains night behaviour\n"
        "better than it explains which stations simply have late service",
        fontsize=10,
    )
    axis.grid(color="#eee")
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES / "04_night_signal_vs_zero_structure.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGURES / "04_night_signal_vs_zero_structure.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    kdiags = load_kdiag()
    grids = load_grid()
    figure_bic(grids)
    figure_kdiag(kdiags)
    figure_stability(kdiags)
    figure_coupling(kdiags)

    # The coupling ratio is the number the figure exists to deliver, so write
    # it out rather than leaving it to be eyeballed off the plot.
    rows = []
    for variant in ORDER:
        frame = kdiags[variant].set_index("K")
        for k in [5, 9]:
            if k not in frame.index:
                continue
            night = float(frame.loc[k, "night_tube_extension_share_eta2"])
            zero = float(frame.loc[k, "zero_bin_eta2"])
            rows.append(
                {
                    "variant": variant, "K": k,
                    "night_tube_eta2": night, "zero_bin_eta2": zero,
                    "ratio_night_over_zero": night / zero if zero > 0 else np.nan,
                }
            )
    ratios = pd.DataFrame(rows)
    ratios.to_csv(C.COMPARISON / "night_signal_vs_zero_structure.csv", index=False)
    print(ratios.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print()
    for name in sorted(p.name for p in FIGURES.glob("*.png")):
        print("  ", name)


if __name__ == "__main__":
    main()
