"""Fair stability comparison of 15-minute and 1-hour Bus RQ1 clustering."""

from __future__ import annotations

import hashlib
import itertools
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.optimize import linear_sum_assignment
from scipy.stats import chi2_contingency, kruskal
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

SOURCE_LONG = (
    FYP
    / "cluster_clean_version_15min"
    / "outputs"
    / "preprocessed"
    / "bus_lsoa_night_long.parquet"
)
EXISTING_X15 = (
    FYP / "cluster_clean_version_15min" / "outputs" / "features" / "X_bus.parquet"
)
EXISTING_X60 = (
    FYP / "cluster_clean_version_fullweek" / "outputs" / "features" / "X_bus.parquet"
)
CONTEXT_METRICS = (
    FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"
)
LNWC_LINK = FYP / "rq2test analysis" / "outputs" / "data" / "bus_analysis_lsoa.csv"

OUT = ROOT / "outputs"
DATA = OUT / "data"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
WORKBOOK = OUT / "workbook"
for directory in (DATA, FIGURES, REPORT, WORKBOOK):
    directory.mkdir(parents=True, exist_ok=True)

DAYS = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
K_VALUES = [3, 4, 5]
COVARIANCES = ["diag", "tied"]
SEEDS = [11, 23, 37, 53, 71, 89]
N_BOOTSTRAPS = 10
REFERENCE_SEED = 42
N_INIT_REFERENCE = 10
N_INIT_SEED = 3
N_INIT_BOOTSTRAP = 2
REG_COVAR = 1e-6
MAX_ITER = 300
SILHOUETTE_SAMPLE = 2000
RANDOM_SEED = 20260702
START = time.time()

