"""ILR-coordinate validation of rq1_bus_clr_transform.

The sample, empirical-prior zero handling and GMM settings are fixed to the CLR
run. Each 36-part direction composition is expressed in a 35-coordinate Helmert
ILR basis. A full-SVD PCA then removes only exact zero-variance directions from
the observed ILR sample; all non-zero variance is retained for fitting.
"""

from __future__ import annotations

import argparse
import hashlib
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
from scipy.linalg import helmert
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent
UPSTREAM = FYP / "rq1_bus_hub_first_reorganisation"
CLR_ROOT = FYP / "rq1_bus_clr_transform"

LONG_INPUT = UPSTREAM / "outputs" / "preprocessed" / "bus_lsoa_night_long.parquet"
EXCEPTION_INPUT = UPSTREAM / "outputs" / "data" / "one_direction_exception_areas.csv"
OFFICIAL_UNITS_REFERENCE = FYP / "巴士聚类错误修改" / "outputs" / "features" / "X_bus_fullweek_alpha0.parquet"
CLR_FEATURE_REFERENCE = CLR_ROOT / "outputs" / "features" / "X_bus_fullweek_clr.parquet"

OUT = ROOT / "outputs"
FEATURES = OUT / "features"
DIAGNOSTICS = OUT / "diagnostics"
LABELS = OUT / "labels"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
MODELS = OUT / "models"
DATA = OUT / "data"
RUN_LOG = ROOT / "run_01.log"
for path in (OUT, FEATURES, DIAGNOSTICS, LABELS, FIGURES, REPORT, MODELS, DATA):
    path.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
HOURS = list(range(1080, 1800, 60))
K_RANGE = list(range(2, 13))
CANDIDATE_KS = [3, 4]
BOOTSTRAP_KS = [2, 3, 4, 5]
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
BOOTSTRAP_N_INIT = 3
REG_COVAR = 1e-6
MAX_ITER = 300
SEED = 42
MIN_TOTAL = 50.0
WEAK_DIRECTION_MIN = 36.0
PSEUDOCOUNT_ALPHA = 1.0
TIMING_METRICS = ["post_midnight_share", "deep_night_share", "post_midnight_persistence"]


