"""Validates the reliable-core reclustering at a chosen K: geographic and
activity eta^2, profile-metric eta^2 breakdown, and a side-by-side
comparison against the originally adopted MIN_TOTAL=1 K=3 solution.

Run after 03_recluster_reliable_core.py. Pick K from
`outputs/data/reliable_core_kdiag.csv` (interpretability + bootstrap
stability, same trade-off logic already used for the adopted rail/bus
solutions) and pass it with --k.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

sys.path.insert(0, str(FYP / "rq1_bus_geography_diagnostic" / "src"))
from run_geography_diagnostic import load_lsoa_coords, eta_squared_oneway  # noqa: E402

UNIT_METRICS = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"
LABELS = ROOT / "outputs" / "labels"
DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"

PROFILE_METRICS = [
    "log_total_activity",
    "direction_balance",
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
    "weekend_ratio",
]


def eta2_table(merged: pd.DataFrame, cluster_col: str) -> dict:
    coords_cols = {"distance_to_centre": eta_squared_oneway(merged["distance_to_centre"], merged[cluster_col])}
    for metric in PROFILE_METRICS:
        coords_cols[metric] = eta_squared_oneway(merged[metric], merged[cluster_col])
    return coords_cols


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, required=True, help="Reliable-core K to validate")
    args = parser.parse_args()

    coords = load_lsoa_coords()
    metrics_full = pd.read_csv(UNIT_METRICS)
    metrics_full["lsoa"] = metrics_full["lsoa"].astype(str)

    # New reliable-core solution
    new_labels = pd.read_csv(LABELS / f"reliable_core_k{args.k}_labels.csv").rename(columns={"unit": "lsoa"})
    new_labels["lsoa"] = new_labels["lsoa"].astype(str)
    new_metrics = metrics_full.drop(columns=["cluster", "max_posterior", "entropy"])
    new_merged = new_labels.merge(new_metrics, on="lsoa", how="inner").merge(coords, on="lsoa", how="inner")
    new_eta2 = eta2_table(new_merged, "cluster")
    new_sizes = new_merged["cluster"].value_counts().sort_index().to_dict()

    # Original adopted solution (MIN_TOTAL=1, K=3, full covariance), for comparison
    old_merged = metrics_full.merge(coords, on="lsoa", how="inner")
    old_eta2 = eta2_table(old_merged, "cluster")
    old_sizes = old_merged["cluster"].value_counts().sort_index().to_dict()

    comparison = pd.DataFrame(
        {
            "adopted_MIN_TOTAL=1_K=3": old_eta2,
            f"reliable_core_K={args.k}": new_eta2,
        }
    )
    comparison.to_csv(DATA / f"comparison_adopted_vs_reliable_core_k{args.k}.csv")

    lines = [
        f"# Reliable-core K={args.k} vs adopted MIN_TOTAL=1 K=3",
        "",
        f"Adopted solution cluster sizes: {old_sizes}",
        f"Reliable-core K={args.k} cluster sizes: {new_sizes}",
        "",
        comparison.to_markdown(),
        "",
        "## Reading",
        "",
        "- eta2 for log_total_activity should be far lower in the reliable-core",
        "  column than the adopted column if the activity-domination problem is",
        "  resolved by threshold-filtering, not by chance.",
        "- eta2 for the late-night timing metrics (post_midnight_share,",
        "  deep_night_share, post_midnight_persistence) should be comparable to or",
        "  higher in the reliable-core column -- evidence the freed-up variance is",
        "  now organised around genuine rhythm, not noise.",
        "- eta2 for distance_to_centre is not expected to jump dramatically; a",
        "  modest, stable value here is itself informative (bus late-night rhythm",
        "  is not strongly tied to simple centre-periphery distance, independent",
        "  of the activity-noise problem).",
    ]
    (REPORT / f"VALIDATE_RELIABLE_CORE_K{args.k}.md").write_text("\n".join(lines), encoding="utf-8")
    print(comparison.to_string())
    print()
    print("Reliable-core sizes:", new_sizes)
    print("Adopted sizes:", old_sizes)


if __name__ == "__main__":
    main()
