# -*- coding: utf-8 -*-
"""07 · Evening down-weighting SENSITIVITY — RIGOROUS version (additive, isolated).

Clara's suggestion: instead of dropping 18:00-20:00, DOWN-WEIGHT it. Earlier we
tested this at a FIXED K/covariance, which only answers "does the weight perturb
the chosen K=4 solution?". This version answers the fuller question: at each
weight, RE-RUN the complete model selection (BIC over covariance x K) so each
weight finds its OWN best (covariance, K); then judge whether down-weighting lets
the night/overnight signal surface better at any K.

For each (dataset, weight w in {1.0, 0.5, 0.3, 0.0}):
  - scale the 18:00-20:00 feature columns by w;
  - BIC grid over covariance x K -> per-weight BIC-best (cov, K);
  - full K-sweep at that covariance: silhouette, CH, DB, and overnight metrics
    computed on the TRUE (unweighted) post-midnight share so they are comparable
    across weights; light bootstrap ARI at the BIC-best K.

Key comparison: overnight-separation vs K, one line per weight. If down-weighting
helps, a w<1 line should rise above the w=1 line at some K.

ISOLATION: reads outputs/features/*.parquet read-only; writes ONLY to
outputs/sensitivity_downweight/. The main pipeline (01-06) is untouched.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score, adjusted_rand_score)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

SENS = C.OUT / "sensitivity_downweight"
SENS.mkdir(parents=True, exist_ok=True)

WEIGHTS = [1.0, 0.5, 0.3, 0.0]
EVENING = (18 * 60, 20 * 60)   # [1080, 1200) down-weighted
POSTMID = 24 * 60              # >=1440 = overnight signal (measured on TRUE shares)
DATASETS = (["rail_weekday", "rail_weekend"] + ["bus_weekday", "bus_weekend"])
WCOLORS = {1.0: "#500778", 0.5: "#2F6B4F", 0.3: "#C89B3C", 0.0: "#9A3D3D"}


def minute_of(col):
    return int(col.rsplit("_", 1)[1])


def fit(X, k, cov, seed=C.RANDOM_STATE, n_init=C.N_INIT):
    return GaussianMixture(k, covariance_type=cov, n_init=n_init, reg_covar=C.REG_COVAR,
                           max_iter=C.MAX_ITER, random_state=seed).fit(X)


def overnight_metrics(true_overnight, lab):
    """Cluster separation on TRUE overnight share + the most night-distinctive cluster."""
    s = pd.Series(true_overnight, name="ov"); g = s.groupby(lab).mean()
    sizes = pd.Series(lab).value_counts()
    top = g.idxmax()
    return float(g.std()), float(g.max()), int(sizes.get(top, 0))


def run_dataset(ds):
    X = pd.read_parquet(C.FEAT / f"X_{ds}.parquet"); X.index = X.index.astype(str)
    Xv0 = X.values.astype(float)
    ev_idx = [i for i, c in enumerate(X.columns) if EVENING[0] <= minute_of(c) < EVENING[1]]
    pm_idx = [i for i, c in enumerate(X.columns) if minute_of(c) >= POSTMID]
    true_overnight = Xv0[:, pm_idx].sum(1) if pm_idx else np.zeros(len(X))
    n = len(X); ss = min(2000, n); rng = np.random.default_rng(C.RANDOM_STATE)

    summary_rows, sweep_rows = [], []
    for w in WEIGHTS:
        Xw = Xv0.copy(); Xw[:, ev_idx] *= w
        # ---- BIC grid: per-weight covariance x K ----
        grid = []
        for cov in C.COVARIANCES:
            for k in C.K_RANGE:
                try:
                    grid.append({"covariance": cov, "K": k, "BIC": fit(Xw, k, cov).bic(Xw)})
                except Exception:
                    grid.append({"covariance": cov, "K": k, "BIC": np.nan})
        grid = pd.DataFrame(grid); grid.to_csv(SENS / f"{ds}_w{w}_bic_grid.csv", index=False)
        best = grid.loc[grid.BIC.idxmin()]; best_cov, best_K = best.covariance, int(best.K)

        # ---- full K-sweep at the per-weight BIC-best covariance ----
        for k in C.K_RANGE:
            lab = fit(Xw, k, best_cov).predict(Xw)
            ov_sep, top_ov, top_sz = overnight_metrics(true_overnight, lab)
            sweep_rows.append({"dataset": ds, "w": w, "covariance": best_cov, "K": k,
                               "silhouette": silhouette_score(Xw, lab, sample_size=ss, random_state=C.RANDOM_STATE),
                               "calinski_harabasz": calinski_harabasz_score(Xw, lab),
                               "davies_bouldin": davies_bouldin_score(Xw, lab),
                               "overnight_separation": ov_sep, "top_overnight_share": top_ov,
                               "top_overnight_cluster_size": top_sz,
                               "smallest": int(min(np.bincount(lab, minlength=k))),
                               "is_bic_best_K": (k == best_K)})
        # ---- bootstrap ARI at the BIC-best K ----
        ref = fit(Xw, best_K, best_cov).predict(Xw)
        aris = []
        for _ in range(C.N_BOOTSTRAP):
            idx = rng.choice(n, n, replace=True)
            aris.append(adjusted_rand_score(ref, fit(Xw[idx], best_K, best_cov, seed=int(rng.integers(1e6)), n_init=3).predict(Xw)))
        at = next(r for r in sweep_rows if r["dataset"] == ds and r["w"] == w and r["K"] == best_K)
        summary_rows.append({"dataset": ds, "w": w, "BIC_best_cov": best_cov, "BIC_best_K": best_K,
                             "silhouette@bestK": round(at["silhouette"], 3),
                             "overnight_sep@bestK": round(at["overnight_separation"], 4),
                             "top_overnight_share@bestK": round(at["top_overnight_share"], 4),
                             "top_ov_cluster_size@bestK": at["top_overnight_cluster_size"],
                             "bootstrap_ARI@bestK": round(float(np.mean(aris)), 3)})
        print(f"  {ds} w={w}: BIC-best {best_cov} K={best_K} | sil={at['silhouette']:.3f} ov_sep={at['overnight_separation']:.4f}")
    return pd.DataFrame(sweep_rows), pd.DataFrame(summary_rows)


def plot_compare(ds, sweep):
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
    for w in WEIGHTS:
        s = sweep[sweep.w == w].sort_values("K")
        ax[0].plot(s.K, s.overnight_separation, "-o", color=WCOLORS[w], label=f"w={w}")
        ax[1].plot(s.K, s.silhouette, "-o", color=WCOLORS[w], label=f"w={w}")
        bk = s[s.is_bic_best_K]
        if len(bk):
            ax[0].scatter(bk.K, bk.overnight_separation, s=160, facecolors="none", edgecolors=WCOLORS[w], lw=2, zorder=5)
            ax[1].scatter(bk.K, bk.silhouette, s=160, facecolors="none", edgecolors=WCOLORS[w], lw=2, zorder=5)
    ax[0].set_title(f"{ds} · overnight separation vs K\n(higher=clusters differ more overnight; circle=per-w BIC-best K)")
    ax[1].set_title(f"{ds} · silhouette vs K")
    for a in ax:
        a.set_xlabel("K"); a.set_xticks(list(C.K_RANGE)); a.grid(color="#eee")
        a.legend(fontsize=8, title="evening weight"); a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(SENS / f"{ds}_sensitivity_compare.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    all_sweep, all_summary = [], []
    for ds in DATASETS:
        print(f"=== {ds} ===")
        sweep, summ = run_dataset(ds)
        sweep.to_csv(SENS / f"{ds}_sweep.csv", index=False)
        plot_compare(ds, sweep)
        all_sweep.append(sweep); all_summary.append(summ)
    pd.concat(all_summary, ignore_index=True).to_csv(SENS / "downweight_summary.csv", index=False)
    pd.concat(all_sweep, ignore_index=True).to_csv(SENS / "downweight_sweep_all.csv", index=False)
    print("\n", pd.concat(all_summary, ignore_index=True).to_string(index=False))
    (SENS / "README.txt").write_text(
        "RIGOROUS evening (18:00-20:00) down-weighting sensitivity.\n"
        "For each weight w, the FULL BIC covariance x K selection is re-run, so each\n"
        "weight finds its own best (covariance, K). Metrics (overnight separation,\n"
        "top-overnight cluster) are computed on TRUE unweighted post-midnight shares\n"
        "for cross-weight comparability. Key figure: {ds}_sensitivity_compare.png.\n"
        "Isolated: reads features/ read-only; does not affect the main pipeline.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