def log(message: str) -> None:
    print(message, flush=True)
    with RUN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_input_manifest() -> None:
    paths = {
        "hub_first_lsoa_long": LONG_INPUT,
        "one_direction_exceptions": EXCEPTION_INPUT,
        "official_raw_sample_reference": OFFICIAL_UNITS_REFERENCE,
        "clr_feature_reference": CLR_FEATURE_REFERENCE,
        "clr_k3_reference": CLR_ROOT / "outputs" / "labels" / "clr_k3_labels.csv",
        "clr_k4_reference": CLR_ROOT / "outputs" / "labels" / "clr_k4_labels.csv",
    }
    rows = []
    for role, path in paths.items():
        exists = path.exists()
        rows.append(
            {
                "role": role,
                "path": str(path.resolve()),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else np.nan,
                "sha256": sha256(path) if exists else "",
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(OUT / "input_manifest.csv", index=False)
    if not manifest.loc[manifest["role"].isin(["hub_first_lsoa_long", "one_direction_exceptions"]), "exists"].all():
        raise FileNotFoundError("A required ILR input is missing; see outputs/input_manifest.csv")


def fit_gmm(X: np.ndarray, k: int, covariance: str, seed: int, n_init: int) -> GaussianMixture:
    return GaussianMixture(
        n_components=k,
        covariance_type=covariance,
        n_init=n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=seed,
    ).fit(X)


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = float(y.mean())
    total = float(np.square(y - grand).sum())
    if total <= 0:
        return float("nan")
    between = sum(
        int((labels == cluster).sum()) * (float(y[labels == cluster].mean()) - grand) ** 2
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
    scores = np.divide(contingency, union, out=np.zeros_like(contingency, dtype=float), where=union > 0)
    rows, cols = linear_sum_assignment(-scores)
    matched = np.zeros(k, dtype=float)
    matched[rows] = scores[rows, cols]
    return matched


def build_sample_and_raw_metrics() -> tuple[pd.Index, dict[str, pd.DataFrame], pd.DataFrame]:
    long = pd.read_parquet(LONG_INPUT).copy()
    long["lsoa"] = long["lsoa"].astype(str)
    long["hour_bin"] = long["hour_bin"].astype(int)
    exceptions = set(pd.read_csv(EXCEPTION_INPUT)["lsoa"].astype(str).unique())

    grouped = long.groupby(
        ["lsoa", "day_type", "direction", "hour_bin"], as_index=False, observed=True
    )["count"].sum()
    full_totals = long.groupby("lsoa", observed=True)["count"].sum().rename("total_activity")
    direction_totals = grouped.groupby(["lsoa", "direction"], observed=True)["count"].sum().unstack(fill_value=0.0)
    for direction in DIRECTIONS:
        if direction not in direction_totals.columns:
            direction_totals[direction] = 0.0
    min_direction = direction_totals[DIRECTIONS].min(axis=1)
    keep = pd.Index(
        sorted(
            set(full_totals.index[full_totals >= MIN_TOTAL].astype(str))
            & set(min_direction.index[min_direction >= WEAK_DIRECTION_MIN].astype(str))
            - exceptions
        ),
        name="lsoa",
    )

    if OFFICIAL_UNITS_REFERENCE.exists():
        reference_units = set(pd.read_parquet(OFFICIAL_UNITS_REFERENCE).index.astype(str))
        if set(keep) != reference_units:
            raise ValueError("Rebuilt ILR sample does not match the official 3,365-LSOA sample")
        log(f"      Verified exact sample match: {len(reference_units)} LSOAs")

    raw_counts: dict[str, pd.DataFrame] = {}
    for direction in DIRECTIONS:
        pieces = []
        for day_type in DAY_TYPES:
            sub = grouped[(grouped["day_type"] == day_type) & (grouped["direction"] == direction)]
            wide = sub.pivot_table(index="lsoa", columns="hour_bin", values="count", aggfunc="sum", fill_value=0.0)
            wide = wide.reindex(index=keep, columns=HOURS, fill_value=0.0).astype(float)
            wide.columns = [f"{direction}_{day_type}_{hour}" for hour in HOURS]
            pieces.append(wide)
        raw_counts[direction] = pd.concat(pieces, axis=1)

    raw = long[long["lsoa"].isin(set(keep))]
    total = raw.groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    direction_raw = raw.groupby(["lsoa", "direction"], observed=True)["count"].sum().unstack(fill_value=0.0).reindex(index=keep, columns=DIRECTIONS, fill_value=0.0)
    post_midnight = raw.loc[raw["hour_bin"].between(1440, 1799)].groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    deep_night = raw.loc[raw["hour_bin"].between(1620, 1799)].groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    evening = raw.loc[raw["hour_bin"].between(1080, 1259)].groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    day_total = raw.groupby(["lsoa", "day_type"], observed=True)["count"].sum().unstack(fill_value=0.0).reindex(index=keep, columns=DAY_TYPES, fill_value=0.0)

    metrics = pd.DataFrame(index=keep)
    metrics["total_activity"] = total
    metrics["log_total_activity"] = np.log1p(total)
    metrics["direction_balance"] = (direction_raw["boardings"] - direction_raw["alightings"]) / total
    metrics["post_midnight_share"] = post_midnight / total
    metrics["deep_night_share"] = deep_night / total
    metrics["post_midnight_persistence"] = post_midnight / evening.replace(0.0, np.nan)
    metrics["weekend_ratio"] = day_total[["Saturday", "Sunday"]].mean(axis=1) / day_total["Weekday"].replace(0.0, np.nan)
    metrics["zero_bin_count"] = sum((raw_counts[direction] == 0).sum(axis=1) for direction in DIRECTIONS)
    return keep, raw_counts, metrics


def build_ilr_features(
    keep: pd.Index, raw_counts: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float | int]]:
    basis = helmert(36, full=False)
    if basis.shape != (35, 36):
        raise ValueError(f"Unexpected Helmert basis shape: {basis.shape}")
    if not np.allclose(basis @ basis.T, np.eye(35), atol=1e-12):
        raise ValueError("Helmert rows are not orthonormal")
    if not np.allclose(basis @ np.ones(36), 0.0, atol=1e-12):
        raise ValueError("Helmert basis is not orthogonal to the closure direction")
    pd.DataFrame(basis, index=[f"balance_{i:02d}" for i in range(1, 36)]).to_csv(DATA / "helmert_ilr_basis_36.csv")

    ilr_blocks = []
    clr_blocks = []
    for direction in DIRECTIONS:
        counts = raw_counts[direction].to_numpy(dtype=float)
        totals = counts.sum(axis=1)
        prior = counts.sum(axis=0) / counts.sum()
        posterior = (counts + PSEUDOCOUNT_ALPHA * prior) / (totals[:, None] + PSEUDOCOUNT_ALPHA)
        if not np.all(posterior > 0):
            raise ValueError(f"Non-positive posterior share in {direction}")
        logp = np.log(posterior)
        clr = logp - logp.mean(axis=1, keepdims=True)
        ilr = logp @ basis.T
        clr_blocks.append(clr)
        ilr_blocks.append(
            pd.DataFrame(
                ilr,
                index=keep,
                columns=[f"{direction}_ilr_{i:02d}" for i in range(1, 36)],
            )
        )

    X_ilr70 = pd.concat(ilr_blocks, axis=1)
    X_ilr70.to_parquet(FEATURES / "X_bus_fullweek_ilr70.parquet")
    centered = X_ilr70.to_numpy(dtype=float) - X_ilr70.to_numpy(dtype=float).mean(axis=0, keepdims=True)
    rank = int(np.linalg.matrix_rank(centered))
    pca = PCA(n_components=rank, svd_solver="full")
    rank_values = pca.fit_transform(X_ilr70.to_numpy(dtype=float))
    X_rank = pd.DataFrame(
        rank_values,
        index=keep,
        columns=[f"ilr_pc_{i:03d}" for i in range(1, rank + 1)],
    )
    X_rank.to_parquet(FEATURES / f"X_bus_fullweek_ilr_rank{rank}.parquet")
    np.savez(
        MODELS / "ilr_rank_projection.npz",
        components=pca.components_,
        mean=pca.mean_,
        explained_variance=pca.explained_variance_,
        singular_values=pca.singular_values_,
    )

    clr72 = np.concatenate(clr_blocks, axis=1)
    rng = np.random.default_rng(SEED)
    left = rng.integers(0, len(keep), size=20000)
    right = rng.integers(0, len(keep), size=20000)
    d_clr = np.linalg.norm(clr72[left] - clr72[right], axis=1)
    ilr70_values = X_ilr70.to_numpy(dtype=float)
    d_ilr = np.linalg.norm(ilr70_values[left] - ilr70_values[right], axis=1)
    d_rank = np.linalg.norm(rank_values[left] - rank_values[right], axis=1)
    audit: dict[str, float | int] = {
        "n_lsoa": len(keep),
        "clr_columns": 72,
        "ilr_columns": 70,
        "centered_ilr_rank": rank,
        "retained_variance_fraction": float(pca.explained_variance_ratio_.sum()),
        "max_sampled_distance_error_clr_vs_ilr70": float(np.max(np.abs(d_clr - d_ilr))),
        "max_sampled_distance_error_ilr70_vs_rank": float(np.max(np.abs(d_ilr - d_rank))),
        "min_retained_explained_variance": float(pca.explained_variance_.min()),
    }
    if CLR_FEATURE_REFERENCE.exists():
        clr_ref = pd.read_parquet(CLR_FEATURE_REFERENCE).loc[keep].to_numpy(dtype=float)
        audit["max_abs_rebuilt_clr_vs_saved_clr"] = float(np.max(np.abs(clr72 - clr_ref)))
    (DIAGNOSTICS / "ilr_coordinate_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if audit["max_sampled_distance_error_clr_vs_ilr70"] > 1e-9 or audit["max_sampled_distance_error_ilr70_vs_rank"] > 1e-9:
        raise ValueError(f"ILR distance preservation failed: {audit}")
    return X_ilr70, X_rank, audit


def run_bic_grid(X: np.ndarray) -> tuple[pd.DataFrame, str, int]:
    rows = []
    for covariance in COVARIANCES:
        for k in K_RANGE:
            started = time.perf_counter()
            model = fit_gmm(X, k, covariance, SEED, N_INIT)
            labels = model.predict(X)
            sizes = np.bincount(labels, minlength=k)
            rows.append(
                {
                    "covariance": covariance,
                    "K": k,
                    "BIC": float(model.bic(X)),
                    "AIC": float(model.aic(X)),
                    "converged": bool(model.converged_),
                    "fit_seconds": time.perf_counter() - started,
                    "min_cluster_n": int(sizes.min()),
                    "min_cluster_share": float(sizes.min() / sizes.sum()),
                }
            )
            pd.DataFrame(rows).to_csv(DIAGNOSTICS / "ilr_bic_grid.partial.csv", index=False)
            log(f"      {covariance:9s} K={k:2d} BIC={rows[-1]['BIC']:.1f} min_n={rows[-1]['min_cluster_n']:4d}")
    grid = pd.DataFrame(rows)
    grid.to_csv(DIAGNOSTICS / "ilr_bic_grid.csv", index=False)
    best = grid.loc[grid["BIC"].idxmin()]
    return grid, str(best["covariance"]), int(best["K"])


def choose_reporting_family(grid: pd.DataFrame, global_covariance: str, global_k: int) -> tuple[str, str]:
    best = grid[(grid["covariance"] == global_covariance) & (grid["K"] == global_k)].iloc[0]
    if global_covariance != "full" and best["min_cluster_n"] <= 3:
        return "full", f"Global BIC minimum {global_covariance}, K={global_k} was near-degenerate; reporting family fixed to full."
    return global_covariance, "Global BIC minimum family used directly; no override needed."


def compare_to_clr(keep: pd.Index, labels_by_k: dict[int, np.ndarray]) -> pd.DataFrame:
    rows = []
    for k in CANDIDATE_KS:
        path = CLR_ROOT / "outputs" / "labels" / f"clr_k{k}_labels.csv"
        if not path.exists():
            continue
        reference = pd.read_csv(path)
        reference["unit"] = reference["unit"].astype(str)
        reference_labels = reference.set_index("unit").loc[keep, "cluster"].to_numpy(dtype=int)
        rows.append({"K": k, "ARI_ilr_vs_clr": float(adjusted_rand_score(reference_labels, labels_by_k[k]))})
    comparison = pd.DataFrame(rows)
    comparison.to_csv(DIAGNOSTICS / "ilr_vs_clr_labels.csv", index=False)
    return comparison


def write_report(
    n: int,
    rank: int,
    audit: dict[str, float | int],
    grid: pd.DataFrame,
    family: str,
    family_note: str,
    kdiag: pd.DataFrame,
    homogeneity: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    best_by_cov = grid.sort_values("BIC").groupby("covariance", as_index=False).first()[
        ["covariance", "K", "BIC", "min_cluster_n", "min_cluster_share"]
    ]
    bic_best_k = int(kdiag.loc[kdiag["BIC"].idxmin(), "K"])
    kdiag_cols = [
        "K", "BIC", "silhouette", "davies_bouldin", "activity_eta2", "zero_bin_eta2",
        "timing_mean_eta2", "min_cluster_share", "bootstrap_ari_mean",
        "bootstrap_min_cluster_jaccard_mean",
    ]
    homog_cols = [
        "K", "cluster", "n", "share", "mean_silhouette", "relative_compactness_vs_sample",
        "zero_bin_count_mean", "log_total_activity_mean", "post_midnight_share_mean",
    ]
    report = f"""# ILR-coordinate bus clustering: results

## Material Passport

- Mode: deterministic feature reconstruction plus stochastic GMM/bootstrap
- Input sample: {n:,} LSOAs, exact match to CLR and official raw-share sample
- Zero handling: same empirical-prior posterior, alpha={PSEUDOCOUNT_ALPHA}
- Standard ILR coordinates: 70
- Retained non-zero sample-space dimensions: {rank}
- Existing CLR outputs modified: no

## Coordinate audit

```json
{json.dumps(audit, indent=2)}
```

The standard Helmert ILR and rank-reduced fitted coordinates preserve the same
Aitchison/CLR sample distances. Absolute BIC values must not be compared with
the old redundant 72-column CLR fit because the fitted dimensionality differs.

## BIC grid summary

{best_by_cov.to_markdown(index=False, floatfmt=".4f")}

{family_note}

Reporting family: **{family}**. BIC-preferred K within this family: **{bic_best_k}**.

## K diagnostics

{kdiag[kdiag_cols].to_markdown(index=False, floatfmt=".4f")}

## Direct label comparison with CLR

{comparison.to_markdown(index=False, floatfmt=".6f") if not comparison.empty else "CLR reference labels unavailable."}

## Per-cluster diagnostics

{homogeneity[homog_cols].to_markdown(index=False, floatfmt=".4f")}

## Interpretation boundary

ILR is a non-redundant coordinate expression of the same posterior compositions,
not a new substantive feature definition. Similar labels are expected when the
same full-covariance model optimum is recovered. A difference would indicate a
numerical/regularisation effect, not new passenger information.
"""
    (REPORT / "ILR_RESULTS.md").write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", type=int, default=20)
    args = parser.parse_args()
    started = time.time()
    RUN_LOG.write_text("", encoding="utf-8")
    write_input_manifest()

    log("[1/8] Rebuilding fixed sample and raw counts")
    keep, raw_counts, metrics = build_sample_and_raw_metrics()
    metrics.to_csv(FEATURES / "raw_metrics.csv")

    log("[2/8] Building Helmert ILR and exact-rank fitted coordinates")
    _, X_rank, audit = build_ilr_features(keep, raw_counts)
    X = X_rank.to_numpy(dtype=float)
    rank = X.shape[1]
    log(f"      n={len(keep)}, ILR70 -> retained rank={rank}, distance error={audit['max_sampled_distance_error_ilr70_vs_rank']:.3e}")

    log("[3/8] Running 4-covariance x K=2..12 BIC grid")
    grid, global_covariance, global_k = run_bic_grid(X)
    family, family_note = choose_reporting_family(grid, global_covariance, global_k)
    log(f"      {family_note}")

    log(f"[4/8] K diagnostics at covariance={family}")
    rows = []
    labels_by_k: dict[int, np.ndarray] = {}
    for k in K_RANGE:
        model = fit_gmm(X, k, family, SEED, N_INIT)
        labels = model.predict(X)
        labels_by_k[k] = labels
        sizes = np.bincount(labels, minlength=k)
        row = {
            "K": k,
            "BIC": float(model.bic(X)),
            "silhouette": float(silhouette_score(X, labels)),
            "davies_bouldin": float(davies_bouldin_score(X, labels)),
            "activity_eta2": eta_squared(metrics["log_total_activity"], labels),
            "zero_bin_eta2": eta_squared(metrics["zero_bin_count"], labels),
            "min_cluster_share": float(sizes.min() / sizes.sum()),
        }
        for metric in TIMING_METRICS + ["direction_balance", "weekend_ratio"]:
            valid = metrics[metric].notna()
            row[f"{metric}_eta2"] = eta_squared(metrics.loc[valid, metric], labels[valid.to_numpy()])
        row["timing_mean_eta2"] = float(np.mean([row[f"{metric}_eta2"] for metric in TIMING_METRICS]))
        rows.append(row)
        pd.DataFrame({"unit": keep, "cluster": labels}).to_csv(LABELS / f"ilr_k{k}_labels.csv", index=False)
        log(f"      K={k:2d} sil={row['silhouette']:.3f} activity_eta2={row['activity_eta2']:.3f} zero_eta2={row['zero_bin_eta2']:.3f}")
    kdiag = pd.DataFrame(rows)

    log(f"[5/8] Bootstrap stability for K={BOOTSTRAP_KS}, n={args.bootstrap}")
    rng = np.random.default_rng(SEED)
    boot_rows = []
    for k in BOOTSTRAP_KS:
        base = labels_by_k[k]
        for replicate in range(args.bootstrap):
            idx = rng.choice(len(X), size=len(X), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model = fit_gmm(X[idx], k, family, seed, BOOTSTRAP_N_INIT)
            other = model.predict(X)
            matched = matched_jaccard(base, other, k)
            boot_rows.append(
                {
                    "K": k,
                    "replicate": replicate + 1,
                    "ARI": float(adjusted_rand_score(base, other)),
                    "min_matched_cluster_jaccard": float(matched.min()),
                }
            )
        sub = pd.DataFrame(boot_rows)
        sub = sub[sub["K"] == k]
        log(f"      K={k}: ARI={sub['ARI'].mean():.3f}, min Jaccard={sub['min_matched_cluster_jaccard'].mean():.3f}")
    bootstrap = pd.DataFrame(boot_rows)
    bootstrap.to_csv(DIAGNOSTICS / "ilr_bootstrap.csv", index=False)
    boot_summary = bootstrap.groupby("K", as_index=False).agg(
        bootstrap_ari_mean=("ARI", "mean"),
        bootstrap_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
    )
    kdiag = kdiag.merge(boot_summary, on="K", how="left")
    kdiag.to_csv(DIAGNOSTICS / "ilr_kdiag.csv", index=False)

    log("[6/8] Per-cluster diagnostics and CLR label comparison")
    grand_centroid = X.mean(axis=0)
    grand_mean_distance = float(np.linalg.norm(X - grand_centroid, axis=1).mean())
    homogeneity_rows = []
    for k in CANDIDATE_KS:
        labels = labels_by_k[k]
        sil = silhouette_samples(X, labels)
        for cluster in range(k):
            mask = labels == cluster
            members = X[mask]
            dist = np.linalg.norm(members - members.mean(axis=0), axis=1)
            homogeneity_rows.append(
                {
                    "K": k,
                    "cluster": cluster,
                    "n": int(mask.sum()),
                    "share": float(mask.mean()),
                    "mean_silhouette": float(sil[mask].mean()),
                    "relative_compactness_vs_sample": float(dist.mean() / grand_mean_distance),
                    "zero_bin_count_mean": float(metrics.loc[mask, "zero_bin_count"].mean()),
                    "log_total_activity_mean": float(metrics.loc[mask, "log_total_activity"].mean()),
                    "post_midnight_share_mean": float(metrics.loc[mask, "post_midnight_share"].mean()),
                }
            )
    homogeneity = pd.DataFrame(homogeneity_rows)
    homogeneity.to_csv(DIAGNOSTICS / "ilr_cluster_homogeneity.csv", index=False)
    comparison = compare_to_clr(keep, labels_by_k)
    log("      " + comparison.to_dict(orient="records").__repr__())

    log("[7/8] Writing primary figures and report")
    fig, ax = plt.subplots(figsize=(8, 5))
    for covariance in COVARIANCES:
        sub = grid[grid["covariance"] == covariance]
        ax.plot(sub["K"], sub["BIC"], marker="o", label=covariance)
    ax.set(xlabel="K", ylabel="BIC", title=f"ILR rank-{rank} features: BIC grid")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "ilr_bic_grid.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].plot(kdiag["K"], kdiag["silhouette"], marker="o")
    axes[0].set_title(f"Silhouette (ILR rank-{rank})")
    axes[1].plot(kdiag["K"], kdiag["activity_eta2"], marker="o", label="activity")
    axes[1].plot(kdiag["K"], kdiag["zero_bin_eta2"], marker="^", label="zero-bin count")
    axes[1].plot(kdiag["K"], kdiag["timing_mean_eta2"], marker="s", label="timing mean")
    axes[1].set_title("Between-group eta2")
    axes[1].legend()
    axes[2].plot(kdiag["K"], kdiag["bootstrap_ari_mean"], marker="o")
    axes[2].set_title("Bootstrap ARI")
    for axis in axes:
        axis.set_xlabel("K")
        axis.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "ilr_k_diagnostics.png", dpi=180)
    plt.close(fig)
    write_report(len(keep), rank, audit, grid, family, family_note, kdiag, homogeneity, comparison)

    elapsed = time.time() - started
    environment = {
        "command": f"python src\\01_run_ilr_clustering.py --bootstrap {args.bootstrap}",
        "elapsed_seconds": elapsed,
        "seed": SEED,
        "n_init": N_INIT,
        "bootstrap_n_init": BOOTSTRAP_N_INIT,
        "bootstrap_replicates": args.bootstrap,
        "pseudocount_alpha": PSEUDOCOUNT_ALPHA,
        "python": sys.version,
        "platform": platform.platform(),
    }
    (OUT / "run_environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    log(f"[8/8] Complete in {elapsed:.1f}s: {REPORT / 'ILR_RESULTS.md'}")


if __name__ == "__main__":
    main()
