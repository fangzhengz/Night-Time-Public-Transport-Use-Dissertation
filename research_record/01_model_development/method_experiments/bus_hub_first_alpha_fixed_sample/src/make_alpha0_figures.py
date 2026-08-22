from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FEATURES = OUT / "features"
LABELS = OUT / "labels"
DIAGNOSTICS = OUT / "diagnostics"
FIGURES = OUT / "figures"

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
HOURS = list(range(1080, 1800, 60))
HOUR_LABELS = ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"]
PROFILE_K = range(2, 9)
SELECTED_K = 3
SELECTED_NAMES = {
    0: "High activity / intermediate late",
    1: "Late-persistent",
    2: "Low activity / early-fading",
}
COLORS = {
    "boardings": "#356D9A",
    "alightings": "#D8752D",
}


def read_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    x = pd.read_parquet(FEATURES / "X_bus_fullweek_alpha0_fixed_sample.parquet")
    x.index = x.index.astype(str)
    grid = pd.read_csv(DIAGNOSTICS / "alpha0_bic_grid.csv")
    kdiag = pd.read_csv(DIAGNOSTICS / "alpha0_full_kdiag_prebootstrap.csv")
    bootstrap = pd.read_csv(DIAGNOSTICS / "alpha0_vs_alpha5_bootstrap_summary.csv")
    return x, grid, kdiag, bootstrap


