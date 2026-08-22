#!/usr/bin/env python
"""Quantify whether Rail ILR results are driven by activity or zero patterns."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import pairwise_distances


HERE = Path(__file__).resolve()
WORKSPACE = HERE.parents[1]
FYP = WORKSPACE.parent
SOURCE = FYP / "cluster_clean_version_fullweek" / "outputs"
RAW_FEATURES = SOURCE / "features" / "X_rail.parquet"
RAW_META = SOURCE / "features" / "rail_meta.csv"
RAW_LABELS = SOURCE / "labels"
K_VALUES = tuple(range(3, 9))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--analysis-output-root", type=Path, default=WORKSPACE / "outputs"
    )
    return parser.parse_args()


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = float(y.mean())
    total = float(np.square(y - grand).sum())
    if total <= 0:
        return float("nan")
    between = sum(
        int((labels == cluster).sum())
        * (float(y[labels == cluster].mean()) - grand) ** 2
        for cluster in np.unique(labels)
    )
    return float(between / total)


def load_label(path: Path, units: pd.Index) -> np.ndarray:
    frame = pd.read_csv(path, dtype={"unit": str}).set_index("unit").reindex(units)
    if frame["cluster"].isna().any():
        raise ValueError(f"label file does not cover all units: {path}")
    return frame["cluster"].to_numpy(dtype=int)


def markdown_table(frame: pd.DataFrame, digits: int = 3) -> str:
    shown = frame.copy()
    for column in shown.columns:
        if pd.api.types.is_float_dtype(shown[column]):
            shown[column] = shown[column].map(
                lambda value: "" if pd.isna(value) else f"{value:.{digits}f}"
            )
    headers = [str(column) for column in shown.columns]
    rows = [[str(value) for value in row] for row in shown.itertuples(index=False, name=None)]
    widths = [
        max(len(headers[i]), max((len(row[i]) for row in rows), default=0))
        for i in range(len(headers))
    ]

    def render(row: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) + " |"

    return "\n".join(
        [render(headers), render(["-" * width for width in widths]), *[render(row) for row in rows]]
    )


def main() -> int:
    args = parse_args()
    root = args.analysis_output_root.resolve()
    diagnostics = root / "diagnostics"
    data = root / "data"
    figures = root / "figures"
    report = root / "report"
    for directory in (diagnostics, data, figures, report):
        directory.mkdir(parents=True, exist_ok=True)

    raw = pd.read_parquet(RAW_FEATURES)
    raw.index = raw.index.astype(str)
    meta = pd.read_csv(RAW_META, dtype={"NLC": str}).set_index("NLC").reindex(raw.index)
    ilr_path = root / "features" / "X_rail_fullweek_ilr342.parquet"
    ilr = pd.read_parquet(ilr_path).reindex(raw.index)
    if ilr.isna().any().any():
        raise ValueError("saved ILR features do not align with raw Rail stations")

    metrics = pd.DataFrame(index=raw.index)
    metrics["log_total_activity"] = np.log1p(meta["total_activity"])
    metrics["log_entry_activity"] = np.log1p(meta["tot_entry"])
    metrics["log_exit_activity"] = np.log1p(meta["tot_exit"])
    metrics["zero_total"] = (raw == 0).sum(axis=1)
    metrics["zero_entry"] = (raw.filter(like="entry_") == 0).sum(axis=1)
    metrics["zero_exit"] = (raw.filter(like="exit_") == 0).sum(axis=1)
    metrics.to_csv(data / "rail_transform_driver_metrics.csv", encoding="utf-8-sig")

    eta_rows = []
    cluster_rows = []
    labels_cache: dict[tuple[str, int], np.ndarray] = {}
    for representation in ("raw", "ilr"):
        for k in K_VALUES:
            label_path = (
                RAW_LABELS / f"rail_k{k}_labels.csv"
                if representation == "raw"
                else root / "labels" / f"ilr_k{k}_labels.csv"
            )
            labels = load_label(label_path, raw.index)
            labels_cache[(representation, k)] = labels
            for metric in metrics.columns:
                eta_rows.append(
                    {
                        "representation": representation,
                        "K": k,
                        "metric": metric,
                        "eta_squared": eta_squared(metrics[metric], labels),
                    }
                )
            if k == 5:
                for cluster in range(k):
                    mask = labels == cluster
                    row = {
                        "representation": representation,
                        "K": k,
                        "cluster": cluster,
                        "n": int(mask.sum()),
                    }
                    for metric in metrics.columns:
                        row[f"{metric}_mean"] = float(metrics.loc[mask, metric].mean())
                    cluster_rows.append(row)
    eta = pd.DataFrame(eta_rows)
    clusters = pd.DataFrame(cluster_rows)
    eta.to_csv(diagnostics / "transform_driver_eta_squared.csv", index=False, encoding="utf-8-sig")
    clusters.to_csv(diagnostics / "k5_transform_driver_cluster_summary.csv", index=False, encoding="utf-8-sig")

    triangle = np.triu_indices(len(raw), 1)
    raw_distance = pairwise_distances(raw.to_numpy(dtype=float))[triangle]
    ilr_distance = pairwise_distances(ilr.to_numpy(dtype=float))[triangle]
    activity = metrics["log_total_activity"].to_numpy(dtype=float)
    zeros = metrics["zero_total"].to_numpy(dtype=float)
    activity_difference = np.abs(activity[:, None] - activity[None, :])[triangle]
    zero_count_difference = np.abs(zeros[:, None] - zeros[None, :])[triangle]
    zero_pattern_difference = pairwise_distances(
        (raw.to_numpy(dtype=float) == 0).astype(float), metric="hamming"
    )[triangle]
    distance_rows = []
    for representation, distance in (
        ("raw_euclidean", raw_distance),
        ("ilr_euclidean", ilr_distance),
    ):
        for driver, values in (
            ("absolute_log_activity_difference", activity_difference),
            ("absolute_zero_count_difference", zero_count_difference),
            ("zero_pattern_hamming_difference", zero_pattern_difference),
        ):
            result = spearmanr(distance, values)
            distance_rows.append(
                {
                    "representation": representation,
                    "driver": driver,
                    "spearman_rho": float(result.statistic),
                    "p_value": float(result.pvalue),
                    "station_pairs": int(len(distance)),
                }
            )
    distance = pd.DataFrame(distance_rows)
    distance.to_csv(diagnostics / "distance_driver_correlations.csv", index=False, encoding="utf-8-sig")

    zero_activity = spearmanr(metrics["zero_total"], metrics["log_total_activity"])
    zero_eta = eta[eta["metric"] == "zero_total"].pivot(
        index="K", columns="representation", values="eta_squared"
    )
    activity_eta = eta[eta["metric"] == "log_total_activity"].pivot(
        index="K", columns="representation", values="eta_squared"
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for representation, color in (("raw", "#2F6B4F"), ("ilr", "#500778")):
        axes[0].plot(zero_eta.index, zero_eta[representation], marker="o", label=representation, color=color)
        axes[1].plot(activity_eta.index, activity_eta[representation], marker="o", label=representation, color=color)
    axes[0].set_title("Cluster eta-squared: zero-bin count")
    axes[1].set_title("Cluster eta-squared: log total activity")
    for axis in axes:
        axis.set(xlabel="K", ylabel="eta-squared", ylim=(0, 1))
        axis.grid(alpha=0.25)
        axis.legend()
    fig.tight_layout()
    fig.savefig(figures / "transform_driver_eta_squared.png", dpi=220)
    plt.close(fig)

    ilr_k5 = labels_cache[("ilr", 5)]
    fig, axis = plt.subplots(figsize=(7, 5.5))
    scatter = axis.scatter(
        metrics["log_total_activity"],
        metrics["zero_total"],
        c=ilr_k5,
        cmap="tab10",
        alpha=0.8,
    )
    axis.set(
        xlabel="log(1 + total activity)",
        ylabel="Zero temporal cells (of 344)",
        title="Rail ILR K=5 is strongly stratified by temporal sparsity",
    )
    axis.grid(alpha=0.2)
    axis.legend(*scatter.legend_elements(), title="ILR cluster", loc="best")
    fig.tight_layout()
    fig.savefig(figures / "ilr_k5_zero_activity_scatter.png", dpi=220)
    plt.close(fig)

    raw_k5_zero_eta = float(
        eta[(eta["representation"] == "raw") & (eta["K"] == 5) & (eta["metric"] == "zero_total")]["eta_squared"].iloc[0]
    )
    ilr_k5_zero_eta = float(
        eta[(eta["representation"] == "ilr") & (eta["K"] == 5) & (eta["metric"] == "zero_total")]["eta_squared"].iloc[0]
    )
    raw_zero_rho = float(
        distance[(distance["representation"] == "raw_euclidean") & (distance["driver"] == "zero_pattern_hamming_difference")]["spearman_rho"].iloc[0]
    )
    ilr_zero_rho = float(
        distance[(distance["representation"] == "ilr_euclidean") & (distance["driver"] == "zero_pattern_hamming_difference")]["spearman_rho"].iloc[0]
    )
    selected_eta = eta[
        (eta["K"].isin([4, 5, 6]))
        & (eta["metric"].isin(["zero_total", "log_total_activity"]))
    ]
    report_text = f"""## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate
