# -*- coding: utf-8 -*-
"""Fit and diagnose one cell of the rail closure x window 2x2.

Grid, covariance families, seed, n_init and bootstrap protocol are copied from
`numbat_all_area_test/src/03_cluster_allmodes.py`. Two additions:

  zero_bin_eta2  the bus sidecar's zero-structure diagnostic. Rail is 10.5%
                 zero cells unpadded and 26.1% padded, so this is NOT inert
                 here and is the main thing to watch when padding.
  seed stability 20 full-data refits at n_init=20, each scored by ARI against
                 the reference partition -- the adopted run's own protocol.
                 This is what decided K=5 over K=7 there (0.894 vs 0.703); a
                 closure change that destabilises K has to be caught here, not
                 after the labels are wired downstream.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import warnings

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    adjusted_rand_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

warnings.filterwarnings("ignore", category=ConvergenceWarning)


def log(message: str) -> None:
    print(message, flush=True)


def fit_gmm(X, k, covariance, seed, n_init):
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
    return float(
        sum(
            int((labels == cluster).sum())
            * (float(y[labels == cluster].mean()) - grand) ** 2
            for cluster in np.unique(labels)
        )
        / total
    )


def matched_jaccard(base, other, k) -> np.ndarray:
    contingency = np.zeros((k, k), dtype=int)
    for left, right in zip(base, other):
        contingency[int(left), int(right)] += 1
    union = (
        contingency.sum(axis=1, keepdims=True)
        + contingency.sum(axis=0, keepdims=True)
        - contingency
    )
    scores = np.divide(
        contingency, union, out=np.zeros_like(contingency, dtype=float), where=union > 0
    )
    rows, columns = linear_sum_assignment(-scores)
    matched = np.zeros(k, dtype=float)
    matched[rows] = scores[rows, columns]
    return matched


def run_variant(variant: str, n_init: int = None) -> None:
    # n_init is an argument because the padded matrix does NOT converge at
    # the pipeline default of 20 -- it lands on a local optimum whose BIC is
    # 709.7 worse than the one reached from n_init>=50. Any variant whose
    # numbers are quoted must be fitted above its own convergence point.
    n_init = C.N_INIT if n_init is None else n_init
    started = time.time()
    spec = C.VARIANTS[variant]
    root = C.OUT / variant
    for sub in ["diagnostics", "labels", "report"]:
        (root / sub).mkdir(parents=True, exist_ok=True)

    X_frame = pd.read_parquet(C.FEATURES / f"X_{variant}.parquet")
    X_frame.index = pd.Index(X_frame.index.astype(str), name="NLC")
    X = X_frame.to_numpy(dtype=float)

    metrics = pd.read_csv(C.RAIL_UNIT_METRICS, dtype={"NLC": str}).set_index("NLC")
    metrics = metrics.reindex(X_frame.index)
    zeros = pd.read_csv(
        C.FEATURES / "zero_bin_share.csv", dtype={"NLC": str}
    ).set_index("NLC")["zero_bin_share"]
    metrics["zero_bin_share"] = zeros.reindex(X_frame.index)

    canon = pd.read_csv(C.CANON_K5_LABELS, dtype={"unit": str}).set_index("unit")["cluster"]

    log(f"[{variant}] n={X.shape[0]}, d={X.shape[1]}, covariances={C.COVARIANCES}")
    grid_rows, grid_labels = [], {}
    for covariance in C.COVARIANCES:
        for k in C.K_RANGE:
            try:
                model = fit_gmm(X, k, covariance, C.SEED, n_init)
                labels = model.predict(X).astype(int)
                sizes = np.bincount(labels, minlength=k)
                grid_labels[(covariance, k)] = labels
                grid_rows.append(
                    {
                        "covariance": covariance, "K": k,
                        "BIC": float(model.bic(X)), "AIC": float(model.aic(X)),
                        "converged": bool(model.converged_),
                        "min_cluster_n": int(sizes.min()),
                        "n_parameters": int(model._n_parameters()),
                    }
                )
                log(f"  {covariance:9s} K={k:2d} BIC={grid_rows[-1]['BIC']:12.1f} "
                    f"p={grid_rows[-1]['n_parameters']:6d} min_n={int(sizes.min()):3d}")
            except Exception as error:  # noqa: BLE001 - canonical does the same
                grid_rows.append(
                    {"covariance": covariance, "K": k, "BIC": np.nan, "AIC": np.nan,
                     "converged": False, "min_cluster_n": -1, "n_parameters": -1}
                )
                log(f"  {covariance:9s} K={k:2d} FAILED: {type(error).__name__}")
    grid = pd.DataFrame(grid_rows)
    grid.to_csv(root / "diagnostics" / "bic_grid.csv", index=False)

    usable = grid.dropna(subset=["BIC"])
    global_best = usable.loc[usable["BIC"].idxmin()]
    primary = usable[usable["covariance"] == C.PRIMARY_COVARIANCE]
    primary_best_k = int(primary.loc[primary["BIC"].idxmin(), "K"])
    log(f"[{variant}] global BIC best: {global_best['covariance']} K={int(global_best['K'])}; "
        f"primary({C.PRIMARY_COVARIANCE}) best K={primary_best_k}")

    kdiag_rows = []
    for k in C.K_RANGE:
        if (C.PRIMARY_COVARIANCE, k) not in grid_labels:
            continue
        labels = grid_labels[(C.PRIMARY_COVARIANCE, k)]
        sizes = np.bincount(labels, minlength=k)
        row = {
            "K": k,
            "BIC": float(primary.loc[primary["K"] == k, "BIC"].iloc[0]),
            "silhouette": float(silhouette_score(X, labels)),
            "davies_bouldin": float(davies_bouldin_score(X, labels)),
            "activity_eta2": eta_squared(metrics["log_total_activity"], labels),
            "zero_bin_eta2": eta_squared(metrics["zero_bin_share"], labels),
            "min_cluster_n": int(sizes.min()),
        }
        for metric in C.EXTERNAL_METRICS:
            values = metrics[metric]
            mask = values.notna()
            row[f"{metric}_eta2"] = eta_squared(values[mask], labels[mask.to_numpy()])
        row["timing_mean_eta2"] = float(
            np.mean([row[f"{m}_eta2"] for m in C.TIMING_METRICS])
        )
        shared = X_frame.index.intersection(canon.index)
        row["ari_vs_canon_k5"] = float(
            adjusted_rand_score(
                canon.loc[shared], pd.Series(labels, index=X_frame.index).loc[shared]
            )
        )
        kdiag_rows.append(row)
        pd.DataFrame(
            {"unit": X_frame.index, "cluster": labels}
        ).to_csv(root / "labels" / f"k{k}_labels.csv", index=False)
    kdiag = pd.DataFrame(kdiag_rows)

    log(f"[{variant}] bootstrap + seed stability on K={C.CANDIDATE_KS}")
    rng = np.random.default_rng(C.SEED)
    stability_rows = []
    for k in C.CANDIDATE_KS:
        if (C.PRIMARY_COVARIANCE, k) not in grid_labels:
            continue
        base = grid_labels[(C.PRIMARY_COVARIANCE, k)]
        aris, jaccards = [], []
        for _ in range(C.N_BOOTSTRAP):
            sample = rng.choice(len(X), size=len(X), replace=True)
            model = fit_gmm(
                X[sample], k, C.PRIMARY_COVARIANCE,
                int(rng.integers(1, 2**31 - 1)), C.BOOTSTRAP_N_INIT,
            )
            other = model.predict(X)
            aris.append(adjusted_rand_score(base, other))
            jaccards.append(float(matched_jaccard(base, other, k).min()))

        # Canonical protocol: each seed run is a full n_init=20 refit scored
        # against the reference partition, not against the other seed runs.
        seed_aris = []
        for run in range(1, C.SEED_RUNS + 1):
            model = fit_gmm(
                X, k, C.PRIMARY_COVARIANCE, C.SEED + 10_000 + run, max(C.SEED_N_INIT, n_init)
            )
            seed_aris.append(adjusted_rand_score(base, model.predict(X)))

        stability_rows.append(
            {
                "K": k,
                "bootstrap_ari_mean": float(np.mean(aris)),
                "bootstrap_ari_sd": float(np.std(aris, ddof=1)),
                "bootstrap_min_jaccard_mean": float(np.mean(jaccards)),
                "seed_ari_mean": float(np.mean(seed_aris)),
                "seed_ari_min": float(np.min(seed_aris)),
            }
        )
        log(f"  K={k}: boot ARI={np.mean(aris):.3f} minJac={np.mean(jaccards):.3f} "
            f"| seed ARI={np.mean(seed_aris):.3f} (min {np.min(seed_aris):.3f})")
    stability = pd.DataFrame(stability_rows)
    stability.to_csv(root / "diagnostics" / "stability.csv", index=False)
    kdiag = kdiag.merge(stability, on="K", how="left")
    kdiag.to_csv(root / "diagnostics" / "kdiag.csv", index=False)

    elapsed = time.time() - started
    (root / "run_environment.json").write_text(
        json.dumps(
            {
                "variant": variant, "closure": spec["closure"], "padded": spec["padded"],
                "n_stations": int(X.shape[0]), "n_features": int(X.shape[1]),
                "global_bic_covariance": str(global_best["covariance"]),
                "global_bic_k": int(global_best["K"]),
                "primary_covariance": C.PRIMARY_COVARIANCE,
                "primary_bic_k": primary_best_k,
                "seed": C.SEED, "n_init": n_init,
                "n_bootstrap": C.N_BOOTSTRAP, "seed_runs": C.SEED_RUNS, "seed_n_init": C.SEED_N_INIT,
                "elapsed_seconds": elapsed,
                "python": sys.version, "platform": platform.platform(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "report" / "RESULTS.md").write_text(
        "\n".join(
            [
                f"# Rail sidecar: {variant}",
                "",
                f"- Closure: {spec['closure']}; window: "
                + ("padded 18:00-05:00 for all day types" if spec["padded"]
                   else "native (MON/TWT/SUN to 01:00, FRI/SAT to 05:00)"),
                f"- n={X.shape[0]} stations, d={X.shape[1]} features.",
                f"- Global BIC best: {global_best['covariance']}, K={int(global_best['K'])}.",
                f"- Primary ({C.PRIMARY_COVARIANCE}) BIC best: K={primary_best_k}.",
                "",
                "## K diagnostics",
                "",
                kdiag.to_markdown(index=False, floatfmt=".4f"),
                "",
                "Sidecar result, not adopted.",
            ]
        ),
        encoding="utf-8",
    )
    log(f"[{variant}] complete in {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=sorted(C.VARIANTS), required=True)
    parser.add_argument("--n-init", type=int, default=None)
    args = parser.parse_args()
    run_variant(args.variant, args.n_init)


if __name__ == "__main__":
    main()