def build_profiles(x: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    profile_rows: list[dict[str, object]] = []
    size_rows: list[dict[str, object]] = []
    for k in PROFILE_K:
        label_path = LABELS / f"alpha0_full_k{k}_labels.csv"
        labels = pd.read_csv(label_path).set_index("unit")["cluster"]
        labels.index = labels.index.astype(str)
        labels = labels.reindex(x.index)
        if labels.isna().any():
            raise ValueError(f"{label_path.name} is missing labels for the feature matrix")
        labels = labels.astype(int)
        for cluster in sorted(labels.unique()):
            mask = labels.eq(cluster)
            means = x.loc[mask].mean(axis=0)
            size_rows.append(
                {
                    "K": k,
                    "cluster": int(cluster),
                    "n": int(mask.sum()),
                    "share": float(mask.mean()),
                }
            )
            for feature, value in means.items():
                stem, hour = feature.rsplit("_", 1)
                direction, day_type = stem.split("_", 1)
                profile_rows.append(
                    {
                        "K": k,
                        "cluster": int(cluster),
                        "day_type": day_type,
                        "direction": direction,
                        "hour_bin": int(hour),
                        "mean_share": float(value),
                    }
                )
    profiles = pd.DataFrame(profile_rows)
    sizes = pd.DataFrame(size_rows)
    profiles.to_csv(DIAGNOSTICS / "alpha0_cluster_profiles_k2_k8.csv", index=False)
    sizes.to_csv(DIAGNOSTICS / "alpha0_cluster_sizes_k2_k8.csv", index=False)
    return profiles, sizes


def style_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D8DEE5", linewidth=0.7, alpha=0.8)


def plot_bic_grid(grid: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 5.5))
    palette = {
        "spherical": "#7A5195",
        "diag": "#EF5675",
        "tied": "#2F9E8F",
        "full": "#356D9A",
    }
    for covariance in ["spherical", "diag", "tied", "full"]:
        sub = grid.loc[grid["covariance"].eq(covariance)].sort_values("K")
        ax.plot(
            sub["K"],
            sub["BIC"],
            marker="o",
            markersize=4.5,
            linewidth=1.8,
            color=palette[covariance],
            label=covariance,
        )
    best = grid.loc[grid["BIC"].idxmin()]
    ax.scatter(best["K"], best["BIC"], marker="*", s=180, color="#1B1B1B", zorder=5)
    ax.annotate(
        f"global minimum: {best['covariance']}, K={int(best['K'])}",
        (best["K"], best["BIC"]),
        xytext=(28, 36),
        textcoords="offset points",
        fontsize=9,
        arrowprops={"arrowstyle": "->", "color": "#4A4A4A"},
    )
    ax.axvline(SELECTED_K, color="#1B1B1B", linestyle="--", linewidth=1, alpha=0.6)
    ax.set(
        xlabel="Number of clusters (K)",
        ylabel="BIC (lower is better)",
        title="Bus full-week GMM model grid (alpha=0)",
    )
    ax.set_xticks(sorted(grid["K"].unique()))
    style_axis(ax)
    ax.legend(title="Covariance", frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGURES / "alpha0_bic_grid.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_k_diagnostics(kdiag: pd.DataFrame, bootstrap: pd.DataFrame) -> None:
    merged = kdiag.merge(bootstrap, on="K", how="left")
    merged["delta_bic"] = merged["BIC"] - merged["BIC"].min()
    panels = [
        ("delta_bic", "Full-covariance BIC difference", "lower is better"),
        ("silhouette", "Silhouette", "higher is better"),
        ("davies_bouldin", "Davies-Bouldin index", "lower is better"),
        ("min_cluster_share", "Smallest cluster share", "guard against tiny clusters"),
        ("alpha0_bootstrap_ari_mean", "Bootstrap ARI", "global recovery; mean +/- SD"),
        ("alpha0_min_cluster_jaccard_mean", "Weakest-cluster Jaccard", "small-cluster recovery; mean"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(14.2, 8.2), sharex=True)
    for ax, (column, title, subtitle) in zip(axes.flat, panels):
        valid = merged[["K", column]].dropna()
        ax.plot(valid["K"], valid[column], color="#356D9A", marker="o", linewidth=1.8)
        if column == "alpha0_bootstrap_ari_mean":
            err = merged.loc[valid.index, "alpha0_bootstrap_ari_sd"].fillna(0)
            ax.fill_between(
                valid["K"].to_numpy(),
                (valid[column] - err).to_numpy(),
                (valid[column] + err).to_numpy(),
                color="#356D9A",
                alpha=0.16,
                linewidth=0,
            )
        ax.axvline(SELECTED_K, color="#C23B23", linestyle="--", linewidth=1.2)
        ax.set_title(f"{title}\n{subtitle}", fontsize=10.5)
        ax.set_xticks(range(2, 13))
        style_axis(ax)
    axes[0, 0].scatter([SELECTED_K], [0], marker="*", s=120, color="#C23B23", zorder=5)
    axes[1, 0].yaxis.set_major_formatter(lambda value, _pos: f"{value:.0%}")
    for ax in axes[1, :]:
        ax.set_xlabel("K")
    fig.suptitle(
        "Bus full-week K-selection diagnostics (alpha=0, full covariance)\n"
        "Red dashed line marks the selected candidate K=3; no single panel is treated as decisive",
        fontsize=14,
        y=1.01,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "alpha0_k_selection_diagnostics.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_profiles(profiles: pd.DataFrame, sizes: pd.DataFrame) -> None:
    for k in PROFILE_K:
        sub = profiles.loc[profiles["K"].eq(k)]
        size_map = sizes.loc[sizes["K"].eq(k)].set_index("cluster")["n"]
        fig, axes = plt.subplots(
            k,
            3,
            figsize=(13.5, max(5.0, 2.15 * k)),
            sharex=True,
            sharey=True,
            squeeze=False,
        )
        for cluster in range(k):
            for column, day_type in enumerate(DAY_TYPES):
                ax = axes[cluster, column]
                cell = sub.loc[sub["cluster"].eq(cluster) & sub["day_type"].eq(day_type)]
                for direction in DIRECTIONS:
                    line = cell.loc[cell["direction"].eq(direction)].sort_values("hour_bin")
                    linestyle = "-" if direction == "boardings" else "--"
                    marker = "o" if direction == "boardings" else "s"
                    ax.plot(
                        range(12),
                        line["mean_share"],
                        color=COLORS[direction],
                        linestyle=linestyle,
                        marker=marker,
                        markersize=3,
                        linewidth=1.8,
                        label=direction.capitalize(),
                    )
                ax.axvline(5.5, color="#68737D", linestyle=":", linewidth=1, alpha=0.8)
                style_axis(ax)
                if cluster == 0:
                    ax.set_title(day_type, fontsize=11)
                if column == 0:
                    if k == SELECTED_K:
                        name = SELECTED_NAMES[cluster].replace(" / ", " /\n")
                        label = f"C{cluster}\n{name}\nn={int(size_map.loc[cluster]):,}"
                    else:
                        label = f"C{cluster} (n={int(size_map.loc[cluster]):,})"
                    ax.set_ylabel(
                        label,
                        fontsize=9.5,
                        rotation=0,
                        ha="right",
                        va="center",
                        labelpad=14,
                    )
                if cluster == k - 1:
                    ax.set_xticks(range(12), HOUR_LABELS, rotation=45)
                    ax.set_xlabel("Hour")
        handles, labels = axes[0, 2].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(0.985, 0.985), frameon=False)
        fig.suptitle(
            f"Bus full-week mean temporal profiles (alpha=0, K={k})\n"
            "Each line is the mean share of that direction's full-week total; dotted divider marks midnight",
            fontsize=13.5,
            y=1.005,
        )
        left = 0.16 if k == SELECTED_K else 0.08
        fig.tight_layout(rect=(left, 0, 0.97, 0.97))
        filename = "alpha0_k3_temporal_profiles.png" if k == SELECTED_K else f"alpha0_profiles_k{k}.png"
        fig.savefig(FIGURES / filename, dpi=200, bbox_inches="tight")
        plt.close(fig)


def validate_outputs(profiles: pd.DataFrame, sizes: pd.DataFrame) -> None:
    selected = profiles.loc[profiles["K"].eq(SELECTED_K)]
    expected_rows = SELECTED_K * len(DAY_TYPES) * len(DIRECTIONS) * len(HOURS)
    if len(selected) != expected_rows:
        raise ValueError(f"K=3 profile has {len(selected)} rows, expected {expected_rows}")
    if int(sizes.loc[sizes["K"].eq(SELECTED_K), "n"].sum()) != 3593:
        raise ValueError("K=3 cluster sizes do not sum to the fixed 3,593-LSOA sample")
    direction_totals = (
        selected.groupby(["cluster", "direction"], observed=True)["mean_share"].sum()
    )
    if not np.allclose(direction_totals.to_numpy(), 1.0, atol=1e-9):
        raise ValueError("Cluster-mean direction shares do not sum to one")
    expected = {
        0: 1882,
        1: 494,
        2: 1217,
    }
    observed = (
        sizes.loc[sizes["K"].eq(SELECTED_K)].set_index("cluster")["n"].astype(int).to_dict()
    )
    if observed != expected:
        raise ValueError(f"K=3 cluster-size/label mismatch: {observed} != {expected}")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    x, grid, kdiag, bootstrap = read_inputs()
    profiles, sizes = build_profiles(x)
    validate_outputs(profiles, sizes)
    plot_bic_grid(grid)
    plot_k_diagnostics(kdiag, bootstrap)
    plot_profiles(profiles, sizes)
    print("Wrote alpha=0 BIC, K-diagnostic, and K=2..8 temporal-profile figures.")
    print(FIGURES.resolve())


if __name__ == "__main__":
    main()
