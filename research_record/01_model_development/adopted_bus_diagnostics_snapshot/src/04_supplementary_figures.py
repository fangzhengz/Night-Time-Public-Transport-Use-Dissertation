# -*- coding: utf-8 -*-
"""Create dissertation-ready diagnostic figures for the StopArea bus analyses."""
from __future__ import annotations

import gc
import sys
from itertools import permutations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import map_style


FIGURES = C.OUT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# Retained-sample size, read once, used to keep figure titles/labels in sync
# with whatever window/threshold config.py currently specifies -- these used
# to be hardcoded (e.g. "3,372-LSOA sample", ">=36") and went stale the
# moment MIN_DIRECTION or HOURS changed.
RETAINED_N = int(pd.read_csv(C.FEATURES / "sample_metrics.csv")["retained_for_fit"].sum())

RAW_COLOR = "#500778"
CLR_COLOR = "#2F6B4F"
GREY = "#A7A9AC"
DARK_GREY = "#4D4D4D"
GOLD = "#C89B3C"
K_COLORS = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2"]


def set_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.linewidth": 0.6,
            "legend.frameon": False,
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)
    gc.collect()


def save_variant_figure(fig: plt.Figure, variant: str, stem: str) -> None:
    destination = C.OUT / variant / "figures"
    destination.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination / f"{stem}.png", dpi=160, bbox_inches="tight")
    fig.savefig(destination / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)
    gc.collect()


def save_variant_aliases(
    fig: plt.Figure,
    variant: str,
    stems: list[str],
    *,
    dpi: int,
    tight: bool = True,
) -> None:
    """Save one figure under both concise and legacy-compatible names."""
    destination = C.OUT / variant / "figures"
    destination.mkdir(parents=True, exist_ok=True)
    save_kwargs = {"bbox_inches": "tight"} if tight else {}
    for stem in stems:
        fig.savefig(destination / f"{stem}.png", dpi=dpi, **save_kwargs)
        fig.savefig(destination / f"{stem}.pdf", **save_kwargs)
    plt.close(fig)
    gc.collect()


def read_kdiag(variant: str) -> pd.DataFrame:
    frame = pd.read_csv(C.OUT / variant / "diagnostics" / "kdiag.csv")
    frame["variant"] = variant
    return frame


def read_labels(variant: str, k: int) -> pd.DataFrame:
    frame = pd.read_csv(
        C.OUT / variant / "labels" / f"k{k}_labels.csv", dtype={"lsoa": str}
    )
    return frame.loc[frame["retained_for_fit"], ["lsoa", "cluster"]].copy()


def sample_filtering_figure(metrics: pd.DataFrame) -> None:
    retained = metrics["retained_for_fit"].astype(bool)
    x = np.log10(1.0 + metrics["tot_boardings"].to_numpy(dtype=float))
    y = np.log10(1.0 + metrics["tot_alightings"].to_numpy(dtype=float))
    cutoff = np.log10(1.0 + C.MIN_DIRECTION)

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5), gridspec_kw={"width_ratios": [1.7, 0.8]})
    ax = axes[0]
    ax.scatter(x[~retained], y[~retained], s=10, color=GREY, alpha=0.55, linewidths=0, label="Excluded")
    ax.scatter(x[retained], y[retained], s=11, color=RAW_COLOR, alpha=0.55, linewidths=0, label="Retained")
    ax.axvline(cutoff, color=GOLD, linewidth=1.5, linestyle="--")
    ax.axhline(cutoff, color=GOLD, linewidth=1.5, linestyle="--")
    ax.set(
        xlabel="log10(1 + full-week boardings)",
        ylabel="log10(1 + full-week alightings)",
        title="StopArea-allocated LSOAs and the two-direction threshold",
    )
    ax.legend(loc="lower right")
    ax.text(
        cutoff + 0.03,
        ax.get_ylim()[0] + 0.05,
        f"{C.MIN_DIRECTION:g} boardings",
        color=DARK_GREY,
        fontsize=9,
        rotation=90,
        va="bottom",
    )
    ax.text(
        ax.get_xlim()[0] + 0.04,
        cutoff + 0.03,
        f"{C.MIN_DIRECTION:g} alightings",
        color=DARK_GREY,
        fontsize=9,
        va="bottom",
    )

    ax = axes[1]
    counts = [int(retained.sum()), int((~retained).sum())]
    bars = ax.bar(["Retained", "Excluded"], counts, color=[RAW_COLOR, GREY], width=0.62)
    total = len(metrics)
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + total * 0.018,
            f"{count:,}\n({count / total:.1%})",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax.set(title="Analytical coverage", ylabel="Number of LSOAs", ylim=(0, max(counts) * 1.16))
    fig.suptitle("Sample construction after official child-StopArea allocation", fontsize=13, y=1.02)
    fig.tight_layout()
    save_figure(fig, "01_sample_filtering")