- Origin Date: {datetime.now(timezone.utc).isoformat()}
- Verification Status: ANALYZED
- Version Label: rail_ilr_transform_driver_v1

# Rail ILR transformation-driver diagnostic

## Verdict

The alpha=1 ILR sensitivity is dominated by temporal zero-pattern structure.
It validly shows that raw K=5 does not survive this exact transformation, but
it does **not** by itself establish that raw K=5 is substantively invalid or
that ILR K=4 should replace it.

## Cluster-level association

{markdown_table(selected_eta)}

For K=5, zero-bin-count eta-squared rises from `{raw_k5_zero_eta:.3f}` under the
raw-share labels to `{ilr_k5_zero_eta:.3f}` under the ILR labels.

## Pairwise distance drivers

{markdown_table(distance)}

The Spearman correlation between station distance and zero-pattern Hamming
difference rises from `{raw_zero_rho:.3f}` in raw-share space to
`{ilr_zero_rho:.3f}` in ILR space. Across stations, zero-bin count and log total
activity have Spearman rho `{zero_activity.statistic:.3f}`.

## Interpretation

The empirical-prior posterior is strictly positive and mathematically valid,
but an observed zero receives a share proportional to the aggregate prior and
inversely related to the station's direction total. With 6,989 zero cells, log
ratios strongly magnify differences in which bins are zero. The resulting
clusters therefore combine temporal shape with sparsity/reliability structure.

## Decision boundary

1. Report the ILR run as a failed robustness check for the current K=5 labels.
2. Do not treat ILR K=4 as a new substantive station typology from this run.
3. A replacement compositional primary model would require a prespecified zero
   treatment/reliability sensitivity and a coordinate-invariant or otherwise
   justified covariance strategy.
"""
    (report / "TRANSFORM_DIAGNOSTIC.md").write_text(report_text, encoding="utf-8")
    metadata = {
        "analysis_output_root": str(root),
        "n_stations": int(len(raw)),
        "n_pairs": int(len(raw_distance)),
        "zero_activity_spearman_rho": float(zero_activity.statistic),
        "raw_k5_zero_eta_squared": raw_k5_zero_eta,
        "ilr_k5_zero_eta_squared": ilr_k5_zero_eta,
        "raw_distance_zero_pattern_rho": raw_zero_rho,
        "ilr_distance_zero_pattern_rho": ilr_zero_rho,
    }
    (report / "TRANSFORM_DIAGNOSTIC_METADATA.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
