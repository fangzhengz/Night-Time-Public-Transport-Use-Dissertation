# -*- coding: utf-8 -*-
"""Compare StopArea raw-share and CLR candidates on their common sample."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def read_new_labels(variant: str, k: int) -> pd.DataFrame:
    path = C.OUT / variant / "labels" / f"k{k}_labels.csv"
    frame = pd.read_csv(path, dtype={"lsoa": str})
    return frame.loc[frame["retained_for_fit"], ["lsoa", "cluster"]].copy()


def matched_jaccard(left: np.ndarray, right: np.ndarray, k: int) -> tuple[float, float]:
    contingency = np.zeros((k, k), dtype=int)
    for a, b in zip(left, right):
        contingency[int(a), int(b)] += 1
    left_sizes = contingency.sum(axis=1, keepdims=True)
    right_sizes = contingency.sum(axis=0, keepdims=True)
    union = left_sizes + right_sizes - contingency
    scores = np.divide(contingency, union, out=np.zeros_like(contingency, dtype=float), where=union > 0)
    rows, columns = linear_sum_assignment(-scores)
    matched = scores[rows, columns]
    return float(matched.mean()), float(matched.min())


def compare_pair(label: str, left: pd.DataFrame, right: pd.DataFrame, k: int) -> dict:
    merged = left.merge(right, on="lsoa", suffixes=("_left", "_right"), validate="one_to_one")
    mean_jaccard, min_jaccard = matched_jaccard(
        merged["cluster_left"].to_numpy(), merged["cluster_right"].to_numpy(), k
    )
    return {
        "comparison": label,
        "K": k,
        "n_left": len(left),
        "n_right": len(right),
        "n_common": len(merged),
        "ARI_common_units": float(
            adjusted_rand_score(merged["cluster_left"], merged["cluster_right"])
        ),
        "mean_matched_cluster_jaccard": mean_jaccard,
        "min_matched_cluster_jaccard": min_jaccard,
    }


def main() -> None:
    rows: list[dict] = []
    for k in C.CANDIDATE_KS:
        raw = read_new_labels("raw_share", k)
        clr = read_new_labels("clr", k)
        rows.append(compare_pair("new_stoparea_raw_share_vs_clr", raw, clr, k))

    result = pd.DataFrame(rows)
    result.to_csv(C.COMPARISON / "raw_share_clr_comparison.csv", index=False)
    report = [
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite/experiment-agent",
        "- Origin Mode: validate",
        "- Verification Status: ANALYZED",
        "- Version Label: stoparea_variant_comparison_v1",
        "",
        "# StopArea raw-share and CLR comparison",
        "",
        result.to_markdown(index=False, floatfmt=".6f"),
        "",
        "ARI and matched Jaccard describe partition agreement, not substantive model quality.",
        "Both partitions use exactly the same LSOAs and differ only in the feature transform.",
    ]
    (C.REPORT / "VARIANT_COMPARISON.md").write_text("\n".join(report), encoding="utf-8")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
