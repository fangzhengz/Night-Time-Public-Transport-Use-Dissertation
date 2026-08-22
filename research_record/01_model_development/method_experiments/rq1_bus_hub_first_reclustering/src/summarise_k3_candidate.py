from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.strtree import STRtree
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


K = 3


def parse_feature(feature: str) -> tuple[str, str, int]:
    stem, hour = feature.rsplit("_", 1)
    direction, day_type = stem.split("_", 1)
    return direction, day_type, int(hour)


def signatures(X: pd.DataFrame, meta: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    records = []
    parsed = {column: parse_feature(column) for column in X.columns}
    for cluster in sorted(labels.unique()):
        units = labels.index[labels == cluster]
        cluster_x = X.loc[units]
        cluster_meta = meta.loc[units]
        record = {
            "cluster": int(cluster),
            "n": len(units),
            "share": len(units) / len(labels),
            "total_p10": cluster_meta["total_activity"].quantile(0.10),
            "total_median": cluster_meta["total_activity"].median(),
            "total_p90": cluster_meta["total_activity"].quantile(0.90),
            "median_boarding_alighting_total_ratio": (
                cluster_meta["tot_boardings"] / cluster_meta["tot_alightings"]
            ).median(),
        }
        mean = cluster_x.mean(axis=0)
        for direction in C.DIRECTIONS:
            direction_columns = [c for c, p in parsed.items() if p[0] == direction]
            for day_type in C.DAY_TYPES:
                columns = [c for c in direction_columns if parsed[c][1] == day_type]
                record[f"{direction}_{day_type}_share"] = float(mean[columns].sum())
            after_midnight = [c for c in direction_columns if parsed[c][2] >= 1440]
            deep_night = [c for c in direction_columns if parsed[c][2] >= 1500]
            record[f"{direction}_00_05_share"] = float(mean[after_midnight].sum())
            record[f"{direction}_01_05_share"] = float(mean[deep_night].sum())
            peak = mean[direction_columns].idxmax()
            _, peak_day, peak_hour = parse_feature(peak)
            record[f"{direction}_peak_day"] = peak_day
            record[f"{direction}_peak_hour"] = peak_hour
        records.append(record)
    return pd.DataFrame(records)


def top_feature_differences(X: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    global_mean = X.mean(axis=0)
    global_sd = X.std(axis=0).replace(0, np.nan)
    rows = []
    for cluster in sorted(labels.unique()):
        cluster_mean = X.loc[labels.index[labels == cluster]].mean(axis=0)
        z = ((cluster_mean - global_mean) / global_sd).sort_values(key=np.abs, ascending=False)
        for rank, (feature, value) in enumerate(z.head(10).items(), start=1):
            rows.append(
                {
                    "cluster": int(cluster),
                    "rank": rank,
                    "feature": feature,
                    "standardized_mean_difference": float(value),
                    "cluster_mean_share": float(cluster_mean[feature]),
                    "global_mean_share": float(global_mean[feature]),
                }
            )
    return pd.DataFrame(rows)


def spatial_diagnostic(labels: pd.Series) -> tuple[pd.DataFrame, dict, gpd.GeoDataFrame]:
    boundaries = gpd.read_file(C.LSOA_GEOJSON)[["LSOA21CD", "geometry"]]
    frame = boundaries.merge(
        labels.rename("cluster").rename_axis("LSOA21CD").reset_index(),
        on="LSOA21CD",
        how="inner",
    ).reset_index(drop=True)
    geometries = frame.geometry.to_numpy()
    pairs = STRtree(geometries).query(geometries, predicate="touches")
    left, right = pairs
    unique = left < right
    left, right = left[unique], right[unique]
    left_labels = frame.loc[left, "cluster"].to_numpy(dtype=int)
    right_labels = frame.loc[right, "cluster"].to_numpy(dtype=int)
    same = left_labels == right_labels
    shares = frame["cluster"].value_counts(normalize=True).sort_index()
    expected = float((shares**2).sum())
    observed = float(same.mean())
    summary = {
        "n_mapped_lsoas": len(frame),
        "n_queen_edges": len(left),
        "observed_same_cluster_edge_share": observed,
        "random_label_expected_share": expected,
        "observed_to_expected_ratio": observed / expected,
    }
    rows = []
    for cluster in sorted(frame["cluster"].unique()):
        incident = (left_labels == cluster) | (right_labels == cluster)
        internal = (left_labels == cluster) & (right_labels == cluster)
        rows.append(
            {
                "cluster": int(cluster),
                "n_lsoa": int((frame["cluster"] == cluster).sum()),
                "incident_edges": int(incident.sum()),
                "within_cluster_edges": int(internal.sum()),
                "within_share_of_incident_edges": float(internal.sum() / incident.sum()),
            }
        )
    return pd.DataFrame(rows), summary, frame


def old_new_contingency(labels: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    old_path = C.OLD_FULLWEEK / "outputs" / "labels" / "bus_k3_labels.csv"
    old = pd.read_csv(old_path).set_index("unit")["cluster"]
    old.index = old.index.astype(str)
    common = old.index.intersection(labels.index)
    counts = pd.crosstab(old.loc[common], labels.loc[common])
    row_shares = counts.div(counts.sum(axis=1), axis=0)
    ari = float(adjusted_rand_score(old.loc[common], labels.loc[common]))
    return counts, row_shares, ari


def plot_map(frame: gpd.GeoDataFrame, summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 9))
    colors = ["#e41a1c", "#377eb8", "#4daf4a"]
    for cluster in sorted(frame["cluster"].unique()):
        frame[frame["cluster"] == cluster].plot(
            ax=ax, color=colors[int(cluster)], linewidth=0.05, edgecolor="#dddddd"
        )
    handles = []
    for _, row in summary.iterrows():
        cluster = int(row["cluster"])
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="s",
                linestyle="",
                color=colors[cluster],
                label=f"C{cluster} (n={int(row['n'])})",
                markersize=9,
            )
        )
    ax.legend(handles=handles, loc="lower right")
    ax.set_axis_off()
    ax.set_title("Hub-first full-week bus GMM candidate K=3")
    fig.tight_layout()
    fig.savefig(C.FIGURES / "map_k3_with_legend.png", dpi=200)
    plt.close(fig)


