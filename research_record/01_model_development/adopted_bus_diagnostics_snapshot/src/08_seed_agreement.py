# -*- coding: utf-8 -*-
"""Random-seed agreement diagnostic for the reported CLR solution.

Fills in the "Random-seed agreement -- mean pairwise ARI" panel that exists
in the rail K-selection figure but is blank in the bus one, because kdiag.csv
never stored per-seed labels: 02_run_clustering.py's final-seed refit
(config.FINAL_SEEDS) keeps only the best-BIC seed's labels for each candidate
K, discarding the other four. This script independently refits every K in
BOOTSTRAP_KS at the same FINAL_SEEDS / N_INIT_FINAL / covariance budget
already used for the official refit, keeps each seed's own labels, and
reports the mean PAIRWISE ARI among them -- the same statistic and method as
numbat_all_area_test/08_k_selection_panel.py's seed_ari_mean (mean of
combinations(seeds, 2), not agreement with any single privileged partition).

Read-only with respect to cluster assignments: merges one new column
(`seed_ari_mean`) into kdiag.csv by K; does not touch the `cluster` column in
any labels file.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

VARIANT = "clr"
COVARIANCE = "full"  # matches this run's reporting_covariance (run_environment.json)


def log(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    output = C.OUT / VARIANT
    X_frame = pd.read_parquet(C.FEATURES / f"X_bus_stoparea_{VARIANT}_min33.parquet")
    X_frame.index = pd.Index(X_frame.index.astype(str), name="lsoa")
    X = X_frame.to_numpy(dtype=float)

    rows: list[dict] = []
    for k in C.BOOTSTRAP_KS:
        labels_by_seed = []
        for seed in C.FINAL_SEEDS:
            model = GaussianMixture(
                n_components=k,
                covariance_type=COVARIANCE,
                n_init=C.N_INIT_FINAL,
                reg_covar=C.REG_COVAR,
                max_iter=C.MAX_ITER,
                random_state=seed,
            ).fit(X)
            labels_by_seed.append(model.predict(X))
        pairwise = [adjusted_rand_score(a, b) for a, b in combinations(labels_by_seed, 2)]
        seed_ari_mean = float(np.mean(pairwise))
        rows.append({"K": k, "seed_ari_mean": seed_ari_mean})
        log(
            f"K={k}: seed_ari_mean={seed_ari_mean:.4f} "
            f"(5 seeds x n_init={C.N_INIT_FINAL}, {COVARIANCE})"
        )

    result = pd.DataFrame(rows)
    seed_agreement_path = output / "diagnostics" / "seed_agreement.csv"
    result.to_csv(seed_agreement_path, index=False)
    log(f"Wrote {seed_agreement_path}")

    kdiag_path = output / "diagnostics" / "kdiag.csv"
    kdiag = pd.read_csv(kdiag_path)
    kdiag = kdiag.drop(columns=[c for c in ["seed_ari_mean"] if c in kdiag.columns])
    kdiag = kdiag.merge(result, on="K", how="left")
    kdiag.to_csv(kdiag_path, index=False)
    log(f"Merged seed_ari_mean into {kdiag_path}")


if __name__ == "__main__":
    main()