def delta_bic_figure() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.3), sharex=True)
    for ax, variant, color, label in [
        (axes[0], "raw_share", RAW_COLOR, "Raw-share"),
        (axes[1], "clr", CLR_COLOR, "CLR"),
    ]:
        grid = pd.read_csv(C.OUT / variant / "diagnostics" / "bic_grid.csv")
        full = grid.loc[grid["covariance"] == "full"].sort_values("K").copy()
        full["delta_bic"] = full["BIC"] - full["BIC"].min()
        best = full.loc[full["delta_bic"].idxmin()]
        ax.plot(full["K"], full["delta_bic"], marker="o", color=color, linewidth=2)
        ax.scatter([best["K"]], [0], s=75, color=GOLD, edgecolor=DARK_GREY, linewidth=0.7, zorder=3)
        ax.annotate(
            f"minimum: K={int(best['K'])}",
            (best["K"], 0),
            xytext=(8, 12),
            textcoords="offset points",
            fontsize=9,
        )
        ax.set_title(label)
        ax.set_xlabel("Number of clusters (K)")
        ax.set_xticks(C.K_RANGE)
        ax.set_yscale("symlog", linthresh=100)
    axes[0].set_ylabel("Delta BIC from within-variant minimum (lower is better)")
    fig.suptitle("Full-covariance model selection within each feature space", fontsize=13, y=1.02)
    fig.tight_layout()
    save_figure(fig, "02_full_covariance_delta_bic")


