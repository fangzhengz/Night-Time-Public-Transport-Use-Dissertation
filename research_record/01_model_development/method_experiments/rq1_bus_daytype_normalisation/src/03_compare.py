# -*- coding: utf-8 -*-
"""Compare the four day-type-closure variants against the adopted full-week runs.

`zero_bin_eta2` did not exist as a saved diagnostic in the canonical folder --
the 2026-07-23 finding was computed ad hoc. It is recomputed here for the
canonical labels using the SAME definition and the SAME zero-bin series as the
sidecar, so the two sides of the table are measured with one instrument.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = float(y.mean())
    total = float(np.square(y - grand).sum())
    if total <= 0:
        return float("nan")
    return float(
        sum(
            int((labels == cluster).sum())
            * (float(y[labels == cluster].mean()) - grand) ** 2
            for cluster in np.unique(labels)
        )
        / total
    )


def canonical_rows() -> pd.DataFrame:
    """Recompute the comparable diagnostics for the adopted full-week runs."""
    zeros = pd.read_csv(
        C.FEATURES / "zero_bin_share.csv", dtype={"lsoa": str}
    ).set_index("lsoa")["zero_bin_share"]
    metrics = pd.read_csv(C.SAMPLE_METRICS, dtype={"lsoa": str}).set_index("lsoa")

    rows: list[dict] = []
    for variant, folder in [("canon_raw_share", "raw_share"), ("canon_clr", "clr")]:
        kdiag_path = C.CANONICAL / "outputs" / folder / "diagnostics" / "kdiag.csv"
        kdiag = pd.read_csv(kdiag_path).set_index("K")
        geo_path = C.CANONICAL / "outputs" / folder / "data" / "central_outer_diagnostic.csv"
        geo = pd.read_csv(geo_path).set_index("K") if geo_path.exists() else None
        for k in C.CANDIDATE_KS:
            label_path = C.CANONICAL / "outputs" / folder / "labels" / f"k{k}_labels.csv"
            if not label_path.exists():
                continue
            frame = pd.read_csv(label_path, dtype={"lsoa": str}).set_index("lsoa")
            frame = frame[frame["cluster"] >= 0]
            labels = frame["cluster"].to_numpy(dtype=int)
            shared = frame.index
            row = {
                "variant": variant,
                "closure": "full-week",
                "K": k,
                "n": len(frame),
                "silhouette": float(kdiag.loc[k, "silhouette"]),
                "activity_eta2": float(kdiag.loc[k, "activity_eta2"]),
                "zero_bin_eta2": eta_squared(zeros.loc[shared], labels),
                "timing_mean_eta2": float(kdiag.loc[k, "timing_mean_eta2"]),
                "weekend_ratio_eta2": float(kdiag.loc[k, "weekend_ratio_eta2"]),
                "bootstrap_ari_mean": float(kdiag.loc[k, "bootstrap_ari_mean"]),
                "bootstrap_min_jaccard": float(
                    kdiag.loc[k, "bootstrap_min_cluster_jaccard_mean"]
                ),
                "central_outer_tv": (
                    float(geo.loc[k, "central_outer_total_variation"])
                    if geo is not None and k in geo.index else np.nan
                ),
                "ari_vs_canon_clr_k4": np.nan,
                "ari_vs_canon_raw_k3": np.nan,
            }
            rows.append(row)
    return pd.DataFrame(rows)


def sidecar_rows() -> pd.DataFrame:
    rows: list[dict] = []
    for variant in C.VARIANTS:
        root = C.OUT / variant
        kdiag = pd.read_csv(root / "diagnostics" / "kdiag.csv").set_index("K")
        geo_path = root / "data" / "central_outer_diagnostic.csv"
        geo = pd.read_csv(geo_path).set_index("K") if geo_path.exists() else None
        n = int(pd.read_parquet(C.FEATURES / f"X_{variant}.parquet").shape[0])
        for k in C.CANDIDATE_KS:
            rows.append(
                {
                    "variant": variant,
                    "closure": "day-type",
                    "K": k,
                    "n": n,
                    "silhouette": float(kdiag.loc[k, "silhouette"]),
                    "activity_eta2": float(kdiag.loc[k, "activity_eta2"]),
                    "zero_bin_eta2": float(kdiag.loc[k, "zero_bin_eta2"]),
                    "timing_mean_eta2": float(kdiag.loc[k, "timing_mean_eta2"]),
                    "weekend_ratio_eta2": float(kdiag.loc[k, "weekend_ratio_eta2"]),
                    "bootstrap_ari_mean": float(kdiag.loc[k, "bootstrap_ari_mean"]),
                    "bootstrap_min_jaccard": float(
                        kdiag.loc[k, "bootstrap_min_cluster_jaccard_mean"]
                    ),
                    "central_outer_tv": (
                        float(geo.loc[k, "central_outer_total_variation"])
                        if geo is not None and k in geo.index else np.nan
                    ),
                    "ari_vs_canon_clr_k4": float(kdiag.loc[k, "ari_vs_canon_clr_k4"]),
                    "ari_vs_canon_raw_k3": float(kdiag.loc[k, "ari_vs_canon_raw_k3"]),
                }
            )
    return pd.DataFrame(rows)


def bic_selection() -> pd.DataFrame:
    rows: list[dict] = []
    for variant in C.VARIANTS:
        grid = pd.read_csv(C.OUT / variant / "diagnostics" / "bic_grid.csv")
        best = grid.loc[grid["BIC"].idxmin()]
        family = grid[grid["covariance"] == best["covariance"]].set_index("K")["BIC"]
        ordered = family.sort_values()
        runner_k = int(ordered.index[1])
        rows.append(
            {
                "variant": variant,
                "bic_covariance": str(best["covariance"]),
                "bic_K": int(best["K"]),
                "bic_min_cluster_n": int(best["min_cluster_n"]),
                "runner_up_K": runner_k,
                "bic_margin_over_runner_up": float(ordered.iloc[1] - ordered.iloc[0]),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    table = pd.concat([canonical_rows(), sidecar_rows()], ignore_index=True)
    table.to_csv(C.COMPARISON / "variant_comparison.csv", index=False)
    selection = bic_selection()
    selection.to_csv(C.COMPARISON / "bic_selection.csv", index=False)

    display = table[
        [
            "variant", "closure", "K", "n", "silhouette", "activity_eta2",
            "zero_bin_eta2", "timing_mean_eta2", "weekend_ratio_eta2",
            "central_outer_tv", "bootstrap_ari_mean", "bootstrap_min_jaccard",
            "ari_vs_canon_raw_k3", "ari_vs_canon_clr_k4",
        ]
    ]

    report = [
        "# Day-type closure vs full-week closure: bus",
        "",
        "Sidecar result, 2026-08-01. Not an adopted result.",
        "",
        "## What differs between the two sides",
        "",
        "Only the denominator. Allocation (StopArea), window (18:00-06:00), "
        "granularity (hourly), retention (both direction week totals >= 36), GMM "
        "grid, seed, n_init and bootstrap protocol are identical. The strict "
        "variant additionally requires every one of the six (direction x day "
        "type) blocks to clear 36, which is the one place the sample changes.",
        "",
        "## BIC selection",
        "",
        selection.to_markdown(index=False, floatfmt=".1f"),
        "",
        "## Diagnostics at the candidate Ks",
        "",
        display.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Reading notes",
        "",
        "- `zero_bin_eta2` is the share of a unit's exactly-zero raw-cell "
        "fraction explained by the partition. High values mean the clusters are "
        "largely service-continuity tiers rather than shape types. Recomputed "
        "here for the canonical labels with the sidecar's own definition.",
        "- `weekend_ratio_eta2` is a VALIDITY indicator that flips meaning "
        "between the two sides. Under full-week closure weekend intensity is "
        "inside the feature vector, so a high value is partly circular. Under "
        "day-type closure it is external to the features, so it measures "
        "genuine external agreement.",
        "- `central_outer_tv` is total variation between the Westminster/Camden "
        "cluster distribution and the Kingston/Richmond one. Higher = the two "
        "geographies are better separated, which is Howard's objection.",
        "- ARI columns are computed on shared units only.",
    ]
    (C.COMPARISON / "COMPARISON.md").write_text("\n".join(report), encoding="utf-8")

    print(selection.to_string(index=False))
    print()
    print(display.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print()
    print("Saved:", C.COMPARISON / "COMPARISON.md")


if __name__ == "__main__":
    main()
