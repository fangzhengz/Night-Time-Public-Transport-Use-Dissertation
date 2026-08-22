# -*- coding: utf-8 -*-
"""Seed-stability and night-cluster-survival battery for the bus CLR clustering.

Answers one question the adopted bus result cannot currently answer in writing:
StopArea CLR K=4 was selected on BIC alone, and BIC in CLR feature space has
already been shown to be seed-unstable on this project's bus data
(``rq1_bus_daytype_normalisation``, 2026-08-01). The rail side resolved the
equivalent question with a seed battery plus a night-cluster survival check
(``numbat_all_area_test``); this script runs the same two diagnostics on bus so
both modes can be defended with one argument instead of two.

Reads ``rq1_bus_stoparea_clustering``'s CLR feature matrix and its adopted
labels. Writes only into this folder -- never modifies its sources.

Grid A reproduces the adopted run's budget (n_init=20) so the BIC numbers are
comparable to ``outputs/clr/diagnostics/kdiag.csv``. Grid B raises the budget to
test the restart-bias effect documented for rail on 2026-08-02: a fixed n_init
across K under-optimises high-K models and biases BIC toward low K.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

SRC_CLUSTERING = FYP / "rq1_bus_stoparea_clustering"
FEATURES = SRC_CLUSTERING / "outputs" / "features" / "X_bus_stoparea_clr_min36.parquet"
METRICS = SRC_CLUSTERING / "outputs" / "features" / "sample_metrics.csv"
ADOPTED_K4_LABELS = SRC_CLUSTERING / "outputs" / "clr" / "labels" / "k4_labels.csv"
CLUSTER_NAMES = SRC_CLUSTERING / "outputs" / "data" / "bus_cluster_names.csv"

OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

K_RANGE = [2, 3, 4, 5, 6, 7]
SEEDS_A = [42, 7, 123, 2026, 999]
SEEDS_B = [42, 7, 123]
N_INIT_A = 20          # the adopted run's budget
N_INIT_B = 100         # restart-bias probe
COVARIANCE = "full"    # the adopted run's reporting family
REG_COVAR = 1e-6
MAX_ITER = 300

# The night-persistent cluster in the adopted K=4 solution, as named by
# rq1_bus_stoparea_clustering/src/06_cluster_names.py. Read from that file
# rather than hardcoded -- cluster ids are not stable across refits.
NIGHT_ROLE = "night_persistent"


def log(message: str) -> None:
    print(message, flush=True)


def fit(X: np.ndarray, k: int, seed: int, n_init: int) -> GaussianMixture:
    return GaussianMixture(
        n_components=k,
        covariance_type=COVARIANCE,
        n_init=n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=seed,
    ).fit(X)


def jaccard(left: np.ndarray, right: np.ndarray) -> float:
    intersection = int(np.logical_and(left, right).sum())
    union = int(np.logical_or(left, right).sum())
    return float(intersection / union) if union else float("nan")


def best_matching_jaccard(labels: np.ndarray, reference: np.ndarray, k: int) -> tuple[float, int]:
    scores = [(jaccard(labels == cluster, reference), cluster) for cluster in range(k)]
    return max(scores)


def run_grid(
    X: np.ndarray, seeds: list[int], n_init: int, tag: str
) -> tuple[pd.DataFrame, dict[tuple[int, int], np.ndarray]]:
    rows: list[dict] = []
    labels_by: dict[tuple[int, int], np.ndarray] = {}
    for seed in seeds:
        for k in K_RANGE:
            started = time.perf_counter()
            model = fit(X, k, seed, n_init)
            seconds = time.perf_counter() - started
            labels = model.predict(X).astype(int)
            labels_by[(k, seed)] = labels
            sizes = np.bincount(labels, minlength=k)
            rows.append(
                {
                    "grid": tag,
                    "n_init": n_init,
                    "seed": seed,
                    "K": k,
                    "BIC": float(model.bic(X)),
                    "converged": bool(model.converged_),
                    "min_cluster_n": int(sizes.min()),
                    "fit_seconds": seconds,
                }
            )
            log(
                f"  [{tag}] seed={seed:<5d} K={k} BIC={rows[-1]['BIC']:15.1f} "
                f"min_n={int(sizes.min()):5d} ({seconds:.1f}s)"
            )
    return pd.DataFrame(rows), labels_by


def seed_agreement(labels_by: dict[tuple[int, int], np.ndarray], seeds: list[int]) -> pd.DataFrame:
    rows: list[dict] = []
    for k in K_RANGE:
        pairwise = [
            adjusted_rand_score(labels_by[(k, a)], labels_by[(k, b)])
            for a, b in itertools.combinations(seeds, 2)
        ]
        rows.append(
            {
                "K": k,
                "seed_ari_mean": float(np.mean(pairwise)),
                "seed_ari_min": float(np.min(pairwise)),
                "seed_ari_max": float(np.max(pairwise)),
                "n_pairs": len(pairwise),
            }
        )
    return pd.DataFrame(rows)


def bic_spread(grid: pd.DataFrame) -> pd.DataFrame:
    spread = grid.groupby("K", as_index=False).agg(
        bic_mean=("BIC", "mean"),
        bic_min=("BIC", "min"),
        bic_max=("BIC", "max"),
    )
    spread["bic_range"] = spread["bic_max"] - spread["bic_min"]
    winner = grid.loc[grid.groupby("seed")["BIC"].idxmin(), ["seed", "K"]]
    counts = winner["K"].value_counts().rename("seeds_won").reset_index()
    counts.columns = ["K", "seeds_won"]
    spread = spread.merge(counts, on="K", how="left").fillna({"seeds_won": 0})
    spread["seeds_won"] = spread["seeds_won"].astype(int)
    return spread


def k4_margin(grid: pd.DataFrame) -> pd.DataFrame:
    """Per seed, how far K=4's BIC beats the better of its neighbours K=3/K=5.

    Positive means K=4 is preferred (BIC is minimised here). This is the exact
    quantity the adoption decision rested on; the question is its spread, not
    its point value.
    """
    rows: list[dict] = []
    for seed, sub in grid.groupby("seed"):
        by_k = sub.set_index("K")["BIC"]
        rival = min(by_k[3], by_k[5])
        rows.append(
            {
                "seed": int(seed),
                "bic_k3": float(by_k[3]),
                "bic_k4": float(by_k[4]),
                "bic_k5": float(by_k[5]),
                "k4_advantage_over_best_rival": float(rival - by_k[4]),
                "k4_is_grid_optimum": bool(by_k.idxmin() == 4),
            }
        )
    return pd.DataFrame(rows)


def survival(
    X_index: pd.Index,
    labels_by: dict[tuple[int, int], np.ndarray],
    seeds: list[int],
    metrics: pd.DataFrame,
    adopted_night: np.ndarray,
) -> pd.DataFrame:
    """Does the night-persistent group survive as a cluster at each K?

    Two reference sets, because each answers a different objection:

    ``adopted``  the night-persistent cluster of the adopted K=4 solution.
                 Answers "if we moved to K=3, would this specific group still
                 exist?" -- but it is defined by a clustering, so a high score
                 at K=4 is partly tautological.
    ``metric``   a size-matched set built only from post_midnight_persistence,
                 with no clustering involved. Answers the same question without
                 that circularity, and is the defensible one to report.
    """
    persistence = metrics.loc[X_index, "post_midnight_persistence"]
    size = int(adopted_night.sum())
    metric_reference = np.zeros(len(X_index), dtype=bool)
    metric_reference[np.argsort(-persistence.to_numpy())[:size]] = True

    rows: list[dict] = []
    for k in K_RANGE:
        for seed in seeds:
            labels = labels_by[(k, seed)]
            adopted_score, adopted_cluster = best_matching_jaccard(labels, adopted_night, k)
            metric_score, metric_cluster = best_matching_jaccard(labels, metric_reference, k)
            rows.append(
                {
                    "K": k,
                    "seed": seed,
                    "adopted_night_jaccard": adopted_score,
                    "adopted_night_host_cluster": adopted_cluster,
                    "adopted_night_host_n": int((labels == adopted_cluster).sum()),
                    "metric_night_jaccard": metric_score,
                    "metric_night_host_cluster": metric_cluster,
                    "metric_night_host_n": int((labels == metric_cluster).sum()),
                }
            )
    frame = pd.DataFrame(rows)
    frame.attrs["reference_size"] = size
    return frame


def main() -> None:
    started = time.time()
    for path in [FEATURES, METRICS, ADOPTED_K4_LABELS, CLUSTER_NAMES]:
        if not path.exists():
            raise FileNotFoundError(path)

    X_frame = pd.read_parquet(FEATURES)
    X_frame.index = pd.Index(X_frame.index.astype(str), name="lsoa")
    X = X_frame.to_numpy(dtype=float)
    if X.shape[1] != 72:
        raise RuntimeError(f"Unexpected feature width {X.shape}")
    log(f"CLR feature matrix: n={X.shape[0]:,}, d={X.shape[1]}, covariance={COVARIANCE}")

    metrics = pd.read_csv(METRICS, dtype={"lsoa": str}).set_index("lsoa")

    names = pd.read_csv(CLUSTER_NAMES)
    night_row = names.loc[names["role"] == NIGHT_ROLE]
    if len(night_row) != 1:
        raise RuntimeError(f"Expected exactly one '{NIGHT_ROLE}' cluster, got {len(night_row)}")
    night_cluster_id = int(night_row.iloc[0]["cluster"])
    log(
        f"Adopted K=4 night-persistent cluster: C{night_cluster_id} "
        f"({night_row.iloc[0]['name_en']}), n={int(night_row.iloc[0]['n']):,}"
    )

    adopted = pd.read_csv(ADOPTED_K4_LABELS, dtype={"lsoa": str}).set_index("lsoa")
    adopted = adopted.loc[X_frame.index, "cluster"].to_numpy(dtype=int)
    adopted_night = adopted == night_cluster_id

    log(f"\nGrid A: n_init={N_INIT_A} (adopted budget), seeds={SEEDS_A}")
    grid_a, labels_a = run_grid(X, SEEDS_A, N_INIT_A, "A")
    log(f"\nGrid B: n_init={N_INIT_B} (restart-bias probe), seeds={SEEDS_B}")
    grid_b, labels_b = run_grid(X, SEEDS_B, N_INIT_B, "B")

    grids = pd.concat([grid_a, grid_b], ignore_index=True)
    grids.to_csv(OUT / "bic_by_seed.csv", index=False)

    agree_a = seed_agreement(labels_a, SEEDS_A).assign(grid="A", n_init=N_INIT_A)
    agree_b = seed_agreement(labels_b, SEEDS_B).assign(grid="B", n_init=N_INIT_B)
    agreement = pd.concat([agree_a, agree_b], ignore_index=True)
    agreement.to_csv(OUT / "seed_agreement.csv", index=False)

    spread_a = bic_spread(grid_a).assign(grid="A", n_init=N_INIT_A)
    spread_b = bic_spread(grid_b).assign(grid="B", n_init=N_INIT_B)
    spread = pd.concat([spread_a, spread_b], ignore_index=True)
    spread.to_csv(OUT / "bic_spread.csv", index=False)

    margin_a = k4_margin(grid_a).assign(grid="A", n_init=N_INIT_A)
    margin_b = k4_margin(grid_b).assign(grid="B", n_init=N_INIT_B)
    margin = pd.concat([margin_a, margin_b], ignore_index=True)
    margin.to_csv(OUT / "k4_bic_margin.csv", index=False)

    surv = survival(X_frame.index, labels_a, SEEDS_A, metrics, adopted_night)
    surv.to_csv(OUT / "night_cluster_survival.csv", index=False)
    surv_summary = surv.groupby("K", as_index=False).agg(
        adopted_night_jaccard_mean=("adopted_night_jaccard", "mean"),
        adopted_night_jaccard_min=("adopted_night_jaccard", "min"),
        metric_night_jaccard_mean=("metric_night_jaccard", "mean"),
        metric_night_jaccard_min=("metric_night_jaccard", "min"),
    )
    surv_summary.to_csv(OUT / "night_cluster_survival_summary.csv", index=False)

    elapsed = time.time() - started
    (OUT / "run_metadata.json").write_text(
        json.dumps(
            {
                "elapsed_seconds": elapsed,
                "n_lsoas": int(X.shape[0]),
                "n_features": int(X.shape[1]),
                "covariance": COVARIANCE,
                "k_range": K_RANGE,
                "grid_a": {"n_init": N_INIT_A, "seeds": SEEDS_A},
                "grid_b": {"n_init": N_INIT_B, "seeds": SEEDS_B},
                "adopted_night_cluster_id": night_cluster_id,
                "night_reference_size": int(adopted_night.sum()),
                "python": sys.version,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    log("\n" + "=" * 72)
    log("BIC spread across seeds")
    log(spread.to_string(index=False))
    log("\nSeed agreement (mean pairwise ARI)")
    log(agreement.to_string(index=False))
    log("\nK=4 BIC advantage over the better of K=3/K=5, per seed")
    log(margin.to_string(index=False))
    log("\nNight-cluster survival by K (Jaccard vs best-matching cluster)")
    log(surv_summary.to_string(index=False))
    log(f"\nComplete in {elapsed:.1f}s -> {OUT}")


if __name__ == "__main__":
    main()