def candidate_diagnostics_figure() -> None:
    data = pd.concat([read_kdiag("raw_share"), read_kdiag("clr")], ignore_index=True)
    data = data[data["K"].isin(C.CANDIDATE_KS)].copy()
    order = [("raw_share", 3), ("raw_share", 4), ("clr", 3), ("clr", 4)]
    labels = ["Raw K=3", "Raw K=4", "CLR K=3", "CLR K=4"]
    colors = [RAW_COLOR, RAW_COLOR, CLR_COLOR, CLR_COLOR]
    hatches = ["", "//", "", "//"]
    metrics = [
        ("silhouette", "Silhouette", None),
        ("activity_eta2", "Activity eta-squared", None),
        ("bootstrap_ari_mean", "Bootstrap ARI mean", (0, 1)),
        ("bootstrap_min_cluster_jaccard_mean", "Minimum-cluster Jaccard mean", (0, 1)),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.5))
    for ax, (column, title, ylim) in zip(axes.flat, metrics):
        values = []
        for variant, k in order:
            values.append(float(data.loc[(data["variant"] == variant) & (data["K"] == k), column].iloc[0]))
        bars = ax.bar(range(4), values, color=colors, width=0.68, edgecolor="white")
        for bar, hatch, value in zip(bars, hatches, values):
            bar.set_hatch(hatch)
            ax.text(bar.get_x() + bar.get_width() / 2, value + max(values) * 0.035, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
        ax.set_title(title)
        ax.set_xticks(range(4), labels, rotation=18, ha="right")
        if ylim:
            ax.set_ylim(*ylim)
        else:
            ax.set_ylim(0, max(values) * 1.2)
    fig.suptitle(f"Candidate diagnostics on the identical {RETAINED_N:,}-LSOA sample", fontsize=13, y=1.01)
    fig.tight_layout()
    save_figure(fig, "03_candidate_diagnostics")


def bootstrap_figure() -> None:
    records = []
    for variant in ["raw_share", "clr"]:
        frame = pd.read_csv(C.OUT / variant / "diagnostics" / "bootstrap.csv")
        frame = frame[frame["K"].isin(C.CANDIDATE_KS)].copy()
        frame["variant"] = variant
        records.append(frame)
    data = pd.concat(records, ignore_index=True)
    groups = [("raw_share", 3), ("raw_share", 4), ("clr", 3), ("clr", 4)]
    labels = ["Raw K=3", "Raw K=4", "CLR K=3", "CLR K=4"]
    colors = [RAW_COLOR, RAW_COLOR, CLR_COLOR, CLR_COLOR]
    hatches = ["", "//", "", "//"]
    rng = np.random.default_rng(42)

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), sharey=True)
    for ax, column, title in [
        (axes[0], "ARI", "Partition recovery (ARI)"),
        (axes[1], "min_matched_cluster_jaccard", "Weakest matched cluster (Jaccard)"),
    ]:
        arrays = [
            data.loc[(data["variant"] == variant) & (data["K"] == k), column].to_numpy(dtype=float)
            for variant, k in groups
        ]
        bp = ax.boxplot(arrays, patch_artist=True, widths=0.58, showfliers=False, medianprops={"color": "white", "linewidth": 1.5})
        for patch, color, hatch in zip(bp["boxes"], colors, hatches):
            patch.set_facecolor(color)
            patch.set_hatch(hatch)
            patch.set_alpha(0.86)
        for index, values in enumerate(arrays, start=1):
            jitter = rng.uniform(-0.10, 0.10, size=len(values))
            ax.scatter(np.full(len(values), index) + jitter, values, s=13, color=DARK_GREY, alpha=0.55, linewidths=0)
        ax.set_title(title)
        ax.set_xticks(range(1, 5), labels, rotation=18, ha="right")
        ax.set_ylim(0, 1.03)
        ax.axhline(0.8, color=GOLD, linestyle="--", linewidth=1, alpha=0.8)
    axes[0].set_ylabel("Bootstrap agreement")
    fig.suptitle("Bootstrap stability across 20 resamples", fontsize=13, y=1.02)
    fig.tight_layout()
    save_figure(fig, "04_bootstrap_stability")


def partition_agreement_figure() -> None:
    cmap = LinearSegmentedColormap.from_list("agreement", ["#F2EEF5", RAW_COLOR])
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.7))
    for ax, k in zip(axes, C.CANDIDATE_KS):
        raw = read_labels("raw_share", k)
        clr = read_labels("clr", k)
        merged = raw.merge(clr, on="lsoa", suffixes=("_raw", "_clr"), validate="one_to_one")
        table = pd.crosstab(merged["cluster_raw"], merged["cluster_clr"]).reindex(index=range(k), columns=range(k), fill_value=0)
        matrix = table.to_numpy()
        ordered_clr = list(
            max(
                permutations(range(k)),
                key=lambda order: sum(matrix[row, order[row]] for row in range(k)),
            )
        )
        table = table[ordered_clr]
        shares = table.div(table.sum(axis=1), axis=0)
        image = ax.imshow(shares.to_numpy(), vmin=0, vmax=1, cmap=cmap, aspect="equal")
        for row in range(k):
            for column in range(k):
                share = float(shares.iloc[row, column])
                count = int(table.iloc[row, column])
                ax.text(
                    column,
                    row,
                    f"{count:,}\n{share:.0%}",
                    ha="center",
                    va="center",
                    color="white" if share > 0.48 else DARK_GREY,
                    fontsize=9,
                )
        ari = adjusted_rand_score(merged["cluster_raw"], merged["cluster_clr"])
        ax.set_title(f"K={k}: ARI={ari:.3f}")
        ax.set_xlabel("CLR cluster (matched order)")
        ax.set_ylabel("Raw-share cluster")
        ax.set_xticks(range(k), [f"C{value}" for value in ordered_clr])
        ax.set_yticks(range(k), [f"C{value}" for value in range(k)])
    colorbar = fig.colorbar(image, ax=axes, fraction=0.035, pad=0.04)
    colorbar.set_label("Share of each raw-share cluster")
    fig.suptitle("Raw-share and CLR partition agreement on identical LSOAs", fontsize=13, y=0.99)
    fig.subplots_adjust(left=0.08, right=0.89, bottom=0.13, top=0.84, wspace=0.30)
    save_figure(fig, "05_raw_clr_partition_agreement")


