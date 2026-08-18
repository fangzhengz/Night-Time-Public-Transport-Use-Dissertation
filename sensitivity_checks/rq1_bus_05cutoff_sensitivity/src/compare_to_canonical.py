# -*- coding: utf-8 -*-
"""Compare the 05:00-cutoff sensitivity sidecar's CLR K=4 result to the
canonical (18:00-06:00) StopArea CLR K=4 result. Read-only: writes only to
this sidecar's own comparison/ output directory.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

HERE = Path(__file__).resolve()
SIDECAR_ROOT = HERE.parents[1]
FYP = HERE.parents[2]

CANONICAL_ROOT = FYP / "rq1_bus_stoparea_clustering" / "outputs"
SIDECAR_CLR_ROOT = SIDECAR_ROOT / "clustering_05cutoff" / "outputs" / "clr"
OUT = SIDECAR_ROOT / "clustering_05cutoff" / "outputs" / "comparison"
OUT.mkdir(parents=True, exist_ok=True)


def load_labels(path: Path, k: int) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"lsoa": str})
    return df


def main() -> None:
    canon_labels = load_labels(CANONICAL_ROOT / "clr" / "labels" / "k4_labels.csv", 4)
    side_labels = load_labels(SIDECAR_CLR_ROOT / "labels" / "k4_labels.csv", 4)

    canon_retained = canon_labels.loc[canon_labels["retained_for_fit"], ["lsoa", "cluster"]].rename(
        columns={"cluster": "cluster_canonical_06"}
    )
    side_retained = side_labels.loc[side_labels["retained_for_fit"], ["lsoa", "cluster"]].rename(
        columns={"cluster": "cluster_05cutoff"}
    )

    n_canon = len(canon_retained)
    n_side = len(side_retained)
    common = canon_retained.merge(side_retained, on="lsoa", how="inner")
    n_common = len(common)

    only_canon = set(canon_retained["lsoa"]) - set(side_retained["lsoa"])
    only_side = set(side_retained["lsoa"]) - set(canon_retained["lsoa"])

    ari_common = float(
        adjusted_rand_score(common["cluster_canonical_06"], common["cluster_05cutoff"])
    )

    contingency = pd.crosstab(
        common["cluster_canonical_06"], common["cluster_05cutoff"],
        rownames=["canonical_06_cluster"], colnames=["cutoff_05_cluster"],
    )
    contingency.to_csv(OUT / "k4_contingency_common_lsoas.csv")

    # Majority-mapping-based "changed label" rate: map each canonical cluster
    # to the sidecar cluster it overlaps most, then count common LSOAs whose
    # sidecar cluster differs from that mapped-through label.
    majority_map = contingency.idxmax(axis=1)
    common = common.copy()
    common["cluster_05cutoff_mapped_to_canonical_frame"] = common["cluster_canonical_06"].map(majority_map)
    changed = common["cluster_05cutoff"] != common["cluster_05cutoff_mapped_to_canonical_frame"]
    n_changed = int(changed.sum())
    pct_changed = 100 * n_changed / n_common if n_common else float("nan")

    retention_rows = [
        {"metric": "n_retained_canonical_06", "value": n_canon},
        {"metric": "n_retained_05cutoff", "value": n_side},
        {"metric": "n_common_retained", "value": n_common},
        {"metric": "n_only_in_canonical_06_not_05cutoff", "value": len(only_canon)},
        {"metric": "n_only_in_05cutoff_not_canonical_06", "value": len(only_side)},
        {"metric": "ari_on_common_lsoas_k4", "value": ari_common},
        {"metric": "n_common_lsoas_changed_cluster_via_majority_map", "value": n_changed},
        {"metric": "pct_common_lsoas_changed_cluster_via_majority_map", "value": pct_changed},
    ]
    retention_df = pd.DataFrame(retention_rows)
    retention_df.to_csv(OUT / "retention_and_ari_summary.csv", index=False)

    # Cluster-size comparison (on each pipeline's own retained set, not just common).
    canon_sizes = canon_retained["cluster_canonical_06"].value_counts().sort_index()
    side_sizes = side_retained["cluster_05cutoff"].value_counts().sort_index()
    size_df = pd.DataFrame(
        {"canonical_06_n": canon_sizes, "05cutoff_n": side_sizes}
    ).fillna(0).astype(int)
    size_df["canonical_06_share"] = size_df["canonical_06_n"] / size_df["canonical_06_n"].sum()
    size_df["05cutoff_share"] = size_df["05cutoff_n"] / size_df["05cutoff_n"].sum()
    size_df.to_csv(OUT / "cluster_size_comparison.csv")

    # kdiag (silhouette, eta2, bootstrap ARI) comparison for K=2..12.
    canon_kdiag = pd.read_csv(CANONICAL_ROOT / "clr" / "diagnostics" / "kdiag.csv")
    side_kdiag = pd.read_csv(SIDECAR_CLR_ROOT / "diagnostics" / "kdiag.csv")
    kdiag_compare = canon_kdiag.merge(
        side_kdiag, on="K", suffixes=("_canonical_06", "_05cutoff")
    )
    for col in [
        "silhouette", "activity_eta2", "post_midnight_share_eta2",
        "deep_night_share_eta2", "post_midnight_persistence_eta2",
        "direction_balance_eta2", "weekend_ratio_eta2", "timing_mean_eta2",
        "bootstrap_ari_mean", "min_cluster_share",
    ]:
        kdiag_compare[f"{col}_diff_05cutoff_minus_canonical"] = (
            kdiag_compare[f"{col}_05cutoff"] - kdiag_compare[f"{col}_canonical_06"]
        )
    kdiag_compare.to_csv(OUT / "kdiag_comparison.csv", index=False)

    # Central/outer diagnostic comparison at K=4.
    canon_geo = pd.read_csv(CANONICAL_ROOT / "clr" / "data" / "central_outer_diagnostic.csv")
    side_geo = pd.read_csv(SIDECAR_CLR_ROOT / "data" / "central_outer_diagnostic.csv")
    geo_compare = canon_geo.merge(side_geo, on="K", suffixes=("_canonical_06", "_05cutoff"))
    geo_compare.to_csv(OUT / "central_outer_comparison.csv", index=False)

    lines = []
    lines.append("# 05:00-cutoff sensitivity: comparison to canonical StopArea CLR K=4\n")
    lines.append(
        "Canonical: 18:00-06:00 night window (72 features), min-direction "
        "retention threshold 36 (= 12 hours x 3 day types, i.e. an average of "
        ">=1 activity per hourly interval per Marinas-Collado et al. 2022). "
        "Sidecar: 18:00-05:00 (66 features), retention threshold corrected to "
        "33 (= 11 hours x 3 day types) to preserve the same >=1/interval "
        "reliability standard rather than reusing the canonical absolute count. "
        "StopArea allocation, CLR construction, and GMM/bootstrap "
        "hyperparameters are otherwise identical. Only the raw BUSTO "
        "preprocessing `--end-min` (1740 vs 1800) and the retention threshold "
        "differ.\n"
    )
    lines.append("## Retained-sample and partition agreement at K=4\n")
    lines.append(retention_df.to_markdown(index=False))
    lines.append("")
    lines.append("## Cluster size comparison at K=4 (each pipeline's own retained set)\n")
    lines.append(size_df.to_markdown())
    lines.append("")
    lines.append("## K diagnostics comparison (K=2..12)\n")
    show_cols = [
        "K", "silhouette_canonical_06", "silhouette_05cutoff",
        "activity_eta2_canonical_06", "activity_eta2_05cutoff",
        "timing_mean_eta2_canonical_06", "timing_mean_eta2_05cutoff",
        "bootstrap_ari_mean_canonical_06", "bootstrap_ari_mean_05cutoff",
        "min_cluster_share_canonical_06", "min_cluster_share_05cutoff",
    ]
    lines.append(kdiag_compare[show_cols].to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    lines.append("## Central-vs-outer diagnostic comparison\n")
    lines.append(geo_compare.to_markdown(index=False, floatfmt=".4f"))
    lines.append("")
    (OUT / "COMPARISON_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    print(retention_df.to_string(index=False))
    print()
    print(size_df.to_string())
    print()
    print(f"Wrote comparison outputs to {OUT}")


if __name__ == "__main__":
    main()
