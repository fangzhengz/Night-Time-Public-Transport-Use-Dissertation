from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


ROOT = Path(__file__).resolve().parents[1]
FYP = ROOT.parent
BASE = FYP / "rq1_bus_hub_first_reclustering"
BASE_SRC = BASE / "src"
sys.path.insert(0, str(BASE_SRC))
import config as base_config
import run_fullweek_first_pass as base


OUT = ROOT / "outputs"
FEATURES = OUT / "features"
DIAGNOSTICS = OUT / "diagnostics"
LABELS = OUT / "labels"
REPORT = OUT / "report"
for path in (OUT, FEATURES, DIAGNOSTICS, LABELS, REPORT):
    path.mkdir(parents=True, exist_ok=True)

LONG_INPUT = base_config.LONG_INPUT
ALPHA5_X = BASE / "outputs" / "features" / "X_bus_fullweek_alpha5.parquet"
ALPHA5_GRID = BASE / "outputs" / "diagnostics" / "bus_fullweek_bic_grid.csv"
ALPHA5_BOOT = BASE / "outputs" / "diagnostics" / "bus_fullweek_bootstrap.csv"
K_RANGE = list(range(2, 13))
BOOTSTRAP_K = list(range(2, 9))
COVARIANCES = ["spherical", "diag", "tied", "full"]
DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
HOURS = list(range(1080, 1800, 60))
SEED = 42
N_INIT = 20
BOOTSTRAP_N_INIT = 3


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_alpha0(reference: pd.DataFrame) -> pd.DataFrame:
    long = pd.read_parquet(LONG_INPUT)
    long["lsoa"] = long["lsoa"].astype(str)
    long["hour_bin"] = long["hour_bin"].astype(int)
    keep = reference.index.astype(str).tolist()
    grouped = (
        long.groupby(["lsoa", "day_type", "direction", "hour_bin"], as_index=False, observed=True)["count"]
        .sum()
    )
    parts = []
    for direction in DIRECTIONS:
        day_parts = []
        for day_type in DAY_TYPES:
            sub = grouped[
                (grouped["day_type"] == day_type) & (grouped["direction"] == direction)
            ]
            wide = sub.pivot_table(
                index="lsoa", columns="hour_bin", values="count", aggfunc="sum", fill_value=0.0
            )
            wide = wide.reindex(index=keep, columns=HOURS, fill_value=0.0).astype(float)
            wide.columns = pd.MultiIndex.from_product([[day_type], HOURS])
            day_parts.append(wide)
        counts = pd.concat(day_parts, axis=1)
        total = counts.sum(axis=1)
        if (total <= 0).any():
            raise ValueError(f"Direction {direction} has a zero total in the fixed sample")
        share = counts.div(total, axis=0)
        share.columns = [
            f"{direction}_{day_type}_{int(hour)}" for day_type, hour in share.columns
        ]
        parts.append(share)
    X = pd.concat(parts, axis=1)
    X = X.reindex(index=reference.index, columns=reference.columns)
    if not np.isfinite(X.to_numpy()).all():
        raise ValueError("alpha=0 feature matrix has non-finite values")
    if not np.allclose(X.sum(axis=1).to_numpy(), 2.0, atol=1e-10):
        raise ValueError("alpha=0 row sums are not two")
    return X


