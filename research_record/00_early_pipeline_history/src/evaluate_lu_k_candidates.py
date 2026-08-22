from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture


PROJECT_ROOT_RELATIVE: Path | None = None
# If this notebook/script is moved outside the FYP folder, set the line above.
# Example when the notebook folder sits next to FYP:
# PROJECT_ROOT_RELATIVE = Path("../FYP")


def find_project_root(start: Path | None = None) -> Path:
    """Find the FYP project root by walking upward from a local path."""
    if start is None:
        try:
            start = Path(__file__).resolve()
        except NameError:
            start = Path.cwd().resolve()

    if start.is_file():
        start = start.parent

    for candidate in [start, *start.parents]:
        if (candidate / "PROJECT_CONTEXT.md").exists():
            return candidate

    raise FileNotFoundError(
        "Could not find PROJECT_CONTEXT.md. Run this from inside the FYP project folder."
    )


def resolve_project_root(project_root_relative: Path | None = None) -> Path:
    """Resolve the project root, optionally from a user-provided relative path.

    In JupyterLab, relative paths are resolved from the current kernel working
    directory. Run `Path.cwd()` in a cell if you need to confirm that location.
    """
    if project_root_relative is not None:
        candidate = (Path.cwd() / project_root_relative).resolve()
        if not (candidate / "PROJECT_CONTEXT.md").exists():
            raise FileNotFoundError(
                f"PROJECT_ROOT_RELATIVE resolved to {candidate}, but PROJECT_CONTEXT.md "
                "was not found there. Adjust PROJECT_ROOT_RELATIVE in the config cell."
            )
        return candidate

    return find_project_root()


ROOT = resolve_project_root(PROJECT_ROOT_RELATIVE)
INPUT_DIR = ROOT / "outputs" / "rq1_trial_numbat_lu_only"
OUTPUT_DIR = INPUT_DIR / "candidate_evaluation"

X_PATH = INPUT_DIR / "X_rail_LU_TWT_trial.parquet"
META_PATH = INPUT_DIR / "rail_LU_TWT_meta_trial.csv"
GMM_DIAGNOSTICS_PATH = INPUT_DIR / "rail_LU_TWT_gmm_k_diagnostics.csv"
KMEANS_DIAGNOSTICS_PATH = INPUT_DIR / "rail_LU_TWT_kmeans_k_diagnostics.csv"

CANDIDATE_KS = [3, 7]
RANDOM_STATE = 42


