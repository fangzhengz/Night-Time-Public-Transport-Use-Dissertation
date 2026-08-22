from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FYP = ROOT.parent
BASE = FYP / "rq1_bus_hub_first_reclustering"
BASE_SRC = BASE / "src"
sys.path.insert(0, str(BASE_SRC))
import config as base_config
import summarise_k3_candidate as candidate


OUT = ROOT / "outputs"
FEATURES = OUT / "features"
DIAGNOSTICS = OUT / "diagnostics"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
FIGURES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    X = pd.read_parquet(FEATURES / "X_bus_fullweek_alpha0_fixed_sample.parquet")
    X.index = X.index.astype(str)
    meta = pd.read_csv(
        BASE / "outputs" / "features" / "bus_fullweek_meta_alpha5.csv", index_col="lsoa"
    )
    meta.index = meta.index.astype(str)
    alpha0 = pd.read_csv(OUT / "labels" / "alpha0_full_k3_labels.csv").set_index("unit")["cluster"]
    alpha0.index = alpha0.index.astype(str)
    alpha0 = alpha0.reindex(X.index).astype(int)
    alpha5 = pd.read_csv(
        BASE / "outputs" / "labels" / "bus_fullweek_k3_labels.csv"
    ).set_index("unit")["cluster"]
    alpha5.index = alpha5.index.astype(str)
    alpha5 = alpha5.reindex(X.index).astype(int)

    signatures = candidate.signatures(X, meta, alpha0)
    spatial_by_cluster, spatial_summary, mapped = candidate.spatial_diagnostic(alpha0)
    contingency = pd.crosstab(alpha5, alpha0)
    contingency_share = contingency.div(contingency.sum(axis=1), axis=0)
    signatures.to_csv(DIAGNOSTICS / "alpha0_k3_signatures.csv", index=False)
    spatial_by_cluster.to_csv(DIAGNOSTICS / "alpha0_k3_spatial_adjacency.csv", index=False)
    (DIAGNOSTICS / "alpha0_k3_spatial_summary.json").write_text(
        json.dumps(spatial_summary, indent=2), encoding="utf-8"
    )
    contingency.to_csv(DIAGNOSTICS / "alpha5_to_alpha0_k3_contingency.csv")
    contingency_share.to_csv(DIAGNOSTICS / "alpha5_to_alpha0_k3_contingency_row_share.csv")

    fig, ax = plt.subplots(figsize=(9, 9))
    colors = ["#e41a1c", "#377eb8", "#4daf4a"]
    for cluster in sorted(mapped["cluster"].unique()):
        mapped[mapped["cluster"] == cluster].plot(
            ax=ax, color=colors[int(cluster)], linewidth=0.05, edgecolor="#dddddd"
        )
    handles = []
    for _, row in signatures.iterrows():
        cluster = int(row["cluster"])
        handles.append(
            plt.Line2D(
                [0], [0], marker="s", linestyle="", color=colors[cluster],
                label=f"C{cluster} (n={int(row['n'])})", markersize=9,
            )
        )
    ax.legend(handles=handles, loc="lower right")
    ax.set_axis_off()
    ax.set_title("Hub-first full-week bus GMM, alpha=0, K=3")
    fig.tight_layout()
    fig.savefig(FIGURES / "alpha0_k3_map.png", dpi=200)
    plt.close(fig)

    report = f"""# alpha=0 K=3 candidate audit

## Cluster signatures

{signatures.to_markdown(index=False)}

## Spatial adjacency

Observed same-cluster neighbour share:
{spatial_summary['observed_same_cluster_edge_share']:.3f}; random label-frequency
expectation: {spatial_summary['random_label_expected_share']:.3f}; ratio:
{spatial_summary['observed_to_expected_ratio']:.2f}.

{spatial_by_cluster.to_markdown(index=False)}

## alpha=5 rows mapped to alpha=0 columns

{contingency.to_markdown()}

Row shares:

{contingency_share.to_markdown()}

## Reading

The high-activity/intermediate-late cluster is alpha=0 C0. The low-activity,
early-fading cluster is alpha=0 C2. The smaller late-persistent cluster is
alpha=0 C1. Cluster numbers are arbitrary and should be replaced with descriptive
names in writing.
"""
    (REPORT / "ALPHA0_K3_AUDIT.md").write_text(report, encoding="utf-8")
    print(signatures.to_string(index=False))
    print(json.dumps(spatial_summary, indent=2))
    print(contingency.to_string())
    print(REPORT / "ALPHA0_K3_AUDIT.md")


if __name__ == "__main__":
    main()