def activity_by_cluster_figure(metrics: pd.DataFrame) -> None:
    base = metrics[["lsoa", "total_activity"]].copy()
    base["log10_activity"] = np.log10(base["total_activity"].astype(float))
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.6), sharey=True)
    for ax, variant, k in zip(
        axes.flat,
        ["raw_share", "raw_share", "clr", "clr"],
        [3, 4, 3, 4],
    ):
        labels = read_labels(variant, k)
        joined = labels.merge(base, on="lsoa", how="left", validate="one_to_one")
        arrays = [
            joined.loc[joined["cluster"] == cluster, "log10_activity"].to_numpy(dtype=float)
            for cluster in range(k)
        ]
        bp = ax.boxplot(arrays, patch_artist=True, widths=0.63, showfliers=False, medianprops={"color": "white", "linewidth": 1.4})
        for cluster, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(K_COLORS[cluster])
            patch.set_alpha(0.88)
        eta = float(read_kdiag(variant).loc[lambda d: d["K"] == k, "activity_eta2"].iloc[0])
        ax.set_title(f"{'Raw-share' if variant == 'raw_share' else 'CLR'}, K={k}  |  activity eta-squared={eta:.3f}")
        ax.set_xticks(range(1, k + 1), [f"C{cluster}" for cluster in range(k)])
        ax.set_xlabel("Cluster (labels are local to each model)")
        for index, values in enumerate(arrays, start=1):
            ax.text(index, ax.get_ylim()[0] + 0.04, f"n={len(values):,}", ha="center", va="bottom", fontsize=8, color=DARK_GREY)
    axes[0, 0].set_ylabel("log10(full-week total activity)")
    axes[1, 0].set_ylabel("log10(full-week total activity)")
    fig.suptitle("Activity distributions within candidate clusters", fontsize=13, y=1.01)
    fig.tight_layout()
    save_figure(fig, "06_activity_by_cluster")


def central_outer_figure() -> None:
    rows = []
    for variant in ["raw_share", "clr"]:
        frame = pd.read_csv(C.OUT / variant / "data" / "central_outer_diagnostic.csv")
        frame["variant"] = variant
        rows.append(frame)
    data = pd.concat(rows, ignore_index=True)
    order = [("raw_share", 3), ("raw_share", 4), ("clr", 3), ("clr", 4)]
    labels = ["Raw K=3", "Raw K=4", "CLR K=3", "CLR K=4"]
    colors = [RAW_COLOR, RAW_COLOR, CLR_COLOR, CLR_COLOR]
    hatches = ["", "//", "", "//"]
    columns = [
        ("central_outer_total_variation", "Central–outer total variation", "Higher means less overlap"),
        ("central_outer_same_cluster_probability", "Same-cluster probability", "Lower means less overlap"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.4), sharey=True)
    for ax, (column, title, subtitle) in zip(axes, columns):
        values = [
            float(data.loc[(data["variant"] == variant) & (data["K"] == k), column].iloc[0])
            for variant, k in order
        ]
        bars = ax.bar(range(4), values, color=colors, width=0.66, edgecolor="white")
        for bar, hatch, value in zip(bars, hatches, values):
            bar.set_hatch(hatch)
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.018, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
        ax.set_title(f"{title}\n{subtitle}")
        ax.set_xticks(range(4), labels, rotation=18, ha="right")
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("Diagnostic value")
    fig.suptitle("External central-versus-outer characterization", fontsize=13, y=1.02)
    fig.tight_layout()
    save_figure(fig, "07_central_outer_comparison")