def cluster_sizes(labels: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(labels, return_counts=True)
    return {str(int(value)): int(count) for value, count in zip(values, counts, strict=True)}


def posterior_entropy(posterior: np.ndarray) -> np.ndarray:
    clipped = np.clip(posterior, 1e-12, 1.0)
    return -(posterior * np.log(clipped)).sum(axis=1)


def parse_feature_table(X: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    rows = []
    for nlc, label in zip(X.index.astype(str), labels, strict=True):
        for feature, value in X.loc[nlc].items():
            day_type, direction, bin_label = feature.split("_", 2)
            rows.append(
                {
                    "NLC": nlc,
                    "cluster": int(label),
                    "day_type": day_type,
                    "direction": direction,
                    "bin_label": bin_label,
                    "share": float(value),
                }
            )
    return pd.DataFrame(rows)


def bin_start_minutes(bin_label: str) -> int:
    hour = int(bin_label[:2])
    minute = int(bin_label[2:4])
    total = hour * 60 + minute
    if total < 18 * 60:
        total += 24 * 60
    return total


def format_night_axis(ax: plt.Axes) -> None:
    ax.set_xlim(18 * 60, 25 * 60)
    ax.set_xticks([18 * 60, 21 * 60, 24 * 60, 25 * 60])
    ax.set_xticklabels(["18:00", "21:00", "00:00", "01:00"])
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def fit_gmm(X: pd.DataFrame, k: int) -> tuple[GaussianMixture, np.ndarray, np.ndarray]:
    model = GaussianMixture(
        n_components=k,
        covariance_type="full",
        n_init=50,
        tol=1e-6,
        max_iter=300,
        random_state=RANDOM_STATE,
    )
    labels = model.fit_predict(X)
    posterior = model.predict_proba(X)
    return model, labels, posterior


def plot_k_diagnostics(gmm_diag: pd.DataFrame, kmeans_diag: pd.DataFrame) -> None:
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(9, 9), sharex=True)

    specs = [
        ("silhouette", "Silhouette score", "higher is better"),
        ("calinski_harabasz", "Calinski-Harabasz index", "higher is better"),
        ("davies_bouldin", "Davies-Bouldin index", "lower is better"),
    ]

    for ax, (column, title, note) in zip(axes, specs, strict=True):
        ax.plot(gmm_diag["k"], gmm_diag[column], marker="o", label="GMM")
        ax.plot(kmeans_diag["k"], kmeans_diag[column], marker="s", label="KMeans")
        for k in CANDIDATE_KS:
            ax.axvline(k, color="#999999", linestyle="--", linewidth=0.8)
        ax.set_ylabel(title)
        ax.set_title(f"{title} ({note})")
        ax.grid(color="#eeeeee", linewidth=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    axes[-1].set_xlabel("Number of clusters (K)")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "k_diagnostics_gmm_kmeans.png", dpi=200)
    plt.close(fig)


def plot_cluster_profiles(X: pd.DataFrame, labels: np.ndarray, k: int) -> pd.DataFrame:
    long_df = parse_feature_table(X, labels)
    long_df["plot_minute"] = long_df["bin_label"].apply(bin_start_minutes)

    profile = (
        long_df.groupby(["cluster", "direction", "bin_label", "plot_minute"], as_index=False)
        .agg(
            median_share=("share", "median"),
            mean_share=("share", "mean"),
            p10_share=("share", lambda values: values.quantile(0.10)),
            p90_share=("share", lambda values: values.quantile(0.90)),
        )
        .sort_values(["cluster", "direction", "plot_minute"])
    )

    profile.to_csv(OUTPUT_DIR / f"k{k}_cluster_temporal_profiles.csv", index=False)

    clusters = sorted(profile["cluster"].unique())
    fig, axes = plt.subplots(
        nrows=len(clusters),
        ncols=1,
        figsize=(10, max(2.6 * len(clusters), 4)),
        sharex=True,
        sharey=False,
    )
    if len(clusters) == 1:
        axes = [axes]

    for ax, cluster in zip(axes, clusters, strict=True):
        subset = profile[profile["cluster"] == cluster]
        for direction, color in [("entry", "#2F6B4F"), ("exit", "#9A3D3D")]:
            line = subset[subset["direction"] == direction]
            ax.plot(
                line["plot_minute"],
                line["median_share"],
                marker="o",
                markersize=3,
                linewidth=1.6,
                color=color,
                label=direction,
            )
            ax.fill_between(
                line["plot_minute"].to_numpy(dtype=float),
                line["p10_share"].to_numpy(dtype=float),
                line["p90_share"].to_numpy(dtype=float),
                color=color,
                alpha=0.12,
                linewidth=0,
            )
        ax.set_title(f"K={k}, cluster {cluster}")
        ax.set_ylabel("Feature share")
        format_night_axis(ax)

    axes[0].legend(loc="upper right")
    axes[-1].set_xlabel("Time")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"k{k}_entry_exit_temporal_profiles.png", dpi=200)
    plt.close(fig)

    asymmetry = profile.pivot_table(
        index=["cluster", "bin_label", "plot_minute"],
        columns="direction",
        values="median_share",
        aggfunc="first",
    ).reset_index()
    asymmetry["entry_minus_exit"] = asymmetry.get("entry", 0.0) - asymmetry.get("exit", 0.0)
    asymmetry.to_csv(OUTPUT_DIR / f"k{k}_entry_exit_asymmetry.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    for cluster in clusters:
        line = asymmetry[asymmetry["cluster"] == cluster].sort_values("plot_minute")
        ax.plot(
            line["plot_minute"],
            line["entry_minus_exit"],
            marker="o",
            markersize=3,
            linewidth=1.4,
            label=f"cluster {cluster}",
        )
    ax.axhline(0, color="#333333", linewidth=0.8)
    format_night_axis(ax)
    ax.set_title(f"K={k}, entry-exit median profile asymmetry")
    ax.set_xlabel("Time")
    ax.set_ylabel("Entry share minus exit share")
    ax.legend(ncols=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"k{k}_entry_exit_asymmetry.png", dpi=200)
    plt.close(fig)

    return profile


def plot_pca(X: pd.DataFrame, labels_by_k: dict[int, np.ndarray]) -> None:
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(X)

    for k, labels in labels_by_k.items():
        fig, ax = plt.subplots(figsize=(7, 6))
        scatter = ax.scatter(
            coords[:, 0],
            coords[:, 1],
            c=labels,
            cmap="tab10",
            s=32,
            alpha=0.85,
            edgecolor="white",
            linewidth=0.3,
        )
        ax.set_title(f"PCA view of LU-only TWT profiles, K={k}")
        ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
        ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
        ax.grid(color="#eeeeee", linewidth=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        legend = ax.legend(*scatter.legend_elements(), title="Cluster", loc="best")
        ax.add_artist(legend)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"k{k}_pca_clusters.png", dpi=200)
        plt.close(fig)

    pca_table = pd.DataFrame(
        {
            "NLC": X.index.astype(str),
            "pc1": coords[:, 0],
            "pc2": coords[:, 1],
        }
    )
    for k, labels in labels_by_k.items():
        pca_table[f"k{k}_cluster"] = labels
    pca_table.to_csv(OUTPUT_DIR / "candidate_pca_coordinates.csv", index=False)


def build_cluster_outputs(
    X: pd.DataFrame,
    meta: pd.DataFrame,
    model: GaussianMixture,
    labels: np.ndarray,
    posterior: np.ndarray,
    k: int,
) -> None:
    entropy = posterior_entropy(posterior)
    max_posterior = posterior.max(axis=1)

    label_df = meta.copy()
    label_df["cluster"] = labels
    label_df["max_posterior"] = max_posterior
    label_df["posterior_entropy"] = entropy
    label_df.to_csv(OUTPUT_DIR / f"k{k}_labels_with_posterior.csv", index=False)

    summary = (
        label_df.groupby("cluster", as_index=False)
        .agg(
            station_count=("NLC", "count"),
            total_activity_sum=("total_rail_activity", "sum"),
            total_activity_median=("total_rail_activity", "median"),
            total_activity_mean=("total_rail_activity", "mean"),
            mean_max_posterior=("max_posterior", "mean"),
            min_max_posterior=("max_posterior", "min"),
            mean_entropy=("posterior_entropy", "mean"),
        )
        .sort_values("cluster")
    )
    summary.to_csv(OUTPUT_DIR / f"k{k}_cluster_summary.csv", index=False)

    representative_rows = []
    X_values = X.to_numpy()
    for cluster in sorted(np.unique(labels)):
        cluster_idx = np.where(labels == cluster)[0]
        center = model.means_[cluster]
        distances = np.linalg.norm(X_values[cluster_idx] - center, axis=1)
        order = np.lexsort((-max_posterior[cluster_idx], distances))

        for rank, local_pos in enumerate(order[:10], start=1):
            row_pos = cluster_idx[local_pos]
            meta_row = meta.iloc[row_pos]
            representative_rows.append(
                {
                    "cluster": int(cluster),
                    "rank": rank,
                    "NLC": meta_row["NLC"],
                    "ASC": meta_row["ASC"],
                    "Station": meta_row["Station"],
                    "Fare Zone": meta_row["Fare Zone"],
                    "mode_label": meta_row["mode_label"],
                    "total_rail_activity": meta_row["total_rail_activity"],
                    "distance_to_gmm_mean": float(distances[local_pos]),
                    "max_posterior": float(max_posterior[row_pos]),
                    "posterior_entropy": float(entropy[row_pos]),
                }
            )

    representative = pd.DataFrame(representative_rows)
    representative.to_csv(OUTPUT_DIR / f"k{k}_representative_stations.csv", index=False)

    model_summary = {
        "k": k,
        "bic": float(model.bic(X)),
        "aic": float(model.aic(X)),
        "log_likelihood": float(model.score(X)),
        "converged": bool(model.converged_),
        "n_iter": int(model.n_iter_),
        "cluster_sizes": cluster_sizes(labels),
        "mean_max_posterior": float(max_posterior.mean()),
        "min_max_posterior": float(max_posterior.min()),
        "mean_entropy": float(entropy.mean()),
    }
    with open(OUTPUT_DIR / f"k{k}_model_summary.json", "w", encoding="utf-8") as handle:
        json.dump(model_summary, handle, indent=2)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    X = pd.read_parquet(X_PATH)
    X.index = X.index.astype(str)
    meta = pd.read_csv(META_PATH, dtype={"NLC": "string", "ASC": "string"})
    meta["NLC"] = meta["NLC"].astype(str)
    meta = meta.set_index("NLC").loc[X.index].reset_index()

    gmm_diag = pd.read_csv(GMM_DIAGNOSTICS_PATH)
    kmeans_diag = pd.read_csv(KMEANS_DIAGNOSTICS_PATH)

    print("Loaded X:", X.shape)
    print("Loaded meta:", meta.shape)
    print("Candidate Ks:", CANDIDATE_KS)

    plot_k_diagnostics(gmm_diag, kmeans_diag)

    labels_by_k = {}
    comparison_rows = []

    for k in CANDIDATE_KS:
        print(f"Fitting GMM candidate K={k}...")
        model, labels, posterior = fit_gmm(X, k)
        labels_by_k[k] = labels

        build_cluster_outputs(X, meta, model, labels, posterior, k)
        plot_cluster_profiles(X, labels, k)

        entropy = posterior_entropy(posterior)
        comparison_rows.append(
            {
                "k": k,
                "bic": model.bic(X),
                "aic": model.aic(X),
                "log_likelihood": model.score(X),
                "converged": model.converged_,
                "n_iter": model.n_iter_,
                "mean_max_posterior": posterior.max(axis=1).mean(),
                "min_max_posterior": posterior.max(axis=1).min(),
                "mean_entropy": entropy.mean(),
                "cluster_sizes": json.dumps(cluster_sizes(labels)),
            }
        )

    plot_pca(X, labels_by_k)

    comparison = pd.DataFrame(comparison_rows)
    comparison.to_csv(OUTPUT_DIR / "candidate_model_comparison.csv", index=False)

    readme = OUTPUT_DIR / "README_candidate_evaluation.md"
    readme.write_text(
        "\n".join(
            [
                "# LU-only TWT Candidate K Evaluation",
                "",
                "This folder compares GMM candidate K values for the LU-only TWT trial.",
                "",
                "Candidate K values:",
                ", ".join(str(k) for k in CANDIDATE_KS),
                "",
                "Use these outputs to assess profile interpretability and assignment stability.",
                "Do not treat the script as automatically selecting the final K.",
                "",
                "Key files:",
                "- k_diagnostics_gmm_kmeans.png",
                "- candidate_model_comparison.csv",
                "- k*_cluster_summary.csv",
                "- k*_representative_stations.csv",
                "- k*_entry_exit_temporal_profiles.png",
                "- k*_entry_exit_asymmetry.png",
                "- k*_pca_clusters.png",
            ]
        ),
        encoding="utf-8",
    )

    print("Saved candidate evaluation outputs to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
