from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture

"""03b - Full {spherical, diag, tied, full} covariance-family BIC grid.

`03_cluster_allmodes.py` restricts its main BIC grid to {diag, full} for
speed (diag is what canonical rail actually uses; full is kept only as a
cross-check). This script runs canonical's complete four-family grid on
the SAME all-modes feature matrix, to independently verify that diag is
still the right covariance family once every family is considered -- not
just assumed by scope-narrowing.

Must be rerun whenever `X_rail_allmodes.parquet` changes upstream (e.g.
after `01b_merge_colocated_stations.py` changes which stations are
included) -- it reads that file directly, so it is always checking
whatever station set the rest of the pipeline currently uses.
"""

DATA_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
FIG_DIR = Path(__file__).resolve().parents[1] / "outputs" / "figures"
X_PATH = DATA_DIR / "X_rail_allmodes.parquet"
OUT_CSV = DATA_DIR / "rail_allmodes_bic_grid_full4family.csv"
OUT_FIG = FIG_DIR / "rail_allmodes_bic_grid_full4family.png"

K_RANGE = list(range(2, 13))
COVARIANCES = ["spherical", "diag", "tied", "full"]
# Left at 20: this script is a covariance-FAMILY screen (does diag beat full?),
# not a source of reported labels. `full` is degenerate at n=403 with 440
# dimensions and collapses to K=2 regardless of restarts, so raising n_init here
# would cost ~20 minutes to confirm the same conclusion.
N_INIT = 20
REG_COVAR = 1e-6
MAX_ITER = 300
RANDOM_STATE = 42


def fit(X, k, cov):
    return GaussianMixture(
        k, covariance_type=cov, n_init=N_INIT, reg_covar=REG_COVAR,
        max_iter=MAX_ITER, random_state=RANDOM_STATE,
    ).fit(X)


def main() -> None:
    X = pd.read_parquet(X_PATH)
    Xv = X.values.astype(float)
    print(f"X shape: {Xv.shape}", flush=True)

    rows = []
    for cov in COVARIANCES:
        for k in K_RANGE:
            try:
                bic = fit(Xv, k, cov).bic(Xv)
            except Exception as exc:
                print(f"  [warn] cov={cov} K={k} failed: {exc}")
                bic = np.nan
            rows.append({"covariance": cov, "K": k, "BIC": bic})
            print(f"  cov={cov} K={k} BIC={bic:.1f}" if bic == bic else f"  cov={cov} K={k} BIC=NaN", flush=True)

    grid = pd.DataFrame(rows)
    grid.to_csv(OUT_CSV, index=False)

    pivot = grid.pivot(index="K", columns="covariance", values="BIC")
    print(pivot.to_string())
    best = grid.loc[grid["BIC"].idxmin()]
    print(f"\nOverall BIC-best: covariance={best['covariance']}, K={int(best['K'])}, BIC={best['BIC']:.1f}")
    for cov in COVARIANCES:
        sub = grid[grid.covariance == cov].dropna()
        if not sub.empty:
            r = sub.loc[sub.BIC.idxmin()]
            print(f"  {cov}: best K={int(r.K)} (BIC {r.BIC:.1f})")

    fig, ax = plt.subplots(figsize=(7.5, 5))
    for cov, mk in zip(COVARIANCES, ["o", "s", "^", "D"]):
        sub = grid[grid.covariance == cov]
        ax.plot(sub.K, sub.BIC, "-" + mk, label=cov)
    ax.set_xlabel("K")
    ax.set_ylabel("BIC (lower=better)")
    ax.set_title(f"rail all-modes ({X.shape[0]} stations) — full covariance-family BIC grid")
    ax.legend(fontsize=9)
    ax.grid(color="#eee")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("\nSaved:", OUT_CSV)
    print("Saved:", OUT_FIG)


if __name__ == "__main__":
    main()