def house_style_profiles_and_maps(metrics: pd.DataFrame, variant: str) -> None:
    """Recreate the five core outputs using the original analysis layout."""
    raw_share = pd.read_parquet(C.FEATURES / "X_bus_stoparea_raw_share_min33.parquet")
    raw_share.index = pd.Index(raw_share.index.astype(str), name="lsoa")
    retained_units = raw_share.index
    metrics = metrics.copy()
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    all_units = pd.Index(metrics["lsoa"], name="lsoa")

    legacy_prefix = "literature_mean1ph_full" if variant == "raw_share" else "clr"
    for k in C.CANDIDATE_KS:
        labels_frame = read_labels(variant, k).set_index("lsoa").loc[retained_units]
        labels = labels_frame["cluster"].to_numpy(dtype=int)
        sizes = np.bincount(labels, minlength=k)
        fig, axes = plt.subplots(
            k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True
        )
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            means = raw_share.loc[labels == cluster].mean(axis=0)
            for day_index, day_type in enumerate(C.DAY_TYPES):
                ax = axes[cluster, day_index]
                for direction, color in [
                    ("boardings", "#4C78A8"),
                    ("alightings", "#F58518"),
                ]:
                    values = [
                        means[f"{direction}_{day_type}_{hour}"] for hour in C.HOURS
                    ]
                    ax.plot(
                        range(len(C.HOURS)),
                        values,
                        marker="o",
                        markersize=2,
                        color=color,
                        label=direction,
                    )
                if cluster == 0:
                    ax.set_title(day_type)
                if day_index == 0:
                    ax.set_ylabel(f"C{cluster} (n={int(sizes[cluster])})")
                ax.grid(alpha=0.2)
        axes[-1, 1].set_xticks(
            range(len(C.HOURS)),
            [f"{((h // 60) % 24):02d}" for h in C.HOURS],
            rotation=45,
        )
        axes[0, -1].legend(loc="upper right", fontsize=8)
        if variant == "raw_share":
            title = (
                f"StopArea mean >=1/hour analogue (both directions >={C.MIN_DIRECTION:g}), "
                f"full covariance, K={k}\n"
                "mean share of each direction's own full-week total"
            )
        else:
            title = (
                f"StopArea CLR-derived clusters (both directions >={C.MIN_DIRECTION:g}), "
                f"full covariance, K={k}\n"
                "profiles shown in raw-share space for interpretability"
            )
        fig.suptitle(title, y=1.01)
        fig.tight_layout()
        save_variant_aliases(
            fig,
            variant,
            [f"profiles_k{k}", f"{legacy_prefix}_profiles_k{k}"],
            dpi=160,
        )

    import geopandas as gpd

    boundaries = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(column for column in boundaries if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(
        columns={code_column: "lsoa"}
    )
    # 2026-08-08: aligned to the same house style as 02_run_clustering.py's
    # own maps (map_style.draw_cluster_map) instead of a plain tab10 legend
    # that only showed numeric cluster ids and collapsed low-flow/no-stop
    # into one grey -- see map_style.py's module docstring for why those two
    # states are kept visually distinct.
    for k in C.CANDIDATE_KS:
        labels = (
            read_labels(variant, k)
            .set_index("lsoa")
            .loc[retained_units, "cluster"]
            .to_numpy(dtype=int)
        )
        mapped = map_style.build_status_frame(boundaries, retained_units, labels, all_units)
        fig, ax = plt.subplots(figsize=(8, 8))
        map_style.draw_cluster_map(ax, mapped, k)
        if variant == "raw_share":
            title = f"StopArea mean >=1/hour analogue, full covariance, K={k}"
        else:
            title = f"StopArea CLR-derived clusters, full covariance, K={k}"
        ax.set_title(
            f"{title}\nretained if both directions >= {C.MIN_DIRECTION:g} over the full week",
            fontsize=11,
        )
        fig.tight_layout()
        save_variant_aliases(
            fig,
            variant,
            [f"map_k{k}", f"{legacy_prefix}_map_k{k}"],
            dpi=180,
            tight=False,
        )


def house_style_kdiag(variant: str) -> None:
    feature_path = (
        C.FEATURES / "X_bus_stoparea_raw_share_min33.parquet"
        if variant == "raw_share"
        else C.FEATURES / "X_bus_stoparea_clr_min33.parquet"
    )
    X = pd.read_parquet(feature_path)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    Xv = X.to_numpy(dtype=float)
    d = read_kdiag(variant).drop(columns="variant")

    ch_rows = []
    for k in C.K_RANGE:
        labels = read_labels(variant, k).set_index("lsoa").loc[X.index, "cluster"].to_numpy(dtype=int)
        ch_rows.append({"K": k, "calinski_harabasz": float(calinski_harabasz_score(Xv, labels))})
    d = d.merge(pd.DataFrame(ch_rows), on="K", how="left")

    bootstrap = pd.read_csv(C.OUT / variant / "diagnostics" / "bootstrap.csv")
    boot_summary = (
        bootstrap.groupby("K")["ARI"]
        .agg(ARI_mean="mean", ARI_sd="std")
        .reset_index()
    )
    d = d.merge(boot_summary, on="K", how="left")
    d.to_csv(C.OUT / variant / "diagnostics" / "kdiag_full.csv", index=False)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    panels = [
        ("silhouette", "Silhouette (higher=better)", RAW_COLOR),
        ("calinski_harabasz", "Calinski-Harabasz (higher=better)", CLR_COLOR),
        ("davies_bouldin", "Davies-Bouldin (lower=better)", "#9A3D3D"),
        ("BIC", "BIC (lower=better)", RAW_COLOR),
    ]
    for ax, (column, title, color) in zip(axes.flat[:4], panels):
        ax.plot(d["K"], d[column], "-o", color=color)
        ax.set_title(title)
    ax = axes.flat[4]
    available = d["ARI_mean"].notna()
    ax.errorbar(
        d.loc[available, "K"],
        d.loc[available, "ARI_mean"],
        yerr=d.loc[available, "ARI_sd"],
        fmt="-o",
        color=RAW_COLOR,
        capsize=3,
    )
    ax.set_title("Bootstrap stability ARI (higher=better)")
    ax.set_ylim(0, 1.02)
    axes.flat[5].axis("off")
    for ax in axes.flat:
        if ax.has_data():
            ax.set_xlabel("K")
            ax.set_xticks(C.K_RANGE)
            ax.grid(color="#eeeeee")
            ax.spines[["top", "right"]].set_visible(False)
    variant_title = "raw-share" if variant == "raw_share" else "CLR-transformed"
    feature_title = "raw-share" if variant == "raw_share" else "CLR features"
    kdiag_title = (
        f"bus (StopArea allocation, full week, both directions >={C.MIN_DIRECTION:g}, {variant_title}) - K-diagnostics\n"
        f"same {RETAINED_N:,}-LSOA sample, full-covariance reporting family ({feature_title}, GMM)"
    )
    fig.suptitle(
        f"bus (StopArea allocation, full week, both directions >={C.MIN_DIRECTION:g}, {variant_title}) — K-diagnostics\n"
        f"same {RETAINED_N:,}-LSOA sample, full-covariance reporting family ({feature_title}, GMM)",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    fig.suptitle(kdiag_title, fontsize=13, y=1.02)
    legacy_stem = (
        "literature_mean1ph_kdiag_full" if variant == "raw_share" else "clr_kdiag_full"
    )
    save_variant_aliases(fig, variant, ["kdiag_full", legacy_stem], dpi=160)


def house_style_homogeneity(metrics: pd.DataFrame, variant: str, k: int) -> None:
    labels = read_labels(variant, k)
    joined = labels.merge(metrics, on="lsoa", how="left", validate="one_to_one")
    plot_metrics = [
        "log_total_activity",
        "post_midnight_share",
        "deep_night_share",
        "post_midnight_persistence",
    ]
    fig, axes = plt.subplots(1, len(plot_metrics), figsize=(4.2 * len(plot_metrics), 4.2))
    for ax, metric in zip(axes, plot_metrics):
        arrays = [
            joined.loc[joined["cluster"] == cluster, metric].dropna().to_numpy(dtype=float)
            for cluster in range(k)
        ]
        ax.boxplot(
            arrays,
            tick_labels=[f"C{cluster}" for cluster in range(k)],
            showfliers=False,
            medianprops={"color": "#F58518"},
        )
        ax.set_title(metric)
        ax.grid(alpha=0.2)
    label = "Raw-share" if variant == "raw_share" else "CLR"
    fig.suptitle(
        f"StopArea allocation, both directions >={C.MIN_DIRECTION:g}: within-cluster dispersion, {label}, K={k}"
    )
    fig.tight_layout()
    save_variant_figure(fig, variant, f"homogeneity_boxplots_k{k}")


def write_index() -> None:
    lines = [
        "# Figure index: StopArea bus clustering",
        "",
        "All figures are saved as publication-resolution PNG and vector PDF.",
        "",
        "| Figure | Analytical purpose | Interpretation boundary |",
        "|---|---|---|",
        f"| `01_sample_filtering` | Shows the both-directions>={C.MIN_DIRECTION:g} rule and retained coverage. | The retained sample represents higher-evidence LSOAs, not all London LSOAs. |",
        "| `02_full_covariance_delta_bic` | Shows within-variant K selection after setting each feature space's best BIC to zero. | Absolute BIC cannot be compared between raw-share and CLR spaces. |",
        "| `03_candidate_diagnostics` | Compares silhouette, activity eta-squared, bootstrap ARI and weakest-cluster Jaccard for K=3/K=4. | No single metric settles K; activity eta-squared is a confounding diagnostic. |",
        "| `04_bootstrap_stability` | Shows the distribution across 20 bootstrap resamples. | Stability does not establish substantive validity. |",
        "| `05_raw_clr_partition_agreement` | Shows how raw-share clusters split under CLR on identical LSOAs. | Cluster numbers are arbitrary and CLR columns are reordered only for display. |",
        "| `06_activity_by_cluster` | Makes the remaining activity association visible. | The fitted feature vectors omit total activity; these are external distributions. |",
        "| `07_central_outer_comparison` | Compares external central/outer separation diagnostics. | Geography is not fitted by the GMM and is not an independent validation target. |",
        "",
        "## Required core figures",
        "",
        "Variant-specific figures under `outputs/raw_share/figures` and `outputs/clr/figures` reproduce the original two analyses' house style:",
        "",
        "- Raw-share: `literature_mean1ph_full_map_k{3,4}`, `literature_mean1ph_full_profiles_k{3,4}`, and `literature_mean1ph_kdiag_full`.",
        "- CLR: `clr_map_k{3,4}`, `clr_profiles_k{3,4}`, and `clr_kdiag_full`.",
        "- Every core figure is saved as PNG and PDF; concise aliases (`map_k*`, `profiles_k*`, `kdiag_full`) are retained.",
        "- The K-diagnostic is the original 2x3 silhouette, Calinski-Harabasz, Davies-Bouldin, BIC and bootstrap-ARI panel.",
        "- `homogeneity_boxplots_k{3,4}`: four raw-metric dispersion panels.",
    ]
    (C.REPORT / "FIGURE_INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    set_style()
    metrics = pd.read_csv(C.FEATURES / "sample_metrics.csv", dtype={"lsoa": str})
    sample_filtering_figure(metrics)
    delta_bic_figure()
    candidate_diagnostics_figure()
    bootstrap_figure()
    partition_agreement_figure()
    activity_by_cluster_figure(metrics)
    central_outer_figure()
    for variant in ["raw_share", "clr"]:
        house_style_profiles_and_maps(metrics, variant)
        house_style_kdiag(variant)
        for k in C.CANDIDATE_KS:
            house_style_homogeneity(metrics, variant, k)
    write_index()
    print(
        f"Wrote 7 cross-variant figures plus original-style maps, temporal profiles, "
        f"K-diagnostics and homogeneity panels (PNG + PDF) under {C.OUT}"
    )


if __name__ == "__main__":
    main()