def main() -> None:
    X = pd.read_parquet(C.FEATURES / "X_bus_fullweek_alpha5.parquet")
    X.index = X.index.astype(str)
    meta = pd.read_csv(C.FEATURES / "bus_fullweek_meta_alpha5.csv", index_col="lsoa")
    meta.index = meta.index.astype(str)
    label_frame = pd.read_csv(C.LABELS / "bus_fullweek_k3_labels.csv")
    labels = label_frame.set_index("unit")["cluster"]
    labels.index = labels.index.astype(str)
    labels = labels.reindex(X.index)
    if labels.isna().any():
        raise ValueError("K=3 labels do not cover the feature matrix")
    labels = labels.astype(int)

    signature = signatures(X, meta, labels)
    differences = top_feature_differences(X, labels)
    spatial_by_cluster, spatial_summary, mapped = spatial_diagnostic(labels)
    old_counts, old_row_shares, old_new_ari = old_new_contingency(labels)
    cluster_summary = pd.read_csv(C.DIAGNOSTICS / "bus_fullweek_cluster_summary.csv")
    cluster_summary = cluster_summary[cluster_summary["K"] == K]

    signature.to_csv(C.DIAGNOSTICS / "k3_candidate_signatures.csv", index=False)
    differences.to_csv(C.DIAGNOSTICS / "k3_candidate_top_feature_differences.csv", index=False)
    spatial_by_cluster.to_csv(C.DIAGNOSTICS / "k3_candidate_spatial_adjacency.csv", index=False)
    (C.DIAGNOSTICS / "k3_candidate_spatial_summary.json").write_text(
        json.dumps(spatial_summary, indent=2), encoding="utf-8"
    )
    old_counts.to_csv(C.DIAGNOSTICS / "k3_old_new_contingency_counts.csv")
    old_row_shares.to_csv(C.DIAGNOSTICS / "k3_old_new_contingency_row_shares.csv")
    plot_map(mapped, cluster_summary)

    recovery = pd.read_csv(C.DIAGNOSTICS / "bus_fullweek_bootstrap_cluster_recovery.csv")
    recovery = recovery[recovery["K"] == K]
    recovery_summary = (
        recovery.groupby("base_cluster", as_index=False)["matched_jaccard"]
        .agg(["mean", "std", "min", "median", "max"])
        .reset_index()
    )
    recovery_summary.to_csv(C.DIAGNOSTICS / "k3_cluster_recovery_summary.csv", index=False)

    report = f"""# K=3 candidate interpretation audit

## Direct verdict

K=3 is the BIC-supported candidate and is much more defensible than K>=4, but
it is **not yet a strongly separated three-type solution**. The temporal means
remain close, silhouette is low, and the least stable cluster must be treated
as provisional until the fixed-sample alpha sensitivity is run.

## Size and activity

{cluster_summary.to_markdown(index=False)}

{signature.to_markdown(index=False)}

## Bootstrap recovery by cluster

{recovery_summary.to_markdown(index=False)}

## Spatial adjacency

Across {spatial_summary['n_queen_edges']} retained-LSOA neighbour edges, the
observed same-cluster share is {spatial_summary['observed_same_cluster_edge_share']:.3f};
the label-frequency expectation is {spatial_summary['random_label_expected_share']:.3f}
(ratio {spatial_summary['observed_to_expected_ratio']:.2f}). This is a compact
spatial-coherence diagnostic, not a formal spatial clustering objective.

{spatial_by_cluster.to_markdown(index=False)}

## Relationship to the historical K=3 labels

ARI on shared LSOAs: {old_new_ari:.3f}.

Counts:

{old_counts.to_markdown()}

Old-cluster row shares mapped into the new clusters:

{old_row_shares.to_markdown()}

## Largest standardised profile deviations

{differences.to_markdown(index=False)}

## Interpretation limit

The new result is a combined consequence of hub-first allocation, the full-week
total>=50 floor, exception exclusion, and alpha=5 shrinkage. The low old-new ARI
therefore proves pipeline sensitivity, not which single change caused it. The
next minimal test is alpha=0 versus alpha=5 on exactly these 3,593 LSOAs.
"""
    (C.REPORT / "K3_CANDIDATE_AUDIT.md").write_text(report, encoding="utf-8")
    print(signature.to_string(index=False))
    print(json.dumps(spatial_summary, indent=2))
    print(recovery_summary.to_string(index=False))
    print(f"old-new K3 ARI={old_new_ari:.3f}")
    print(C.REPORT / "K3_CANDIDATE_AUDIT.md")


if __name__ == "__main__":
    main()
