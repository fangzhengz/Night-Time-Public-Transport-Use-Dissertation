# -*- coding: utf-8 -*-
"""Compare original, parent-hub-first and StopArea-only isolated results."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


VERSIONS = {
    "original": {
        "meta": C.ORIGINAL_BUS_META,
        "grid": C.ORIGINAL_BUS_BIC_GRID,
        "kdiag": C.ORIGINAL_BUS_KDIAG,
        "labels": C.ORIGINAL_BUS_LABELS,
    },
    "parent_hub_first": {
        "meta": C.HUBFIRST_BUS_META,
        "grid": C.HUBFIRST_BUS_BIC_GRID,
        "kdiag": C.HUBFIRST_BUS_KDIAG,
        "labels": C.HUBFIRST_BUS_LABELS,
    },
    "stoparea_only": {
        "meta": C.FEAT / "bus_meta.csv",
        "grid": C.DIAG / "bus_bic_grid.csv",
        "kdiag": C.DIAG / "bus_kdiag.csv",
        "labels": C.LAB,
    },
}


def unit_set(path: Path) -> set[str]:
    return set(pd.read_csv(path, index_col=0).index.astype(str))


def label_ari(left_dir: Path, right_dir: Path, k: int) -> tuple[int, float]:
    left = pd.read_csv(left_dir / f"bus_k{k}_labels.csv")
    right = pd.read_csv(right_dir / f"bus_k{k}_labels.csv")
    left["unit"] = left["unit"].astype(str)
    right["unit"] = right["unit"].astype(str)
    merged = left[["unit", "cluster"]].merge(
        right[["unit", "cluster"]], on="unit", suffixes=("_left", "_right")
    )
    return len(merged), adjusted_rand_score(merged["cluster_left"], merged["cluster_right"])


def main() -> None:
    units = {name: unit_set(paths["meta"]) for name, paths in VERSIONS.items()}
    all_common = set.intersection(*units.values())
    sample_rows = [
        {"version": name, "n_lsoa_min_total_1": len(unit_codes), "n_common_all_three": len(all_common)}
        for name, unit_codes in units.items()
    ]
    sample = pd.DataFrame(sample_rows)

    best_rows = []
    for name, paths in VERSIONS.items():
        grid = pd.read_csv(paths["grid"])
        best = grid.loc[grid["BIC"].idxmin()]
        best_rows.append({
            "version": name,
            "covariance": best["covariance"],
            "K": int(best["K"]),
            "BIC_within_version": float(best["BIC"]),
        })
    best_table = pd.DataFrame(best_rows)

    diag_frames = []
    cols = ["K", "BIC", "silhouette", "calinski_harabasz", "davies_bouldin", "ARI", "ARI_sd"]
    for name, paths in VERSIONS.items():
        frame = pd.read_csv(paths["kdiag"])[cols].copy()
        frame.insert(0, "version", name)
        diag_frames.append(frame)
    diagnostics = pd.concat(diag_frames, ignore_index=True)

    pair_rows = []
    pairs = [
        ("original", "stoparea_only"),
        ("parent_hub_first", "stoparea_only"),
        ("original", "parent_hub_first"),
    ]
    for left, right in pairs:
        for k in C.CAND_K:
            n, ari = label_ari(VERSIONS[left]["labels"], VERSIONS[right]["labels"], k)
            pair_rows.append({"left": left, "right": right, "K": k, "n_matched": n, "ARI": ari})
    pairwise = pd.DataFrame(pair_rows)

    sample.to_csv(C.DATA / "sample_comparison.csv", index=False)
    best_table.to_csv(C.DATA / "bic_best_comparison.csv", index=False)
    diagnostics.to_csv(C.DATA / "kdiag_comparison_long.csv", index=False)
    pairwise.to_csv(C.DATA / "label_ari_pairwise.csv", index=False)

    k34 = diagnostics.loc[diagnostics["K"].isin([3, 4])].copy()
    report = [
        "## Material Passport", "",
        "- Origin Skill: academic-research-suite/experiment-agent", "- Origin Mode: run + validate",
        "- Verification Status: ANALYZED", "- Version Label: stoparea_only_isolated_v1", "",
        "# StopArea-only isolation comparison", "",
        "Only spatial preprocessing differs. Downstream feature and GMM source is",
        "executed directly from `rq1_bus_hub_first_isolated_test/src` with paths rebound.", "",
        "## Sample", "", sample.to_markdown(index=False), "",
        "## Global BIC minimum within each version", "",
        best_table.to_markdown(index=False, floatfmt=".4f"), "",
        "Absolute BIC is not compared across versions because sample size and input",
        "realisation differ. Each value is used only for K/covariance choice within its version.", "",
        "## K=3 and K=4 diagnostics", "", k34.to_markdown(index=False, floatfmt=".4f"), "",
        "## Same-K label agreement", "", pairwise.to_markdown(index=False, floatfmt=".4f"), "",
        "## Interpretation boundary", "",
        "This test identifies sensitivity to the spatial-unit definition. It does not",
        "decide whether a child StopArea or a complete parent interchange is the true",
        "substantive unit; that decision must use coverage, direction-zero behaviour,",
        "stability and the RQ's area-versus-interchange interpretation together.", "",
    ]
    (C.REPORT / "STOPAREA_ONLY_ISOLATED_COMPARISON.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(sample.to_string(index=False))
    print("\n", best_table.to_string(index=False))
    print("\n", k34.to_string(index=False))
    print("\n", pairwise.to_string(index=False))


if __name__ == "__main__":
    main()
