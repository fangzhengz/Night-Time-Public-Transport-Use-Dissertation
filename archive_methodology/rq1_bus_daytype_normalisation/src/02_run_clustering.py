# -*- coding: utf-8 -*-
"""Run the canonical GMM diagnostic battery on one day-type-closure variant.

The grid, covariance families, seed, n_init, bootstrap protocol and eta-squared
definitions are copied verbatim from
`rq1_bus_stoparea_clustering/src/02_run_clustering.py` so that every number
produced here is directly comparable to the adopted run. Two diagnostics are
ADDED because this sidecar exists to answer questions the canonical run does
not ask:

  zero_bin_eta2   how much of a unit's raw zero-cell fraction the partition
                  explains. The 2026-07-23 finding was that canonical CLR
                  scored 0.83-0.92 here against raw_share's 0.54-0.58, i.e.
                  CLR clusters were largely service-continuity tiers. Whether
                  block closure fixes or worsens that is the main open
                  question behind B2/B3.
  ari_vs_canon_*  agreement with the currently adopted labels, on the shared
                  units only.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
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
import config as C


def log(message: str) -> None:
    print(message, flush=True)


def fit_gmm(X: np.ndarray, k: int, covariance: str, seed: int, n_init: int) -> GaussianMixture:
    return GaussianMixture(
        n_components=k,
        covariance_type=covariance,
        n_init=n_init,
        reg_covar=C.REG_COVAR,
        max_iter=C.MAX_ITER,
        random_state=seed,
    ).fit(X)


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


def matched_jaccard(base: np.ndarray, other: np.ndarray, k: int) -> np.ndarray:
    contingency = np.zeros((k, k), dtype=int)
    for left, right in zip(base, other):
        contingency[int(left), int(right)] += 1
    base_sizes = contingency.sum(axis=1, keepdims=True)
    other_sizes = contingency.sum(axis=0, keepdims=True)
    union = base_sizes + other_sizes - contingency
    scores = np.divide(
        contingency, union, out=np.zeros_like(contingency, dtype=float), where=union > 0
    )
    rows, columns = linear_sum_assignment(-scores)
    matched = np.zeros(k, dtype=float)
    matched[rows] = scores[rows, columns]
    return matched


def choose_reporting_family(grid: pd.DataFrame) -> tuple[str, str, int, str]:
    best = grid.loc[grid["BIC"].idxmin()]
    best_family = str(best["covariance"])
    best_k = int(best["K"])
    if best_family != "full" and int(best["min_cluster_n"]) <= 3:
        return (
            "full", best_family, best_k,
            "Global BIC minimum was a near-singleton solution; reporting family overridden to full covariance.",
        )
    return best_family, best_family, best_k, "Global BIC minimum family used directly."


def output_dirs(variant: str) -> dict[str, Path]:
    root = C.OUT / variant
    directories = {
        "root": root,
        "diagnostics": root / "diagnostics",
        "labels": root / "labels",
        "figures": root / "figures",
        "report": root / "report",
        "data": root / "data",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def load_canonical_labels() -> dict[str, pd.Series]:
    out: dict[str, pd.Series] = {}
    for name, path in [
        ("clr_k4", C.CANON_CLR_K4_LABELS),
        ("raw_k3", C.CANON_RAW_K3_LABELS),
    ]:
        if not path.exists():
            log(f"  (canonical {name} labels not found at {path}; ARI skipped)")
            continue
        frame = pd.read_csv(path, dtype={"lsoa": str})
        series = frame.set_index("lsoa")["cluster"]
        out[name] = series[series >= 0]
    return out


def cluster_geography(
    labels_by_k: dict[int, np.ndarray], units: pd.Index, output: dict[str, Path]
) -> pd.DataFrame:
    if not C.LSOA_LAD_LOOKUP.exists():
        return pd.DataFrame()
    lookup = pd.read_csv(C.LSOA_LAD_LOOKUP, usecols=["LSOA21CD", "LAD22CD"])
    lookup["LSOA21CD"] = lookup["LSOA21CD"].astype(str)
    lookup["borough"] = lookup["LAD22CD"].map(C.TARGET_LADS)
    rows: list[dict] = []
    for k in C.CANDIDATE_KS:
        target = pd.DataFrame({"LSOA21CD": units, "cluster": labels_by_k[k]}).merge(
            lookup[["LSOA21CD", "borough"]], on="LSOA21CD", how="left"
        )
        target = target[target["borough"].notna()].copy()
        target["area_group"] = np.where(
            target["borough"].isin(["Westminster", "Camden"]), "central", "outer"
        )
        distributions: dict[str, np.ndarray] = {}
        for group in ["central", "outer"]:
            counts = target.loc[target["area_group"] == group, "cluster"].value_counts()
            values = np.array([counts.get(cluster, 0) for cluster in range(k)], dtype=float)
            distributions[group] = values / values.sum() if values.sum() else values
        central, outer = distributions["central"], distributions["outer"]
        rows.append(
            {
                "K": k,
                "central_outer_total_variation": 0.5 * float(np.abs(central - outer).sum()),
                "central_outer_same_cluster_probability": float(np.dot(central, outer)),
            }
        )
    result = pd.DataFrame(rows)
    result.to_csv(output["data"] / "central_outer_diagnostic.csv", index=False)
    return result


def make_profiles(
    variant: str, labels_by_k: dict[int, np.ndarray], units: pd.Index, output: dict[str, Path]
) -> None:
    """Profiles are drawn in DAY-TYPE SHARE space, which is this variant's own
    feature space -- unlike the canonical script, which redraws CLR clusters in
    raw-share space for interpretability."""
    share = pd.read_parquet(C.FEATURES / "X_daytype_raw_share.parquet")
    share.index = pd.Index(share.index.astype(str), name="lsoa")
    share = share.loc[units]
    for k in C.FIGURE_KS:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        fig, axes = plt.subplots(k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True)
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            means = share.loc[labels == cluster].mean(axis=0)
            for day_index, day_type in enumerate(C.DAY_TYPES):
                ax = axes[cluster, day_index]
                for direction, color in [("boardings", "#0072B2"), ("alightings", "#D55E00")]:
                    values = [means[f"{direction}_{day_type}_{hour}"] for hour in C.HOURS]
                    ax.plot(range(12), values, marker="o", markersize=2, color=color, label=direction)
                if cluster == 0:
                    ax.set_title(day_type)
                if day_index == 0:
                    ax.set_ylabel(
                        f"C{cluster}\nn={int(sizes[cluster]):,} ({sizes[cluster]/sizes.sum()*100:.1f}%)",
                        color=C.CLUSTER_COLOURS[cluster % len(C.CLUSTER_COLOURS)],
                        fontweight="bold", fontsize=9,
                    )
                ax.grid(alpha=0.2)
        axes[-1, 1].set_xticks(
            range(12),
            ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"],
            rotation=45,
        )
        axes[0, -1].legend(loc="upper right", fontsize=8)
        fig.suptitle(
            f"Day-type closure, {variant}, K={k}\n"
            "each panel is that day type's own share of the direction's day-type total",
            y=1.01,
        )
        fig.tight_layout()
        fig.savefig(output["figures"] / f"profiles_k{k}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)


def run_variant(variant: str, bootstrap_n: int, n_init: int) -> None:
    started = time.time()
    spec = C.VARIANTS[variant]
    output = output_dirs(variant)
    feature_path = C.FEATURES / f"X_{variant}.parquet"
    if not feature_path.exists():
        raise FileNotFoundError(f"Missing {feature_path}; run 01_prepare_features.py first.")

    X_frame = pd.read_parquet(feature_path)
    X_frame.index = pd.Index(X_frame.index.astype(str), name="lsoa")
    X = X_frame.to_numpy(dtype=float)
    if not np.isfinite(X).all() or X.shape[1] != 72:
        raise RuntimeError(f"Invalid feature matrix: shape={X.shape}")

    all_metrics = pd.read_csv(C.SAMPLE_METRICS, dtype={"lsoa": str}).set_index("lsoa")
    metrics = all_metrics.loc[X_frame.index]
    zeros = pd.read_csv(C.FEATURES / "zero_bin_share.csv", dtype={"lsoa": str}).set_index("lsoa")
    metrics = metrics.join(zeros["zero_bin_share"])

    canonical = load_canonical_labels()

    log(f"[{variant}] fitting 4 covariance families x K=2..12; n={len(X)}, n_init={n_init}")
    grid_rows: list[dict] = []
    grid_labels: dict[tuple[str, int], np.ndarray] = {}
    for covariance in C.COVARIANCES:
        for k in C.K_RANGE:
            fit_started = time.perf_counter()
            model = fit_gmm(X, k, covariance, C.SEED, n_init)
            seconds = time.perf_counter() - fit_started
            labels = model.predict(X).astype(int)
            grid_labels[(covariance, k)] = labels
            sizes = np.bincount(labels, minlength=k)
            grid_rows.append(
                {
                    "covariance": covariance, "K": k,
                    "BIC": float(model.bic(X)), "AIC": float(model.aic(X)),
                    "converged": bool(model.converged_), "fit_seconds": seconds,
                    "min_cluster_n": int(sizes.min()),
                    "min_cluster_share": float(sizes.min() / sizes.sum()),
                }
            )
            log(f"  {covariance:9s} K={k:2d} BIC={grid_rows[-1]['BIC']:.1f} "
                f"min_n={int(sizes.min()):4d} ({seconds:.1f}s)")
    grid = pd.DataFrame(grid_rows)
    grid.to_csv(output["diagnostics"] / "bic_grid.csv", index=False)
    reporting_family, global_family, global_k, family_note = choose_reporting_family(grid)
    log(f"[{variant}] reporting covariance={reporting_family}; {family_note}")
    labels_by_k = {k: grid_labels[(reporting_family, k)] for k in C.K_RANGE}

    kdiag_rows: list[dict] = []
    for k in C.K_RANGE:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        grid_row = grid[(grid["covariance"] == reporting_family) & (grid["K"] == k)].iloc[0]
        row = {
            "K": k,
            "BIC": float(grid_row["BIC"]),
            "silhouette": float(silhouette_score(X, labels)),
            "davies_bouldin": float(davies_bouldin_score(X, labels)),
            "activity_eta2": eta_squared(metrics["log_total_activity"], labels),
            "zero_bin_eta2": eta_squared(metrics["zero_bin_share"], labels),
            "min_cluster_share": float(sizes.min() / sizes.sum()),
        }
        for metric in C.TIMING_METRICS + ["direction_balance", "weekend_ratio"]:
            values = metrics[metric]
            mask = values.notna()
            row[f"{metric}_eta2"] = eta_squared(values[mask], labels[mask.to_numpy()])
        row["timing_mean_eta2"] = float(
            np.mean([row[f"{metric}_eta2"] for metric in C.TIMING_METRICS])
        )
        labels_series = pd.Series(labels, index=X_frame.index)
        for name, canon in canonical.items():
            shared = labels_series.index.intersection(canon.index)
            row[f"ari_vs_canon_{name}"] = float(
                adjusted_rand_score(canon.loc[shared], labels_series.loc[shared])
            )
            row[f"n_shared_{name}"] = int(len(shared))
        kdiag_rows.append(row)

        label_frame = all_metrics[
            ["retained_for_fit", "min_direction_activity", "exclusion_reason"]
        ].copy()
        label_frame["cluster"] = -1
        label_frame.loc[X_frame.index, "cluster"] = labels
        label_frame.reset_index().to_csv(output["labels"] / f"k{k}_labels.csv", index=False)
    kdiag = pd.DataFrame(kdiag_rows)

    log(f"[{variant}] bootstrap K={C.BOOTSTRAP_KS}, replicates={bootstrap_n}")
    rng = np.random.default_rng(C.SEED)
    bootstrap_rows: list[dict] = []
    for k in C.BOOTSTRAP_KS:
        base = labels_by_k[k]
        for replicate in range(bootstrap_n):
            sample = rng.choice(len(X), size=len(X), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model = fit_gmm(X[sample], k, reporting_family, seed, C.BOOTSTRAP_N_INIT)
            other = model.predict(X)
            matched = matched_jaccard(base, other, k)
            bootstrap_rows.append(
                {
                    "K": k, "replicate": replicate + 1,
                    "ARI": float(adjusted_rand_score(base, other)),
                    "min_matched_cluster_jaccard": float(matched.min()),
                }
            )
        sub = pd.DataFrame(bootstrap_rows)
        sub = sub[sub["K"] == k]
        log(f"  K={k}: ARI mean={sub['ARI'].mean():.3f}; "
            f"min Jaccard mean={sub['min_matched_cluster_jaccard'].mean():.3f}")
    bootstrap = pd.DataFrame(bootstrap_rows)
    bootstrap.to_csv(output["diagnostics"] / "bootstrap.csv", index=False)
    boot_summary = bootstrap.groupby("K", as_index=False).agg(
        bootstrap_ari_mean=("ARI", "mean"),
        bootstrap_ari_sd=("ARI", "std"),
        bootstrap_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
    )
    kdiag = kdiag.merge(boot_summary, on="K", how="left")
    kdiag.to_csv(output["diagnostics"] / "kdiag.csv", index=False)

    grand_centroid = X.mean(axis=0)
    grand_distance = float(np.linalg.norm(X - grand_centroid, axis=1).mean())
    homogeneity_rows: list[dict] = []
    for k in C.CANDIDATE_KS:
        labels = labels_by_k[k]
        silhouettes = silhouette_samples(X, labels)
        for cluster in range(k):
            mask = labels == cluster
            members = X[mask]
            distances = np.linalg.norm(members - members.mean(axis=0), axis=1)
            homogeneity_rows.append(
                {
                    "K": k, "cluster": cluster,
                    "n": int(mask.sum()), "share": float(mask.mean()),
                    "mean_silhouette": float(silhouettes[mask].mean()),
                    "relative_compactness_vs_sample": float(distances.mean() / grand_distance),
                    "mean_log_total_activity": float(
                        metrics.iloc[np.flatnonzero(mask)]["log_total_activity"].mean()
                    ),
                    "mean_post_midnight_share": float(
                        metrics.iloc[np.flatnonzero(mask)]["post_midnight_share"].mean()
                    ),
                    "mean_zero_bin_share": float(
                        metrics.iloc[np.flatnonzero(mask)]["zero_bin_share"].mean()
                    ),
                }
            )
    homogeneity = pd.DataFrame(homogeneity_rows)
    homogeneity.to_csv(output["diagnostics"] / "cluster_homogeneity.csv", index=False)

    geography = cluster_geography(labels_by_k, X_frame.index, output)
    make_profiles(variant, labels_by_k, X_frame.index, output)

    fig, ax = plt.subplots(figsize=(8, 5))
    for covariance in C.COVARIANCES:
        sub = grid[grid["covariance"] == covariance]
        ax.plot(sub["K"], sub["BIC"], marker="o", label=covariance)
    ax.set(xlabel="K", ylabel="BIC", title=f"Day-type closure {variant}: BIC grid")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output["figures"] / "bic_grid.png", dpi=180)
    plt.close(fig)

    elapsed = time.time() - started
    environment = {
        "variant": variant,
        "closure": "per (direction, day_type) 12-bin block",
        "kind": spec["kind"], "alpha": spec["alpha"], "strict_sample": spec["strict"],
        "elapsed_seconds": elapsed,
        "n_lsoas": len(X), "n_features": int(X.shape[1]),
        "seed": C.SEED, "n_init": n_init, "bootstrap_replicates": bootstrap_n,
        "reporting_covariance": reporting_family,
        "global_bic_covariance": global_family, "global_bic_k": global_k,
        "python": sys.version, "platform": platform.platform(),
    }
    (output["root"] / "run_environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )

    report = [
        f"# Day-type closure sidecar: {variant}",
        "",
        "## Specification",
        "",
        f"- Closure: each (direction, day_type) 12-bin block sums to 1 independently.",
        f"- Kind: {spec['kind']}"
        + (f", CLR alpha={spec['alpha']}, block-internal empirical prior." if spec["kind"] == "clr" else "."),
        f"- Sample: {len(X):,} LSOAs"
        + (f" (strict: every block >= {C.STRICT_MIN_BLOCK:g})." if spec["strict"]
           else f" (canonical retention: both direction week totals >= {C.MIN_DIRECTION:g})."),
        f"- Features: {X.shape[1]}.",
        f"- GMM grid: K=2..12, covariance={C.COVARIANCES}, n_init={n_init}, seed={C.SEED}.",
        f"- Reporting covariance: {reporting_family}. {family_note}",
        f"- Global BIC grid minimum: covariance={global_family}, K={global_k}.",
        "",
        "## K diagnostics",
        "",
        kdiag.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Candidate-cluster homogeneity",
        "",
        homogeneity.to_markdown(index=False, floatfmt=".6f"),
        "",
    ]
    if not geography.empty:
        report.extend(
            ["## Central-versus-outer diagnostic", "",
             geography.to_markdown(index=False, floatfmt=".6f"), ""]
        )
    report.extend(
        [
            "## Interpretation boundary",
            "",
            "A sidecar test of the normalisation denominator only. It does not "
            "re-open allocation, retention (except in the strict variant, where "
            "that is the point), window, or granularity, and it is not an adopted "
            "result until the comparison in `outputs/comparison` is reviewed.",
        ]
    )
    (output["report"] / "RESULTS.md").write_text("\n".join(report), encoding="utf-8")
    log(f"[{variant}] complete in {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=sorted(C.VARIANTS), required=True)
    parser.add_argument("--bootstrap", type=int, default=20)
    parser.add_argument("--n-init", type=int, default=C.N_INIT)
    args = parser.parse_args()
    if args.bootstrap < 1 or args.n_init < 1:
        parser.error("--bootstrap and --n-init must be positive")
    run_variant(args.variant, args.bootstrap, args.n_init)


if __name__ == "__main__":
    main()
