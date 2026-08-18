# -*- coding: utf-8 -*-
"""Decompose the rail 2x2 into a closure effect and a padding effect.

A flat four-row table invites reading the best row as the winner. The point of
a 2x2 is that each factor gets isolated, so this script reports the two main
effects separately and holds the other factor fixed while doing it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

REPORT_METRICS = [
    "silhouette", "activity_eta2", "zero_bin_eta2", "timing_mean_eta2",
    "night_tube_extension_share_eta2", "weekend_common_ratio_eta2",
    "min_cluster_n", "seed_ari_mean", "bootstrap_ari_mean", "ari_vs_canon_k5",
]


def load_all() -> pd.DataFrame:
    frames = []
    for variant, spec in C.VARIANTS.items():
        frame = pd.read_csv(C.OUT / variant / "diagnostics" / "kdiag.csv")
        frame.insert(0, "variant", variant)
        frame.insert(1, "closure", spec["closure"])
        frame.insert(2, "window", "padded" if spec["padded"] else "native")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def bic_curves() -> pd.DataFrame:
    rows = []
    for variant in C.VARIANTS:
        grid = pd.read_csv(C.OUT / variant / "diagnostics" / "bic_grid.csv")
        diag = grid[grid["covariance"] == C.PRIMARY_COVARIANCE].dropna(subset=["BIC"])
        series = diag.set_index("K")["BIC"]
        ordered = series.sort_values()
        rows.append(
            {
                "variant": variant,
                "bic_best_K": int(ordered.index[0]),
                "runner_up_K": int(ordered.index[1]),
                "margin_over_runner_up": float(ordered.iloc[1] - ordered.iloc[0]),
                # A well-identified K sits in a trough. If the best five Ks are
                # within a hair of each other the criterion is not selecting.
                "spread_of_best_5": float(ordered.iloc[4] - ordered.iloc[0]),
            }
        )
    return pd.DataFrame(rows)


def effect(table: pd.DataFrame, factor: str, held: str, held_value: str, k: int):
    """Difference in each metric when `factor` flips, with `held` fixed."""
    sub = table[(table["K"] == k) & (table[held] == held_value)].set_index(factor)
    levels = list(sub.index)
    if len(levels) != 2:
        return None
    baseline, alternative = levels[0], levels[1]
    out = pd.DataFrame(
        {
            baseline: sub.loc[baseline, REPORT_METRICS],
            alternative: sub.loc[alternative, REPORT_METRICS],
        }
    )
    out["delta"] = out[alternative] - out[baseline]
    return out


def main() -> None:
    table = load_all()
    table.to_csv(C.COMPARISON / "rail_2x2_kdiag.csv", index=False)
    curves = bic_curves()
    curves.to_csv(C.COMPARISON / "bic_selection.csv", index=False)

    display = table[table["K"].isin([4, 5, 6, 7, 9])][
        ["variant", "closure", "window", "K", "BIC"] + REPORT_METRICS
    ]

    sections = [
        "# Rail: day-type vs full-week closure, native vs padded window",
        "",
        "Sidecar result, 2026-08-01. Not an adopted result.",
        "",
        "## Anchor",
        "",
        "`fullweek_unpadded` reproduces the adopted matrix exactly (max abs diff "
        "0.0 in 01) and reproduces its labels at K=5 (`ari_vs_canon_k5` = 1.000) "
        "and its stability numbers (seed ARI 0.894 at K=5, 0.703 at K=7, 0.624 "
        "at K=6). The 2x2 therefore measures against the real pipeline.",
        "",
        "## BIC behaviour",
        "",
        curves.to_markdown(index=False, floatfmt=".1f"),
        "",
        "`spread_of_best_5` is the BIC gap between the best and fifth-best K. A "
        "small spread means BIC has stopped discriminating and K cannot be read "
        "off it -- Clara's standing caveat that BIC must not auto-pick K.",
        "",
        "## Full diagnostics",
        "",
        display.to_markdown(index=False, floatfmt=".4f"),
        "",
    ]

    for k in [5, 9]:
        for window in ["native", "padded"]:
            block = effect(table, "closure", "window", window, k)
            if block is not None:
                sections += [
                    f"## Closure effect at K={k}, window held at {window}",
                    "", block.to_markdown(floatfmt=".4f"), "",
                ]
    for k in [5, 9]:
        for closure in ["fullweek", "daytype"]:
            block = effect(table, "window", "closure", closure, k)
            if block is not None:
                sections += [
                    f"## Padding effect at K={k}, closure held at {closure}",
                    "", block.to_markdown(floatfmt=".4f"), "",
                ]

    (C.COMPARISON / "COMPARISON.md").write_text("\n".join(sections), encoding="utf-8")
    print(curves.to_string(index=False))
    print()
    for k in [5]:
        for window in ["native", "padded"]:
            print(f"--- closure effect at K={k}, window={window} ---")
            print(effect(table, "closure", "window", window, k).to_string(
                float_format=lambda x: f"{x:.4f}"))
            print()
        for closure in ["fullweek", "daytype"]:
            print(f"--- padding effect at K={k}, closure={closure} ---")
            print(effect(table, "window", "closure", closure, k).to_string(
                float_format=lambda x: f"{x:.4f}"))
            print()
    print("Saved:", C.COMPARISON / "COMPARISON.md")


if __name__ == "__main__":
    main()
