# -*- coding: utf-8 -*-
"""03 - Side-by-side comparison against cluster_clean_version_fullweek's bus
result. Read-only against both runs' saved outputs; does not refit anything.
Isolates what changes when the ONLY difference is hub-first stop-to-LSOA
aggregation (see config.py's module docstring and README.md for what is held
fixed).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def log(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    orig_meta = pd.read_csv(C.ORIGINAL_BUS_META, index_col=0)
    new_meta = pd.read_csv(C.FEAT / "bus_meta.csv", index_col=0)
    orig_units = set(orig_meta.index.astype(str))
    new_units = set(new_meta.index.astype(str))
    common = orig_units & new_units

    sample_lines = [
        "## Sample",
        "",
        f"- original (point-in-polygon, MIN_TOTAL=1): n={len(orig_units)}",
        f"- hub-first (MIN_TOTAL=1, otherwise identical): n={len(new_units)}",
        f"- common LSOA codes present in both: {len(common)}",
        f"- only in original (hub-first merged them away): {len(orig_units - new_units)}",
        f"- only in hub-first (newly appear after hub merging): {len(new_units - orig_units)}",
        "",
    ]
    log("\n".join(sample_lines))

    orig_grid = pd.read_csv(C.ORIGINAL_BUS_BIC_GRID)
    new_grid = pd.read_csv(C.DIAG / "bus_bic_grid.csv")
    orig_best = orig_grid.loc[orig_grid.BIC.idxmin()]
    new_best = new_grid.loc[new_grid.BIC.idxmin()]
    bic_lines = [
        "## Global BIC minimum",
        "",
        f"- original: covariance={orig_best.covariance}, K={int(orig_best.K)}, BIC={orig_best.BIC:.1f}",
        f"- hub-first: covariance={new_best.covariance}, K={int(new_best.K)}, BIC={new_best.BIC:.1f}",
        "",
    ]
    log("\n".join(bic_lines))

    orig_kdiag = pd.read_csv(C.ORIGINAL_BUS_KDIAG).set_index("K")
    new_kdiag = pd.read_csv(C.DIAG / "bus_kdiag.csv").set_index("K")
    kdiag_cols = ["BIC", "silhouette", "calinski_harabasz", "davies_bouldin", "ARI", "ARI_sd"]
    kdiag_compare = orig_kdiag[kdiag_cols].join(new_kdiag[kdiag_cols], lsuffix="_original", rsuffix="_hubfirst")
    kdiag_compare = kdiag_compare.reset_index()

    ari_rows = []
    for k in C.CAND_K:
        orig_labels = pd.read_csv(C.ORIGINAL_BUS_LABELS / f"bus_k{k}_labels.csv")
        new_labels = pd.read_csv(C.LAB / f"bus_k{k}_labels.csv")
        orig_labels["unit"] = orig_labels["unit"].astype(str)
        new_labels["unit"] = new_labels["unit"].astype(str)
        merged = orig_labels.set_index("unit").reindex(common)["cluster"].rename("orig").to_frame()
        merged["hubfirst"] = new_labels.set_index("unit").reindex(common)["cluster"]
        merged = merged.dropna()
        ari = adjusted_rand_score(merged["orig"], merged["hubfirst"])
        ari_rows.append({"K": k, "n_matched": len(merged), "ARI_original_vs_hubfirst": ari})
        log(f"K={k}: ARI(original labels, hub-first labels) on {len(merged)} common LSOAs = {ari:.4f}")
    ari_df = pd.DataFrame(ari_rows)

    report_lines = [
        "# Hub-first isolation test: comparison against the true original",
        "",
        "Single changed variable: stop-to-LSOA aggregation (hub-first vs the",
        "original point-in-polygon assignment). MIN_TOTAL=1, no one-direction",
        "exclusion, no weaker-direction floor, alpha=0, identical GMM search --",
        "all copied verbatim from `cluster_clean_version_fullweek/src/config.py`.",
        "",
        *sample_lines,
        *bic_lines,
        "## K diagnostics, side by side",
        "",
        kdiag_compare.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Label agreement: original vs hub-first, same K, common LSOAs only",
        "",
        "ARI compares this run's labels against the true original's labels for",
        "the SAME candidate K, restricted to LSOA codes present in both samples",
        "-- i.e., holding K fixed, how much does re-clustering after hub-first",
        "reassignment alone move individual units between clusters.",
        "",
        ari_df.to_markdown(index=False, floatfmt=".4f"),
        "",
    ]
    (C.REPORT / "HUB_FIRST_ISOLATED_COMPARISON.md").write_text("\n".join(report_lines), encoding="utf-8")
    log(str(C.REPORT / "HUB_FIRST_ISOLATED_COMPARISON.md"))


if __name__ == "__main__":
    main()