INTERPRETABILITY_METRICS = [
    "log_total_activity",
    "post_midnight_share",
    "deep_night_share",
    "direction_balance",
    "weekend_ratio",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def build_features(long: pd.DataFrame, bin_minutes: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = long.copy()
    frame["lsoa"] = frame["lsoa"].astype(str)
    if bin_minutes == 60:
        frame["time_bin"] = (frame["hour_bin"].astype(int) // 60) * 60
        frame = (
            frame.groupby(["day_type", "direction", "lsoa", "time_bin"], as_index=False)[
                "count"
            ]
            .sum()
        )
    elif bin_minutes == 15:
        frame["time_bin"] = frame["hour_bin"].astype(int)
    else:
        raise ValueError("Only 15-minute and 60-minute bins are supported")

    all_units = sorted(frame["lsoa"].unique())
    expected_bins = list(range(1080, 1800, bin_minutes))
    feature_parts = []
    total_parts = []
    for direction in DIRECTIONS:
        direction_blocks = []
        for day in DAYS:
            subset = frame.loc[
                (frame["direction"] == direction) & (frame["day_type"] == day)
            ]
            wide = subset.pivot_table(
                index="lsoa", columns="time_bin", values="count", fill_value=0.0
            )
            wide = wide.reindex(index=all_units, columns=expected_bins, fill_value=0.0)
            wide.columns = [
                f"{direction}_{day}_{int(time_bin)}" for time_bin in expected_bins
            ]
            direction_blocks.append(wide)
        counts = pd.concat(direction_blocks, axis=1)
        direction_total = counts.sum(axis=1)
        shares = counts.div(direction_total.replace(0, np.nan), axis=0).fillna(0.0)
        feature_parts.append(shares)
        total_parts.append(direction_total.rename(f"tot_{direction}"))

    features = pd.concat(feature_parts, axis=1)
    meta = pd.concat(total_parts, axis=1)
    meta["total_activity"] = meta.sum(axis=1)
    keep = meta.index[meta["total_activity"] >= 1]
    return features.loc[keep].sort_index(), meta.loc[keep].sort_index()


def aligned_max_difference(rebuilt: pd.DataFrame, existing_path: Path) -> float:
    existing = pd.read_parquet(existing_path)
    existing.index = existing.index.astype(str)
    existing = existing.reindex(index=rebuilt.index, columns=rebuilt.columns)
    if existing.isna().any().any():
        raise AssertionError(f"Existing feature matrix cannot be aligned: {existing_path}")
    return float(np.abs(existing.to_numpy() - rebuilt.to_numpy()).max())


def fit_model(
    values: np.ndarray,
    k: int,
    covariance: str,
    seed: int,
    n_init: int,
) -> GaussianMixture:
    return GaussianMixture(
        n_components=k,
        covariance_type=covariance,
        n_init=n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=seed,
    ).fit(values)


def pairwise_ari(label_sets: list[np.ndarray]) -> tuple[float, float, float]:
    scores = [
        adjusted_rand_score(label_sets[i], label_sets[j])
        for i, j in itertools.combinations(range(len(label_sets)), 2)
    ]
    return float(np.mean(scores)), float(np.std(scores)), float(np.min(scores))


def epsilon_squared_by_cluster(
    joined: pd.DataFrame,
    metric: str,
    k: int,
) -> float:
    samples = [
        group[metric].dropna().to_numpy()
        for _, group in joined.groupby("cluster", sort=True)
    ]
    statistic, _ = kruskal(*samples)
    n = sum(len(sample) for sample in samples)
    return float(max(0.0, (statistic - k + 1) / (n - k)))


def cramers_v(cluster: pd.Series, lnwc: pd.Series) -> float:
    table = pd.crosstab(cluster, lnwc)
    chi_square, _, _, _ = chi2_contingency(table)
    denominator = len(cluster) * min(table.shape[0] - 1, table.shape[1] - 1)
    return float(np.sqrt(chi_square / denominator))


def matched_agreement(left: np.ndarray, right: np.ndarray, k: int) -> tuple[float, dict[int, int]]:
    contingency = pd.crosstab(left, right).reindex(
        index=range(k), columns=range(k), fill_value=0
    )
    rows, columns = linear_sum_assignment(-contingency.to_numpy())
    mapping = {int(column): int(row) for row, column in zip(rows, columns, strict=True)}
    remapped = np.array([mapping[int(value)] for value in right])
    return float(np.mean(left == remapped)), mapping


def evaluate_solution(
    resolution: str,
    covariance: str,
    k: int,
    features: pd.DataFrame,
    common_hourly: pd.DataFrame,
    external: pd.DataFrame,
    bootstrap_indices: list[np.ndarray],
) -> tuple[dict[str, float | int | str], pd.DataFrame, list[dict[str, float | int | str]]]:
    values = features.to_numpy(dtype=float)
    common_values = common_hourly.to_numpy(dtype=float)
    reference = fit_model(values, k, covariance, REFERENCE_SEED, N_INIT_REFERENCE)
    labels = reference.predict(values)

    seed_label_sets = [
        fit_model(values, k, covariance, seed, N_INIT_SEED).predict(values)
        for seed in SEEDS
    ]
    seed_mean, seed_sd, seed_min = pairwise_ari(seed_label_sets)
    aligned_seed_matches = []
    for seed_labels in seed_label_sets:
        _, mapping = matched_agreement(labels, seed_labels, k)
        aligned = np.array([mapping[int(value)] for value in seed_labels])
        aligned_seed_matches.append(aligned == labels)
    seed_unit_stability = np.mean(np.vstack(aligned_seed_matches), axis=0)

    bootstrap_scores = []
    aligned_bootstrap_matches = []
    for bootstrap_number, indices in enumerate(bootstrap_indices):
        model = fit_model(
            values[indices],
            k,
            covariance,
            RANDOM_SEED + bootstrap_number,
            N_INIT_BOOTSTRAP,
        )
        bootstrap_labels = model.predict(values)
        bootstrap_scores.append(adjusted_rand_score(labels, bootstrap_labels))
        _, mapping = matched_agreement(labels, bootstrap_labels, k)
        aligned = np.array([mapping[int(value)] for value in bootstrap_labels])
        aligned_bootstrap_matches.append(aligned == labels)
    bootstrap_unit_stability = np.mean(np.vstack(aligned_bootstrap_matches), axis=0)

    label_table = pd.DataFrame(
        {
            "unit": features.index.astype(str),
            "resolution": resolution,
            "covariance": covariance,
            "K": k,
            "cluster": labels,
        }
    )
    joined = label_table.merge(external, on="unit", validate="one_to_one")
    cluster_sizes = pd.Series(labels).value_counts()

    record: dict[str, float | int | str] = {
        "resolution": resolution,
        "covariance": covariance,
        "K": k,
        "n_units": len(features),
        "n_features": features.shape[1],
        "bic_within_resolution": reference.bic(values),
        "silhouette_native": silhouette_score(
            values,
            labels,
            sample_size=min(SILHOUETTE_SAMPLE, len(values)),
            random_state=REFERENCE_SEED,
        ),
        "silhouette_common_1h": silhouette_score(
            common_values,
            labels,
            sample_size=min(SILHOUETTE_SAMPLE, len(common_values)),
            random_state=REFERENCE_SEED,
        ),
        "calinski_harabasz_common_1h": calinski_harabasz_score(common_values, labels),
        "davies_bouldin_common_1h": davies_bouldin_score(common_values, labels),
        "seed_pairwise_ari_mean": seed_mean,
        "seed_pairwise_ari_sd": seed_sd,
        "seed_pairwise_ari_min": seed_min,
        "bootstrap_ari_mean": float(np.mean(bootstrap_scores)),
        "bootstrap_ari_sd": float(np.std(bootstrap_scores)),
        "bootstrap_ari_min": float(np.min(bootstrap_scores)),
        "min_cluster_n": int(cluster_sizes.min()),
        "max_cluster_share": float(cluster_sizes.max() / len(features)),
        "singleton_clusters": int((cluster_sizes == 1).sum()),
        "degenerate_solution": bool(
            (cluster_sizes.min() < 20) or (cluster_sizes.max() / len(features) > 0.90)
        ),
        "median_seed_unit_stability": float(np.median(seed_unit_stability)),
        "share_seed_unit_stability_below_0_8": float(
            np.mean(seed_unit_stability < 0.8)
        ),
        "median_bootstrap_unit_stability": float(
            np.median(bootstrap_unit_stability)
        ),
        "share_bootstrap_unit_stability_below_0_8": float(
            np.mean(bootstrap_unit_stability < 0.8)
        ),
        "lnwc_cramers_v": cramers_v(joined["cluster"], joined["lnc_grp"]),
        "converged": bool(reference.converged_),
        "iterations": int(reference.n_iter_),
    }

    interpretability_rows = []
    for metric in INTERPRETABILITY_METRICS:
        effect = epsilon_squared_by_cluster(joined, metric, k)
        record[f"epsilon_{metric}"] = effect
        interpretability_rows.append(
            {
                "resolution": resolution,
                "covariance": covariance,
                "K": k,
                "metric": metric,
                "epsilon_squared": effect,
            }
        )
    interpretability_rows.append(
        {
            "resolution": resolution,
            "covariance": covariance,
            "K": k,
            "metric": "LNWC association",
            "epsilon_squared": record["lnwc_cramers_v"],
        }
    )

    signature_metrics = [
        "total_activity",
        "direction_balance",
        "post_midnight_share",
        "deep_night_share",
        "weekend_ratio",
    ]
    signatures = (
        joined.groupby("cluster")[signature_metrics]
        .median()
        .reset_index()
        .assign(resolution=resolution, covariance=covariance, K=k)
    )
    signatures["n"] = signatures["cluster"].map(cluster_sizes)

    label_table.to_csv(
        DATA / f"labels_{resolution}_{covariance}_k{k}.csv", index=False
    )
    pd.DataFrame(
        {
            "unit": features.index.astype(str),
            "reference_cluster": labels,
            "seed_assignment_stability": seed_unit_stability,
            "bootstrap_assignment_stability": bootstrap_unit_stability,
        }
    ).to_csv(
        DATA / f"unit_stability_{resolution}_{covariance}_k{k}.csv", index=False
    )
    return record, signatures, interpretability_rows


def make_stability_dashboard(comparison: pd.DataFrame) -> None:
    subset = comparison.loc[comparison["covariance"] == "diag"].copy()
    long = subset.melt(
        id_vars=["resolution", "K"],
        value_vars=[
            "silhouette_common_1h",
            "seed_pairwise_ari_mean",
            "bootstrap_ari_mean",
        ],
        var_name="metric",
        value_name="value",
    )
    labels = {
        "silhouette_common_1h": "Silhouette on common 1h space",
        "seed_pairwise_ari_mean": "Across-seed ARI",
        "bootstrap_ari_mean": "Bootstrap ARI",
    }
    long["metric"] = long["metric"].map(labels)
    figure, axes = plt.subplots(1, 3, figsize=(17, 5))
    for axis, metric in zip(axes, labels.values(), strict=True):
        sns.barplot(
            data=long.loc[long["metric"] == metric],
            x="K",
            y="value",
            hue="resolution",
            palette={"15min": "#500778", "1h": "#2F6B4F"},
            ax=axis,
        )
        axis.set_title(metric)
        axis.set_ylim(min(-0.1, long["value"].min() - 0.05), 1.0)
        axis.set_ylabel("")
        axis.legend(frameon=False)
    plt.suptitle("Matched-diagonal GMM stability comparison", y=1.03)
    plt.tight_layout()
    plt.savefig(FIGURES / "stability_dashboard.png", dpi=220, bbox_inches="tight")
    plt.close()


def make_interpretability_dashboard(interpretability: pd.DataFrame) -> None:
    subset = interpretability.loc[
        (interpretability["covariance"] == "diag")
        & (interpretability["K"] == 4)
    ].copy()
    plt.figure(figsize=(12, 6))
    sns.barplot(
        data=subset,
        x="metric",
        y="epsilon_squared",
        hue="resolution",
        palette={"15min": "#500778", "1h": "#2F6B4F"},
    )
    plt.title("K=4 interpretability comparison (same post-hoc metrics)")
    plt.ylabel("Epsilon squared; LNWC row reports Cramér's V")
    plt.xlabel("")
    plt.xticks(rotation=25, ha="right")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(
        FIGURES / "interpretability_dashboard.png", dpi=220, bbox_inches="tight"
    )
    plt.close()


def plot_k4_profiles(
    feature_sets: dict[str, pd.DataFrame],
    signatures: pd.DataFrame,
) -> None:
    figure, axes = plt.subplots(4, 2, figsize=(17, 12), sharex=False)
    for column, resolution in enumerate(["15min", "1h"]):
        features = feature_sets[resolution]
        labels = pd.read_csv(DATA / f"labels_{resolution}_diag_k4.csv").set_index("unit")
        label_series = labels["cluster"].reindex(features.index)
        sig = signatures.loc[
            (signatures["resolution"] == resolution)
            & (signatures["covariance"] == "diag")
            & (signatures["K"] == 4)
        ].sort_values("total_activity")
        ordered_clusters = sig["cluster"].astype(int).tolist()
        for row, cluster in enumerate(ordered_clusters):
            axis = axes[row, column]
            members = features.loc[label_series == cluster]
            for direction, colour in [("boardings", "#2F6B4F"), ("alightings", "#9A3D3D")]:
                columns = [name for name in features.columns if name.startswith(direction + "_")]
                profile = members[columns].median(axis=0).to_numpy()
                axis.plot(profile, color=colour, linewidth=1.6, label=direction)
            activity = float(sig.loc[sig["cluster"] == cluster, "total_activity"].iloc[0])
            axis.set_title(
                f"{resolution} C{cluster} (n={len(members)}, median activity={activity:,.0f})"
            )
            axis.set_ylabel("Median share")
            if row == 3:
                axis.set_xlabel("Concatenated Weekday / Saturday / Sunday bins")
            if row == 0:
                axis.legend(frameon=False)
    plt.suptitle("Matched diagonal GMM, K=4: profiles ordered by median activity", y=1.01)
    plt.tight_layout()
    plt.savefig(FIGURES / "k4_diag_profiles.png", dpi=220, bbox_inches="tight")
    plt.close()


def main() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    required = [SOURCE_LONG, EXISTING_X15, EXISTING_X60, CONTEXT_METRICS, LNWC_LINK]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")

    print("Building 15-minute and 1-hour matrices from the same source...")
    long = pd.read_parquet(SOURCE_LONG)
    x15, meta15 = build_features(long, 15)
    x60, meta60 = build_features(long, 60)
    if not x15.index.equals(x60.index):
        raise AssertionError("15-minute and 1-hour unit universes differ")
    if not np.allclose(meta15["total_activity"], meta60["total_activity"], atol=1e-8):
        raise AssertionError("Activity totals differ after aggregation")

    audit = {
        "source_rows": len(long),
        "source_unique_lsoa": int(long["lsoa"].nunique()),
        "analysis_lsoa": len(x15),
        "x15_shape": list(x15.shape),
        "x60_shape": list(x60.shape),
        "total_activity_max_abs_difference": float(
            np.abs(meta15["total_activity"] - meta60["total_activity"]).max()
        ),
        "x15_existing_max_abs_difference": aligned_max_difference(x15, EXISTING_X15),
        "x60_existing_max_abs_difference": aligned_max_difference(x60, EXISTING_X60),
    }
    x15.to_parquet(DATA / "X_bus_15min_same_source.parquet")
    x60.to_parquet(DATA / "X_bus_1h_same_source.parquet")
    meta15.to_csv(DATA / "bus_meta_same_source.csv")

    context = pd.read_csv(CONTEXT_METRICS).rename(columns={"lsoa": "unit"})
    context["unit"] = context["unit"].astype(str)
    lnwc = pd.read_csv(LNWC_LINK)[["lsoa21cd", "lnc_grp"]].rename(
        columns={"lsoa21cd": "unit"}
    )
    external = context[
        ["unit"]
        + INTERPRETABILITY_METRICS
        + ["total_activity"]
    ].merge(lnwc, on="unit", validate="one_to_one")
    external = external.loc[external["unit"].isin(x15.index)].copy()
    if len(external) != len(x15):
        raise AssertionError("External metrics do not cover the fair-comparison universe")

    rng = np.random.default_rng(RANDOM_SEED)
    bootstrap_indices = [
        rng.choice(len(x15), len(x15), replace=True) for _ in range(N_BOOTSTRAPS)
    ]
    feature_sets = {"15min": x15, "1h": x60}
    model_rows = []
    signature_frames = []
    interpretability_rows = []

    for covariance in COVARIANCES:
        for k in K_VALUES:
            for resolution in ["15min", "1h"]:
                print(f"Fitting {resolution}, covariance={covariance}, K={k}...")
                record, signatures, interpretation = evaluate_solution(
                    resolution,
                    covariance,
                    k,
                    feature_sets[resolution],
                    x60,
                    external,
                    bootstrap_indices,
                )
                model_rows.append(record)
                signature_frames.append(signatures)
                interpretability_rows.extend(interpretation)

    comparison = pd.DataFrame(model_rows)
    signatures = pd.concat(signature_frames, ignore_index=True)
    interpretability = pd.DataFrame(interpretability_rows)
    comparison.to_csv(DATA / "model_comparison.csv", index=False)
    signatures.to_csv(DATA / "cluster_signatures.csv", index=False)
    interpretability.to_csv(DATA / "interpretability_metrics.csv", index=False)

    cross_rows = []
    contingency_rows = []
    for covariance in COVARIANCES:
        for k in K_VALUES:
            left = pd.read_csv(DATA / f"labels_15min_{covariance}_k{k}.csv")
            right = pd.read_csv(DATA / f"labels_1h_{covariance}_k{k}.csv")
            merged = left[["unit", "cluster"]].rename(
                columns={"cluster": "cluster_15min"}
            ).merge(
                right[["unit", "cluster"]].rename(columns={"cluster": "cluster_1h"}),
                on="unit",
                validate="one_to_one",
            )
            agreement, mapping = matched_agreement(
                merged["cluster_15min"].to_numpy(),
                merged["cluster_1h"].to_numpy(),
                k,
            )
            cross_rows.append(
                {
                    "covariance": covariance,
                    "K": k,
                    "adjusted_rand_index": adjusted_rand_score(
                        merged["cluster_15min"], merged["cluster_1h"]
                    ),
                    "normalized_mutual_information": normalized_mutual_info_score(
                        merged["cluster_15min"], merged["cluster_1h"]
                    ),
                    "hungarian_matched_agreement": agreement,
                    "one_hour_to_15min_mapping": json.dumps(mapping, sort_keys=True),
                }
            )
            contingency = pd.crosstab(
                merged["cluster_15min"], merged["cluster_1h"]
            ).reindex(index=range(k), columns=range(k), fill_value=0)
            for cluster_15 in range(k):
                for cluster_60 in range(k):
                    contingency_rows.append(
                        {
                            "covariance": covariance,
                            "K": k,
                            "cluster_15min": cluster_15,
                            "cluster_1h": cluster_60,
                            "n": int(contingency.loc[cluster_15, cluster_60]),
                        }
                    )
    cross = pd.DataFrame(cross_rows)
    cross.to_csv(DATA / "cross_resolution_agreement.csv", index=False)
    pd.DataFrame(contingency_rows).to_csv(
        DATA / "cross_resolution_contingency_long.csv", index=False
    )

    audit_rows = [
        {"metric": key, "value": json.dumps(value) if isinstance(value, list) else value}
        for key, value in audit.items()
    ]
    pd.DataFrame(audit_rows).to_csv(DATA / "data_audit.csv", index=False)
    make_stability_dashboard(comparison)
    make_interpretability_dashboard(interpretability)
    plot_k4_profiles(feature_sets, signatures)

    diag_k4 = comparison.loc[
        (comparison["covariance"] == "diag") & (comparison["K"] == 4)
    ].set_index("resolution")
    cross_diag_k4 = cross.loc[
        (cross["covariance"] == "diag") & (cross["K"] == 4)
    ].iloc[0]
    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Bus 15-minute vs 1-hour fair stability validation",
        "",
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite / experiment-agent",
        "- Origin Mode: run + validate",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "- Version Label: bus_resolution_fair_validation_v1",
        "",
        "## Fairness audit",
        "",
        f"- Same-source analysis universe: {len(x15):,} LSOAs.",
        f"- Feature shapes: 15-minute {x15.shape}; 1-hour {x60.shape}.",
        f"- Maximum total-activity difference after aggregation: "
        f"{audit['total_activity_max_abs_difference']:.3e}.",
        f"- Rebuilt-vs-existing maximum feature difference: 15-minute "
        f"{audit['x15_existing_max_abs_difference']:.3e}; 1-hour "
        f"{audit['x60_existing_max_abs_difference']:.3e}.",
        "",
        "## Matched diagonal K=4",
        "",
        f"- Common-space silhouette: 15-minute labels "
        f"{diag_k4.loc['15min', 'silhouette_common_1h']:.3f}; 1-hour labels "
        f"{diag_k4.loc['1h', 'silhouette_common_1h']:.3f}.",
        f"- Across-seed ARI: 15-minute "
        f"{diag_k4.loc['15min', 'seed_pairwise_ari_mean']:.3f}; 1-hour "
        f"{diag_k4.loc['1h', 'seed_pairwise_ari_mean']:.3f}.",
        f"- Bootstrap ARI: 15-minute "
        f"{diag_k4.loc['15min', 'bootstrap_ari_mean']:.3f}; 1-hour "
        f"{diag_k4.loc['1h', 'bootstrap_ari_mean']:.3f}.",
        f"- LSOAs below 0.8 bootstrap assignment stability: 15-minute "
        f"{diag_k4.loc['15min', 'share_bootstrap_unit_stability_below_0_8']:.1%}; "
        f"1-hour {diag_k4.loc['1h', 'share_bootstrap_unit_stability_below_0_8']:.1%}.",
        f"- Cross-resolution ARI={cross_diag_k4['adjusted_rand_index']:.3f}; "
        f"matched agreement={cross_diag_k4['hungarian_matched_agreement']:.1%}.",
        f"- LNWC Cramér's V: 15-minute "
        f"{diag_k4.loc['15min', 'lnwc_cramers_v']:.3f}; 1-hour "
        f"{diag_k4.loc['1h', 'lnwc_cramers_v']:.3f}.",
        "",
        "## Interpretation",
        "",
        "The fair comparison separates three questions: whether the labels are internally "
        "separated on a common feature space, whether assignments survive seed/bootstrap "
        "perturbation, and whether the resulting groups carry external substantive meaning. "
        "A resolution can be more interpretable while being less stable.",
        "",
        "The tied-covariance sensitivity is treated as invalid when it produces a "
        "cluster smaller than 20 LSOAs or a dominant cluster above 90%. Such solutions "
        "can show artificially high silhouette values while carrying little typological "
        "information.",
        "",
        "BIC is reported only within each resolution/covariance setting and is not compared "
        "across the 288- and 72-dimensional matrices.",
        "",
        "## Decision boundary",
        "",
        "Promotion of the 15-minute K=4 solution should require acceptable common-space "
        "separation and bootstrap stability in addition to stronger LNWC or behavioural "
        "contrasts. External interpretability alone is not sufficient because unstable "
        "LSOA assignments can produce a persuasive but non-reproducible typology.",
    ]
    (REPORT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    manifest = pd.DataFrame(
        [
            {
                "role": path.stem,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in required
        ]
    )
    manifest.to_csv(DATA / "input_manifest.csv", index=False)
    metadata = {
        "generated_utc": generated,
        "duration_seconds": time.time() - START,
        "command": "py -3 src/run_validation.py",
        "python": sys.version,
        "platform": platform.platform(),
        "parameters": {
            "K_values": K_VALUES,
            "covariances": COVARIANCES,
            "seeds": SEEDS,
            "bootstraps": N_BOOTSTRAPS,
            "bootstrap_seed": RANDOM_SEED,
            "reference_seed": REFERENCE_SEED,
        },
    }
    (REPORT / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"Completed in {metadata['duration_seconds']:.1f}s. Outputs: {OUT}")


if __name__ == "__main__":
    main()