def feature_audit(alpha0: pd.DataFrame, alpha5: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []
    for direction in DIRECTIONS:
        columns = [column for column in alpha0.columns if column.startswith(direction + "_")]
        tv = 0.5 * np.abs(alpha0[columns].to_numpy() - alpha5[columns].to_numpy()).sum(axis=1)
        for lsoa, value in zip(alpha0.index, tv):
            rows.append({"lsoa": lsoa, "direction": direction, "TV_alpha0_alpha5": float(value)})
    frame = pd.DataFrame(rows)
    rng = np.random.default_rng(SEED)
    sample = rng.choice(len(alpha0), size=min(500, len(alpha0)), replace=False)
    d0 = pdist(alpha0.to_numpy()[sample])
    d5 = pdist(alpha5.to_numpy()[sample])
    summary = {
        "n_lsoa": len(alpha0),
        "n_features": alpha0.shape[1],
        "alpha0_rank": int(np.linalg.matrix_rank(alpha0.to_numpy() - alpha0.to_numpy().mean(axis=0))),
        "alpha5_rank": int(np.linalg.matrix_rank(alpha5.to_numpy() - alpha5.to_numpy().mean(axis=0))),
        "median_tv": float(frame["TV_alpha0_alpha5"].median()),
        "p95_tv": float(frame["TV_alpha0_alpha5"].quantile(0.95)),
        "max_tv": float(frame["TV_alpha0_alpha5"].max()),
        "pairwise_distance_correlation_500_sample": float(np.corrcoef(d0, d5)[0, 1]),
        "pairwise_distance_median_abs_change": float(np.median(np.abs(d0 - d5))),
        "pairwise_distance_p95_abs_change": float(np.quantile(np.abs(d0 - d5), 0.95)),
    }
    return frame, summary


def bic_grid(values: np.ndarray) -> tuple[pd.DataFrame, str, int]:
    rows = []
    log("[2/5] alpha=0 covariance x K BIC grid")
    for covariance in COVARIANCES:
        for k in K_RANGE:
            model, warning_messages, seconds = base.fit_gmm(values, k, covariance, SEED, N_INIT)
            labels = model.predict(values)
            rows.append(
                {
                    "covariance": covariance,
                    "K": k,
                    "BIC": float(model.bic(values)),
                    "AIC": float(model.aic(values)),
                    "converged": bool(model.converged_),
                    "n_iter": int(model.n_iter_),
                    "fit_seconds": seconds,
                    "warnings": " | ".join(warning_messages),
                    **base.cluster_size_metrics(labels, k),
                }
            )
            log(
                f"      {covariance:9s} K={k:2d} BIC={rows[-1]['BIC']:.1f} "
                f"min_n={rows[-1]['min_cluster_n']:4d}"
            )
            pd.DataFrame(rows).to_csv(DIAGNOSTICS / "alpha0_bic_grid.partial.csv", index=False)
    grid = pd.DataFrame(rows)
    grid.to_csv(DIAGNOSTICS / "alpha0_bic_grid.csv", index=False)
    best = grid.loc[grid["BIC"].idxmin()]
    return grid, str(best["covariance"]), int(best["K"])


def full_diagnostics(
    alpha0: pd.DataFrame, alpha5: pd.DataFrame, bootstrap_n: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    values = alpha0.to_numpy(dtype=float)
    rng = np.random.default_rng(SEED)
    sample = rng.choice(len(values), size=min(2000, len(values)), replace=False)
    rows = []
    labels_by_k = {}
    compare_rows = []
    log("[3/5] Fixed full-covariance alpha=0 diagnostics and alpha=5 label comparison")
    for k in K_RANGE:
        model, warning_messages, seconds = base.fit_gmm(values, k, "full", SEED, N_INIT)
        labels = model.predict(values)
        labels_by_k[k] = labels
        alpha5_labels = pd.read_csv(
            BASE / "outputs" / "labels" / f"bus_fullweek_k{k}_labels.csv"
        ).set_index("unit")["cluster"]
        alpha5_labels.index = alpha5_labels.index.astype(str)
        alpha5_array = alpha5_labels.reindex(alpha0.index).to_numpy(dtype=int)
        matched = base.matched_jaccard(alpha5_array, labels, k)
        size = base.cluster_size_metrics(labels, k)
        rows.append(
            {
                "K": k,
                "BIC": float(model.bic(values)),
                "AIC": float(model.aic(values)),
                "silhouette": float(silhouette_score(values[sample], labels[sample])),
                "calinski_harabasz": float(calinski_harabasz_score(values, labels)),
                "davies_bouldin": float(davies_bouldin_score(values, labels)),
                "converged": bool(model.converged_),
                "fit_seconds": seconds,
                "warnings": " | ".join(warning_messages),
                **size,
            }
        )
        compare_rows.append(
            {
                "K": k,
                "alpha0_vs_alpha5_ARI": float(adjusted_rand_score(alpha5_array, labels)),
                "mean_matched_cluster_jaccard": float(matched.mean()),
                "min_matched_cluster_jaccard": float(matched.min()),
            }
        )
        pd.DataFrame({"unit": alpha0.index, "cluster": labels}).to_csv(
            LABELS / f"alpha0_full_k{k}_labels.csv", index=False
        )
        log(
            f"      K={k:2d} sil={rows[-1]['silhouette']:.3f} "
            f"alpha0/5 ARI={compare_rows[-1]['alpha0_vs_alpha5_ARI']:.3f}"
        )
    kdiag = pd.DataFrame(rows)
    comparison = pd.DataFrame(compare_rows)
    kdiag.to_csv(DIAGNOSTICS / "alpha0_full_kdiag_prebootstrap.csv", index=False)
    comparison.to_csv(DIAGNOSTICS / "alpha0_vs_alpha5_full_labels.csv", index=False)

    log(f"[4/5] alpha=0 full-covariance bootstrap K=2..8, n={bootstrap_n}")
    boot_rows = []
    recovery_rows = []
    for k in BOOTSTRAP_K:
        base_labels = labels_by_k[k]
        for replicate in range(bootstrap_n):
            idx = rng.choice(len(values), size=len(values), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model, warning_messages, seconds = base.fit_gmm(
                values[idx], k, "full", seed, BOOTSTRAP_N_INIT
            )
            predicted = model.predict(values)
            matched = base.matched_jaccard(base_labels, predicted, k)
            boot_rows.append(
                {
                    "K": k,
                    "replicate": replicate + 1,
                    "seed": seed,
                    "ARI": float(adjusted_rand_score(base_labels, predicted)),
                    "mean_matched_cluster_jaccard": float(matched.mean()),
                    "min_matched_cluster_jaccard": float(matched.min()),
                    "fit_seconds": seconds,
                    "converged": bool(model.converged_),
                    "warnings": " | ".join(warning_messages),
                }
            )
            for cluster, score in enumerate(matched):
                recovery_rows.append(
                    {
                        "K": k,
                        "replicate": replicate + 1,
                        "base_cluster": cluster,
                        "matched_jaccard": float(score),
                    }
                )
        current = pd.DataFrame(boot_rows)
        sub = current[current["K"] == k]
        log(
            f"      K={k}: ARI={sub['ARI'].mean():.3f}; "
            f"min-cluster Jaccard={sub['min_matched_cluster_jaccard'].mean():.3f}"
        )
    bootstrap = pd.DataFrame(boot_rows)
    recovery = pd.DataFrame(recovery_rows)
    bootstrap.to_csv(DIAGNOSTICS / "alpha0_full_bootstrap.csv", index=False)
    recovery.to_csv(DIAGNOSTICS / "alpha0_full_bootstrap_cluster_recovery.csv", index=False)
    boot_summary = (
        bootstrap.groupby("K", as_index=False)
        .agg(
            alpha0_bootstrap_ari_mean=("ARI", "mean"),
            alpha0_bootstrap_ari_sd=("ARI", "std"),
            alpha0_bootstrap_ari_p05=("ARI", lambda x: x.quantile(0.05)),
            alpha0_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
            alpha0_min_cluster_jaccard_p05=("min_matched_cluster_jaccard", lambda x: x.quantile(0.05)),
        )
    )
    alpha5_boot = pd.read_csv(ALPHA5_BOOT)
    alpha5_summary = (
        alpha5_boot.groupby("K", as_index=False)
        .agg(
            alpha5_bootstrap_ari_mean=("ARI", "mean"),
            alpha5_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
        )
    )
    boot_compare = boot_summary.merge(alpha5_summary, on="K", how="left")
    boot_compare.to_csv(DIAGNOSTICS / "alpha0_vs_alpha5_bootstrap_summary.csv", index=False)
    return kdiag, comparison, boot_compare, recovery


def write_report(
    feature_summary: dict,
    grid0: pd.DataFrame,
    best_cov0: str,
    best_k0: int,
    kdiag0: pd.DataFrame,
    label_compare: pd.DataFrame,
    boot_compare: pd.DataFrame,
    recovery: pd.DataFrame,
) -> None:
    grid5 = pd.read_csv(ALPHA5_GRID)
    best5 = grid5.loc[grid5["BIC"].idxmin()]
    best_by_cov0 = (
        grid0.sort_values("BIC").groupby("covariance", as_index=False).first()[
            ["covariance", "K", "BIC", "min_cluster_n", "min_cluster_share"]
        ]
    )
    k3_recovery = (
        recovery[recovery["K"] == 3]
        .groupby("base_cluster", as_index=False)["matched_jaccard"]
        .agg(["mean", "std", "min", "median", "max"])
        .reset_index()
    )
    report = f"""# Fixed-sample alpha=0 versus alpha=5 sensitivity

## Direct verdict

Both variants use the same {feature_summary['n_lsoa']} hub-first LSOAs, the same
72 full-week features, and the same GMM settings. The only change is empirical
shrinkage alpha.

- alpha=0 global BIC minimum: covariance={best_cov0}, K={best_k0}
- alpha=5 global BIC minimum: covariance={best5['covariance']}, K={int(best5['K'])}
- alpha=0 versus alpha=5 full-covariance K=3 label ARI:
  {label_compare.loc[label_compare['K'] == 3, 'alpha0_vs_alpha5_ARI'].iloc[0]:.3f}
- K=3 weakest matched cross-alpha cluster Jaccard:
  {label_compare.loc[label_compare['K'] == 3, 'min_matched_cluster_jaccard'].iloc[0]:.3f}

## Feature perturbation

{pd.DataFrame([feature_summary]).to_markdown(index=False)}

## alpha=0 BIC minima by covariance

{best_by_cov0.to_markdown(index=False)}

## Full-covariance K diagnostics at alpha=0

{kdiag0[['K','BIC','silhouette','davies_bouldin','min_cluster_n','min_cluster_share']].to_markdown(index=False)}

## Same-K alpha=0 versus alpha=5 labels

{label_compare.to_markdown(index=False)}

## Bootstrap comparison

{boot_compare.to_markdown(index=False)}

## alpha=0 full K=3 recovery by cluster

{k3_recovery.to_markdown(index=False)}

## Decision boundary

If K=3 and its third cluster remain similar across alpha=0 and alpha=5, the
third cluster is not created by shrinkage; its moderate bootstrap recovery must
instead be reported as an inherent boundary uncertainty. If the cross-alpha
agreement is low, K=3 cannot yet be frozen.
"""
    (REPORT / "ALPHA_SENSITIVITY_RESULTS.md").write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", type=int, default=20)
    args = parser.parse_args()
    if args.bootstrap < 1:
        raise ValueError("bootstrap must be positive")
    started = time.time()

    alpha5 = pd.read_parquet(ALPHA5_X)
    alpha5.index = alpha5.index.astype(str)
    manifest = pd.DataFrame(
        [
            {"role": "hub_first_long", "path": str(LONG_INPUT.resolve()), "sha256": sha256(LONG_INPUT)},
            {"role": "alpha5_fixed_sample", "path": str(ALPHA5_X.resolve()), "sha256": sha256(ALPHA5_X)},
            {"role": "alpha5_bic_grid", "path": str(ALPHA5_GRID.resolve()), "sha256": sha256(ALPHA5_GRID)},
            {"role": "alpha5_bootstrap", "path": str(ALPHA5_BOOT.resolve()), "sha256": sha256(ALPHA5_BOOT)},
        ]
    )
    manifest.to_csv(OUT / "input_manifest.csv", index=False)

    log("[1/5] Building alpha=0 features on the fixed alpha=5 sample")
    alpha0 = build_alpha0(alpha5)
    alpha0.to_parquet(FEATURES / "X_bus_fullweek_alpha0_fixed_sample.parquet")
    tv, feature_summary = feature_audit(alpha0, alpha5)
    tv.to_csv(DIAGNOSTICS / "alpha0_vs_alpha5_row_direction_tv.csv", index=False)
    (DIAGNOSTICS / "feature_perturbation_summary.json").write_text(
        json.dumps(feature_summary, indent=2), encoding="utf-8"
    )
    log(json.dumps(feature_summary))

    grid0, best_cov0, best_k0 = bic_grid(alpha0.to_numpy(dtype=float))
    kdiag0, label_compare, boot_compare, recovery = full_diagnostics(
        alpha0, alpha5, args.bootstrap
    )
    write_report(
        feature_summary,
        grid0,
        best_cov0,
        best_k0,
        kdiag0,
        label_compare,
        boot_compare,
        recovery,
    )
    environment = {
        "command": "python -u src\\run_alpha_sensitivity.py --bootstrap 20",
        "seed": SEED,
        "n_init": N_INIT,
        "bootstrap_n_init": BOOTSTRAP_N_INIT,
        "elapsed_seconds": time.time() - started,
    }
    (OUT / "run_environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    log(f"[5/5] Complete: {REPORT / 'ALPHA_SENSITIVITY_RESULTS.md'}")


if __name__ == "__main__":
    main()
