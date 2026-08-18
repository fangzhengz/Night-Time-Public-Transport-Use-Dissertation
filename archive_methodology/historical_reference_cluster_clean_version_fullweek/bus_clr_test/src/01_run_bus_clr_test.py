# -*- coding: utf-8 -*-
"""CLR clustering on the point-in-polygon (pre-StopArea) bus allocation.

Third arm of a three-way robustness check on whether the LSOA allocation
method (point-in-polygon vs hub-first vs official StopArea) drives the CLR
bus clustering result, or whether the CLR transform and the min-direction
threshold dominate regardless of allocation method. The other two arms:

- hub-first: `rq1_bus_clr_transform` (n=3,365; scripts no longer runnable --
  their upstream paths were archived on 2026-07-23, see that folder's
  outputs/report/CLR_RESULTS.md for the frozen numbers).
- official StopArea: `rq1_bus_stoparea_clustering/outputs/clr` (n=3,372,
  canonical).

Self-contained by design: the input long table is a frozen local copy
(`../input/bus_lsoa_night_long_point_in_polygon.parquet`, copied 2026-07-29
from `FYP/旧分析归档/cluster_clean_version_grouped/outputs/preprocessed/
bus_lsoa_night_long.parquet`) and no code is imported from any other
analysis folder. This avoids the exact failure mode found in
rq1_bus_clr_transform, whose scripts hardcoded paths into sibling folders
that were later archived.

Sample rule: both directions' full-week total >= 36 (single condition,
matching the current canonical rule; see rq1_bus_stoparea_clustering's
2026-07-29 config.py comment for why the former companion total>=50 rule
was dropped -- it never bound).
"""
from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import (
    adjusted_rand_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import map_style

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parents[1]

LONG_INPUT = ROOT / "input" / "bus_lsoa_night_long_point_in_polygon.parquet"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

OUT = ROOT / "outputs"
FEATURES = OUT / "features"
DIAGNOSTICS = OUT / "diagnostics"
LABELS = OUT / "labels"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
for path in (OUT, FEATURES, DIAGNOSTICS, LABELS, FIGURES, REPORT):
    path.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
HOURS = list(range(1080, 1800, 60))
MIN_DIRECTION = 36.0
CLR_PSEUDOCOUNT_ALPHA = 1.0

K_RANGE = list(range(2, 13))
CANDIDATE_KS = [3, 4]
FIGURE_KS = [3, 4, 5, 6, 7, 8]
BOOTSTRAP_KS = [2, 3, 4, 5, 6, 7, 8]
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
BOOTSTRAP_N_INIT = 3
BOOTSTRAP_N = 20
REG_COVAR = 1e-6
MAX_ITER = 300
SEED = 42
TIMING_METRICS = ["post_midnight_share", "deep_night_share", "post_midnight_persistence"]


def log(message: str) -> None:
    print(message, flush=True)


def fit_gmm(X, k, covariance, seed, n_init):
    return GaussianMixture(
        n_components=k, covariance_type=covariance, n_init=n_init,
        reg_covar=REG_COVAR, max_iter=MAX_ITER, random_state=seed,
    ).fit(X)


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = float(y.mean())
    total = float(np.square(y - grand).sum())
    if total <= 0:
        return float("nan")
    between = sum(
        int((labels == c).sum()) * (float(y[labels == c].mean()) - grand) ** 2
        for c in np.unique(labels)
    )
    return float(between / total)


def matched_jaccard(base: np.ndarray, other: np.ndarray, k: int) -> np.ndarray:
    contingency = np.zeros((k, k), dtype=int)
    for left, right in zip(base, other):
        contingency[int(left), int(right)] += 1
    base_sizes = contingency.sum(axis=1, keepdims=True)
    other_sizes = contingency.sum(axis=0, keepdims=True)
    union = base_sizes + other_sizes - contingency
    scores = np.divide(contingency, union, out=np.zeros_like(contingency, dtype=float), where=union > 0)
    rows, cols = linear_sum_assignment(-scores)
    matched = np.zeros(k, dtype=float)
    matched[rows] = scores[rows, cols]
    return matched


def build_sample_and_raw_counts():
    log("[1/9] Loading frozen point-in-polygon long table and building sample")
    long = pd.read_parquet(LONG_INPUT)
    long["lsoa"] = long["lsoa"].astype(str)
    long["hour_bin"] = long["hour_bin"].astype(int)

    all_input_units = pd.Index(sorted(long["lsoa"].unique()), name="lsoa")

    direction_totals = (
        long.groupby(["lsoa", "direction"], observed=True)["count"].sum().unstack(fill_value=0.0)
    )
    for direction in DIRECTIONS:
        if direction not in direction_totals.columns:
            direction_totals[direction] = 0.0
    min_direction_activity = direction_totals[DIRECTIONS].min(axis=1)
    total_activity_all = direction_totals[DIRECTIONS].sum(axis=1)

    retained_mask = min_direction_activity >= MIN_DIRECTION
    keep = pd.Index(sorted(min_direction_activity.index[retained_mask].astype(str)), name="lsoa")

    sample_metrics = pd.DataFrame(index=all_input_units)
    sample_metrics["min_direction_activity"] = min_direction_activity.reindex(all_input_units)
    sample_metrics["total_activity"] = total_activity_all.reindex(all_input_units)
    sample_metrics["retained_for_fit"] = sample_metrics.index.isin(set(keep))
    sample_metrics["exclusion_reason"] = np.where(
        sample_metrics["retained_for_fit"], "retained", "at_least_one_direction_below_36"
    )
    sample_metrics.reset_index().to_csv(FEATURES / "sample_metrics.csv", index=False)
    log(
        f"      input LSOAs (any demand): {len(all_input_units)} | "
        f"retained (min_direction>=36): {len(keep)} | excluded: {len(all_input_units) - len(keep)}"
    )

    raw_counts: dict[str, pd.DataFrame] = {}
    for direction in DIRECTIONS:
        day_parts = []
        for day_type in DAY_TYPES:
            sub = long[(long["day_type"] == day_type) & (long["direction"] == direction)]
            wide = sub.pivot_table(index="lsoa", columns="hour_bin", values="count", aggfunc="sum", fill_value=0.0)
            wide = wide.reindex(index=keep, columns=HOURS, fill_value=0.0).astype(float)
            wide.columns = pd.MultiIndex.from_product([[day_type], HOURS])
            day_parts.append(wide)
        block = pd.concat(day_parts, axis=1)
        block.columns = [f"{direction}_{day}_{int(hour)}" for day, hour in block.columns]
        raw_counts[direction] = block

    raw = long[long["lsoa"].isin(set(keep))]
    total = raw.groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    direction_raw = (
        raw.groupby(["lsoa", "direction"], observed=True)["count"].sum()
        .unstack(fill_value=0.0).reindex(index=keep, columns=DIRECTIONS, fill_value=0.0)
    )
    post_midnight = raw.loc[raw["hour_bin"].between(1440, 1799)].groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    deep_night = raw.loc[raw["hour_bin"].between(1620, 1799)].groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    evening = raw.loc[raw["hour_bin"].between(1080, 1259)].groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    day_total = (
        raw.groupby(["lsoa", "day_type"], observed=True)["count"].sum()
        .unstack(fill_value=0.0).reindex(index=keep, columns=DAY_TYPES, fill_value=0.0)
    )

    metrics = pd.DataFrame(index=keep)
    metrics["total_activity"] = total
    metrics["log_total_activity"] = np.log1p(total)
    metrics["direction_balance"] = (direction_raw["boardings"] - direction_raw["alightings"]) / total
    metrics["post_midnight_share"] = post_midnight / total
    metrics["deep_night_share"] = deep_night / total
    metrics["post_midnight_persistence"] = post_midnight / evening.replace(0.0, np.nan)
    metrics["weekend_ratio"] = day_total[["Saturday", "Sunday"]].mean(axis=1) / day_total["Weekday"].replace(0.0, np.nan)
    metrics.to_csv(FEATURES / "raw_metrics.csv")

    return keep, raw_counts, metrics, all_input_units


def build_raw_share(raw_counts) -> pd.DataFrame:
    blocks = []
    for direction in DIRECTIONS:
        counts = raw_counts[direction]
        totals = counts.sum(axis=1).replace(0.0, np.nan)
        share = counts.div(totals, axis=0).fillna(0.0)
        blocks.append(share)
    return pd.concat(blocks, axis=1)


def build_clr(raw_counts, keep) -> pd.DataFrame:
    log(f"[2/9] Building CLR features (pseudo-count alpha={CLR_PSEUDOCOUNT_ALPHA})")
    blocks = []
    for direction in DIRECTIONS:
        counts = raw_counts[direction].to_numpy(dtype=float)
        totals = counts.sum(axis=1)
        prior = counts.sum(axis=0) / counts.sum()
        posterior = (counts + CLR_PSEUDOCOUNT_ALPHA * prior) / (totals[:, None] + CLR_PSEUDOCOUNT_ALPHA)
        if not np.all(posterior > 0):
            raise ValueError(f"Non-positive share in {direction} block after pseudo-count")
        log_shares = np.log(posterior)
        clr = log_shares - log_shares.mean(axis=1, keepdims=True)
        if not np.allclose(clr.sum(axis=1), 0.0, atol=1e-8):
            raise ValueError(f"CLR block for {direction} does not sum to zero")
        blocks.append(pd.DataFrame(clr, index=keep, columns=raw_counts[direction].columns))
    X = pd.concat(blocks, axis=1)
    if X.shape != (len(keep), 72):
        raise ValueError(f"Unexpected CLR feature shape: {X.shape}")
    if not np.isfinite(X.to_numpy()).all():
        raise ValueError("CLR feature matrix contains non-finite values")
    X.to_parquet(FEATURES / "X_bus_pointinpolygon_clr.parquet")
    return X


def choose_reporting_family(grid: pd.DataFrame) -> tuple[str, str, int, str]:
    best_row = grid.loc[grid["BIC"].idxmin()]
    global_family, global_k = str(best_row["covariance"]), int(best_row["K"])
    if global_family != "full" and int(best_row["min_cluster_n"]) <= 3:
        note = (
            f"Global BIC minimum was covariance={global_family}, K={global_k}, "
            f"min_cluster_n={int(best_row['min_cluster_n'])} -- degenerate near-singleton, "
            "overridden to covariance=full."
        )
        return "full", global_family, global_k, note
    return global_family, global_family, global_k, "Global BIC minimum family used directly; no override needed."


def main() -> None:
    started = time.time()
    keep, raw_counts, metrics, all_input_units = build_sample_and_raw_counts()

    X_clr = build_clr(raw_counts, keep)
    raw_share = build_raw_share(raw_counts)
    Xv = X_clr.to_numpy(dtype=float)

    log(f"[3/9] Fitting 4 covariance families x K=2..12, n_init={N_INIT}, n={len(Xv)}")
    grid_rows, grid_labels = [], {}
    for covariance in COVARIANCES:
        for k in K_RANGE:
            t0 = time.perf_counter()
            model = fit_gmm(Xv, k, covariance, SEED, N_INIT)
            labels = model.predict(Xv).astype(int)
            grid_labels[(covariance, k)] = labels
            sizes = np.bincount(labels, minlength=k)
            grid_rows.append({
                "covariance": covariance, "K": k, "BIC": float(model.bic(Xv)), "AIC": float(model.aic(Xv)),
                "converged": bool(model.converged_), "fit_seconds": time.perf_counter() - t0,
                "min_cluster_n": int(sizes.min()), "min_cluster_share": float(sizes.min() / sizes.sum()),
            })
            log(f"      {covariance:9s} K={k:2d} BIC={grid_rows[-1]['BIC']:.1f} min_n={int(sizes.min()):4d}")
    grid = pd.DataFrame(grid_rows)
    grid.to_csv(DIAGNOSTICS / "clr_bic_grid.csv", index=False)
    reporting_family, global_family, global_k, family_note = choose_reporting_family(grid)
    log(f"[4/9] Reporting covariance={reporting_family}; {family_note}")
    labels_by_k = {k: grid_labels[(reporting_family, k)] for k in K_RANGE}

    log("[5/9] K diagnostics")
    kdiag_rows = []
    for k in K_RANGE:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        grid_row = grid[(grid["covariance"] == reporting_family) & (grid["K"] == k)].iloc[0]
        row = {
            "K": k, "BIC": float(grid_row["BIC"]),
            "silhouette": float(silhouette_score(Xv, labels)),
            "davies_bouldin": float(davies_bouldin_score(Xv, labels)),
            "activity_eta2": eta_squared(metrics["log_total_activity"], labels),
            "min_cluster_share": float(sizes.min() / sizes.sum()),
        }
        for metric in TIMING_METRICS + ["direction_balance", "weekend_ratio"]:
            values = metrics[metric]
            mask = values.notna()
            row[f"{metric}_eta2"] = eta_squared(values[mask], labels[mask.to_numpy()])
        row["timing_mean_eta2"] = float(np.mean([row[f"{m}_eta2"] for m in TIMING_METRICS]))
        kdiag_rows.append(row)
        label_frame = pd.DataFrame({"lsoa": keep, "cluster": labels})
        label_frame.to_csv(LABELS / f"clr_k{k}_labels.csv", index=False)
    kdiag = pd.DataFrame(kdiag_rows)

    log(f"[6/9] Bootstrap K={BOOTSTRAP_KS}, replicates={BOOTSTRAP_N}")
    rng = np.random.default_rng(SEED)
    boot_rows = []
    for k in BOOTSTRAP_KS:
        base = labels_by_k[k]
        for replicate in range(BOOTSTRAP_N):
            idx = rng.choice(len(Xv), size=len(Xv), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model = fit_gmm(Xv[idx], k, reporting_family, seed, BOOTSTRAP_N_INIT)
            other = model.predict(Xv)
            matched = matched_jaccard(base, other, k)
            boot_rows.append({
                "K": k, "replicate": replicate + 1, "ARI": float(adjusted_rand_score(base, other)),
                "min_matched_cluster_jaccard": float(matched.min()),
            })
        sub = pd.DataFrame(boot_rows)
        sub = sub[sub["K"] == k]
        log(f"      K={k}: ARI mean={sub['ARI'].mean():.3f}; min Jaccard mean={sub['min_matched_cluster_jaccard'].mean():.3f}")
    bootstrap = pd.DataFrame(boot_rows)
    bootstrap.to_csv(DIAGNOSTICS / "clr_bootstrap.csv", index=False)
    boot_summary = bootstrap.groupby("K", as_index=False).agg(
        bootstrap_ari_mean=("ARI", "mean"), bootstrap_ari_sd=("ARI", "std"),
        bootstrap_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
    )
    kdiag = kdiag.merge(boot_summary, on="K", how="left")
    kdiag.to_csv(DIAGNOSTICS / "clr_kdiag.csv", index=False)

    log("[7/9] Per-cluster homogeneity for K=3,4")
    grand_centroid = Xv.mean(axis=0)
    grand_mean_distance = float(np.linalg.norm(Xv - grand_centroid, axis=1).mean())
    homogeneity_rows = []
    for k in CANDIDATE_KS:
        labels = labels_by_k[k]
        sil_samples = silhouette_samples(Xv, labels)
        for cluster in range(k):
            mask = labels == cluster
            members = Xv[mask]
            centroid = members.mean(axis=0)
            dist = np.linalg.norm(members - centroid, axis=1)
            homogeneity_rows.append({
                "K": k, "cluster": cluster, "n": int(mask.sum()), "share": float(mask.mean()),
                "mean_silhouette": float(sil_samples[mask].mean()),
                "relative_compactness_vs_sample": float(dist.mean() / grand_mean_distance),
            })
    homogeneity = pd.DataFrame(homogeneity_rows)
    homogeneity.to_csv(DIAGNOSTICS / "clr_cluster_homogeneity.csv", index=False)

    log("[8/9] Figures: BIC grid, K-diagnostics, temporal profiles, spatial maps")
    fig, ax = plt.subplots(figsize=(8, 5))
    for covariance in COVARIANCES:
        sub = grid[grid["covariance"] == covariance]
        ax.plot(sub["K"], sub["BIC"], marker="o", label=covariance)
    ax.set(xlabel="K", ylabel="BIC", title="Point-in-polygon allocation, CLR features: BIC grid")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "clr_bic_grid.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].plot(kdiag["K"], kdiag["silhouette"], marker="o")
    axes[0].set_title("Silhouette (CLR space)")
    axes[1].plot(kdiag["K"], kdiag["activity_eta2"], marker="o", label="activity")
    axes[1].plot(kdiag["K"], kdiag["timing_mean_eta2"], marker="s", label="timing mean")
    axes[1].set_title("Between-group eta2 (raw metrics)")
    axes[1].legend()
    axes[2].plot(kdiag["K"], kdiag["bootstrap_ari_mean"], marker="o")
    axes[2].set_title("Bootstrap ARI mean")
    for a in axes:
        a.set_xlabel("K")
        a.grid(alpha=0.25)
    fig.suptitle("Point-in-polygon allocation, CLR: K diagnostics", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES / "clr_k_diagnostics.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(kdiag["K"], kdiag["bootstrap_min_cluster_jaccard_mean"], marker="o", color="#0072B2")
    ax.set(xlabel="K", ylabel="min matched-cluster Jaccard (mean over 20 resamples)",
           title="Point-in-polygon allocation, CLR: smallest-cluster reproducibility")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "clr_min_cluster_stability.png", dpi=180)
    plt.close(fig)

    for k in FIGURE_KS:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        fig, axes = plt.subplots(k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True)
        axes = np.atleast_2d(axes)
        share_for_profile = raw_share.loc[keep]
        for cluster in range(k):
            means = share_for_profile.loc[labels == cluster].mean(axis=0)
            for day_index, day_type in enumerate(DAY_TYPES):
                ax = axes[cluster, day_index]
                for direction, color in [("boardings", "#0072B2"), ("alightings", "#D55E00")]:
                    values = [means[f"{direction}_{day_type}_{hour}"] for hour in HOURS]
                    ax.plot(range(12), values, marker="o", markersize=2, color=color, label=direction)
                if cluster == 0:
                    ax.set_title(day_type)
                if day_index == 0:
                    share_pct = sizes[cluster] / sizes.sum() * 100
                    ax.set_ylabel(
                        f"C{cluster}\nn={int(sizes[cluster]):,} ({share_pct:.1f}%)",
                        color=map_style.cluster_colour(cluster), fontweight="bold", fontsize=9,
                    )
                ax.grid(alpha=0.2)
        axes[-1, 1].set_xticks(range(12), ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"], rotation=45)
        axes[0, -1].legend(loc="upper right", fontsize=8)
        fig.suptitle(
            f"Point-in-polygon allocation, CLR clustering, K={k}\n"
            "profiles shown as each direction's raw full-week share",
            y=1.01,
        )
        fig.tight_layout()
        fig.savefig(FIGURES / f"profiles_k{k}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

    boundaries = gpd.read_file(LSOA_GEOJSON)
    code_column = next(column for column in boundaries if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(columns={code_column: "lsoa"})
    for k in FIGURE_KS:
        mapped = map_style.build_status_frame(boundaries, keep, labels_by_k[k], all_input_units)
        fig, ax = plt.subplots(figsize=(9, 9))
        map_style.draw_cluster_map(ax, mapped, k)
        ax.set_title(
            f"Point-in-polygon allocation, CLR, K={k}\n"
            f"retained if both directions >= {MIN_DIRECTION:g} over the full week",
            fontsize=11,
        )
        fig.tight_layout()
        fig.savefig(FIGURES / f"map_k{k}.png", dpi=180, bbox_inches="tight")
        fig.savefig(FIGURES / f"map_k{k}.pdf", bbox_inches="tight")
        plt.close(fig)

    log("[9/9] Writing report and run environment")
    write_report(len(keep), len(all_input_units), grid, reporting_family, family_note, kdiag)
    elapsed = time.time() - started
    (OUT / "run_environment.json").write_text(
        json.dumps({
            "allocation": "point_in_polygon_pre_stoparea",
            "input_source": "FYP/旧分析归档/cluster_clean_version_grouped/outputs/preprocessed/bus_lsoa_night_long.parquet (frozen copy 2026-07-29)",
            "n_input_lsoas": int(len(all_input_units)), "n_retained_lsoas": int(len(keep)),
            "elapsed_seconds": elapsed, "seed": SEED, "n_init": N_INIT,
            "clr_pseudocount_alpha": CLR_PSEUDOCOUNT_ALPHA, "min_direction": MIN_DIRECTION,
            "reporting_covariance": reporting_family, "global_bic_covariance": global_family, "global_bic_k": global_k,
            "python": sys.version, "platform": platform.platform(),
        }, indent=2),
        encoding="utf-8",
    )
    log(f"Complete in {elapsed:.1f}s.")


def write_report(n, n_input, grid, family, family_note, kdiag) -> None:
    kdiag_cols = ["K", "BIC", "silhouette", "activity_eta2", "timing_mean_eta2", "direction_balance_eta2",
                  "weekend_ratio_eta2", "min_cluster_share", "bootstrap_ari_mean", "bootstrap_min_cluster_jaccard_mean"]
    best_by_cov = grid.dropna(subset=["BIC"]).sort_values("BIC").groupby("covariance", as_index=False).first()[
        ["covariance", "K", "BIC", "min_cluster_n", "min_cluster_share"]
    ]
    bic_best_k = int(kdiag.loc[kdiag["BIC"].idxmin(), "K"])
    report = f"""# Bus CLR test: point-in-polygon (pre-StopArea) allocation

## Sample and design

Input long table: frozen local copy of the pre-StopArea point-in-polygon
LSOA allocation (`../input/bus_lsoa_night_long_point_in_polygon.parquet`,
copied 2026-07-29 from `FYP/旧分析归档/cluster_clean_version_grouped/
outputs/preprocessed/bus_lsoa_night_long.parquet`). n_input={n_input:,}
LSOAs with any night demand; n_retained={n:,} after the single retention
rule `min(boardings, alightings) full-week total >= 36`.

Feature transform: centered log-ratio (CLR) within each of the two
independent 36-bin (3 day types x 12 hours) direction compositions,
alpha=1 empirical-prior pseudo-count applied only to avoid log(0). Temporal
profile figures are plotted in raw-share space regardless, per this
project's convention that CLR values are not directly interpretable as
"share of activity in this hour".

## BIC result

{best_by_cov.to_markdown(index=False)}

{family_note}

Reporting family: **{family}**.

## K diagnostics

{kdiag[kdiag_cols].to_markdown(index=False, floatfmt=".4f")}

## Comparison across the three allocation methods (CLR, K=3)

| | point-in-polygon (this test) | hub-first (`rq1_bus_clr_transform`) | official StopArea (canonical) |
|---|---:|---:|---:|
| n | {n:,} | 3,365 | 3,372 |
| silhouette | {kdiag.loc[kdiag['K']==3,'silhouette'].iloc[0]:.4f} | 0.1932 | 0.1996 |
| activity_eta2 | {kdiag.loc[kdiag['K']==3,'activity_eta2'].iloc[0]:.4f} | 0.5585 | 0.5578 |
| timing_mean_eta2 | {kdiag.loc[kdiag['K']==3,'timing_mean_eta2'].iloc[0]:.4f} | 0.1893 | 0.1885 |
| direction_balance_eta2 | {kdiag.loc[kdiag['K']==3,'direction_balance_eta2'].iloc[0]:.4f} | 0.0473 | 0.0459 |
| weekend_ratio_eta2 | {kdiag.loc[kdiag['K']==3,'weekend_ratio_eta2'].iloc[0]:.4f} | 0.0512 | 0.0522 |
| bootstrap_ari_mean | {kdiag.loc[kdiag['K']==3,'bootstrap_ari_mean'].iloc[0]:.4f} | 0.8618 | 0.8742 |
| bootstrap_min_cluster_jaccard_mean | {kdiag.loc[kdiag['K']==3,'bootstrap_min_cluster_jaccard_mean'].iloc[0]:.4f} | n/a (not computed) | 0.8830 |

The hub-first and StopArea columns are frozen figures from prior runs, not
recomputed here. If this test's numbers land in the same range, that is
evidence the CLR clustering result is driven by the transform and the
min-direction threshold rather than by the choice of LSOA allocation method.
"""
    (REPORT / "BUS_CLR_TEST_RESULTS.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
