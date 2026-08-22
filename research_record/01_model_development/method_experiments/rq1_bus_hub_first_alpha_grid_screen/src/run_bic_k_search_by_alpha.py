"""Extension to the alpha-grid screen: does the BIC-preferred K move away from
K=3 once stronger direction-specific shrinkage suppresses low-count noise?

`run_alpha_grid_screen.py` forced K=3 at every alpha to isolate the shrinkage
effect cheaply. That design cannot detect a genuine change in cluster
structure. This script fills that gap: full-covariance BIC over K=2..12 at
each candidate alpha, then a confirmatory deep-dive (adjacent-K structure,
activity/timing effect sizes, and the same conditional multinomial resampling
stability diagnostic used for Gate 4) at K=3 and at each alpha's BIC-best K.

Two-stage n_init, following the precedent in
rq1_bus_activity_tiered_reclustering/src/01_threshold_selection.py: a cheap
exploratory scan to locate bic_best_K, then a full n_init=20 confirmatory
refit only for the (alpha, K) pairs actually carried into the deep dive.

Writes only inside rq1_bus_hub_first_alpha_grid_screen/outputs.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy import stats
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_alpha_grid_screen as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
DATA = OUT / "data"
DIAGNOSTICS = OUT / "diagnostics"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
for directory in (OUT, DATA, DIAGNOSTICS, FIGURES, REPORT):
    directory.mkdir(parents=True, exist_ok=True)

ALPHA_CANDIDATES = [5.0, 20.0, 50.0, 100.0, 200.0]
K_RANGE = list(range(2, 13))
SCAN_N_INIT = 5
DEEPDIVE_N_INIT = 20
REG_COVAR = base.REG_COVAR
MAX_ITER = base.MAX_ITER
SEED = 42
RESAMPLE_REPLICATES = 20
LOW_ACTIVITY_THRESHOLD = base.LOW_ACTIVITY_THRESHOLD


def log(message: str) -> None:
    print(message, flush=True)


def fit_gmm(X: np.ndarray, k: int, seed: int, n_init: int) -> tuple[GaussianMixture, float]:
    started = time.perf_counter()
    model = GaussianMixture(
        n_components=k,
        covariance_type="full",
        n_init=n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=seed,
    ).fit(X)
    return model, time.perf_counter() - started


def effect_sizes(metrics: pd.DataFrame, labels: np.ndarray) -> dict:
    _, _, kw_eps2 = base.kw_epsilon_squared(metrics["log_total_activity"], labels)
    out = {"kw_epsilon2_log_total_activity": kw_eps2}
    for metric in [
        "log_total_activity",
        "direction_balance",
        "post_midnight_share",
        "deep_night_share",
        "post_midnight_persistence",
        "weekend_ratio",
    ]:
        out[f"eta2_{metric}"] = base.eta_squared(metrics[metric], labels)
    out["timing_mean_eta2"] = float(
        np.mean([out[f"eta2_{m}"] for m in base.TIMING_METRICS])
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=RESAMPLE_REPLICATES)
    args = parser.parse_args()
    started = time.time()
    started_iso = datetime.now(timezone.utc).isoformat()

    log("[1/6] Rebuilding the fixed 3,593-LSOA hub-first sample")
    counts, priors, meta, metrics = base.prepare_counts()

    log(f"[2/6] Exploratory full-covariance BIC scan, K=2..12, n_init={SCAN_N_INIT}")
    scan_rows = []
    scan_labels: dict[tuple[float, int], np.ndarray] = {}
    for alpha in ALPHA_CANDIDATES:
        X = base.features_for_alpha(counts, priors, alpha).to_numpy(dtype=float)
        for k in K_RANGE:
            model, seconds = fit_gmm(X, k, SEED, SCAN_N_INIT)
            labels = model.predict(X)
            scan_labels[(alpha, k)] = labels
            sizes = np.bincount(labels, minlength=k)
            scan_rows.append(
                {
                    "alpha": alpha,
                    "K": k,
                    "BIC": float(model.bic(X)),
                    "AIC": float(model.aic(X)),
                    "converged": bool(model.converged_),
                    "fit_seconds": seconds,
                    "min_cluster_n": int(sizes.min()),
                    "min_cluster_share": float(sizes.min() / sizes.sum()),
                }
            )
        log(f"      alpha={alpha:g} scan done")
    scan = pd.DataFrame(scan_rows)
    scan.to_csv(DIAGNOSTICS / "bic_k_search_scan_grid.csv", index=False)

    bic_best = (
        scan.sort_values("BIC").groupby("alpha", as_index=False).first()[["alpha", "K", "BIC"]]
        .rename(columns={"K": "bic_best_K", "BIC": "bic_best_value"})
    )
    bic_best.to_csv(DATA / "bic_k_search_best_k_by_alpha.csv", index=False)
    log("      BIC-best K by alpha:")
    for _, row in bic_best.iterrows():
        log(f"        alpha={row['alpha']:g}: bic_best_K={int(row['bic_best_K'])}")

    log("[3/6] Adjacent-K structure at each alpha (from the exploratory scan)")
    adjacent_rows = []
    for alpha in ALPHA_CANDIDATES:
        for k in K_RANGE[:-1]:
            parent = scan_labels[(alpha, k)]
            child = scan_labels[(alpha, k + 1)]
            table = pd.crosstab(pd.Series(parent, name="parent"), pd.Series(child, name="child"))
            weighted_purity = float(table.max(axis=0).sum() / table.to_numpy().sum())
            child_sizes = table.sum(axis=0)
            adjacent_rows.append(
                {
                    "alpha": alpha,
                    "K_parent": k,
                    "K_child": k + 1,
                    "ARI_adjacent": float(adjusted_rand_score(parent, child)),
                    "weighted_child_to_parent_purity": weighted_purity,
                    "smallest_child_share": float(child_sizes.min() / child_sizes.sum()),
                }
            )
    adjacent = pd.DataFrame(adjacent_rows)
    adjacent.to_csv(DIAGNOSTICS / "bic_k_search_adjacent_k.csv", index=False)

    log(f"[4/6] Confirmatory refit at n_init={DEEPDIVE_N_INIT} for K=3 and each alpha's BIC-best K")
    deepdive_pairs: list[tuple[float, int]] = []
    for alpha in ALPHA_CANDIDATES:
        bk = int(bic_best.loc[bic_best["alpha"] == alpha, "bic_best_K"].iloc[0])
        for k in sorted({3, bk}):
            deepdive_pairs.append((alpha, k))

    deepdive_rows = []
    fitted_models: dict[tuple[float, int], GaussianMixture] = {}
    fitted_features: dict[tuple[float, int], np.ndarray] = {}
    fitted_labels: dict[tuple[float, int], np.ndarray] = {}
    rng_sample = np.random.default_rng(SEED)
    for alpha, k in deepdive_pairs:
        X_df = base.features_for_alpha(counts, priors, alpha)
        X = X_df.to_numpy(dtype=float)
        model, seconds = fit_gmm(X, k, SEED, DEEPDIVE_N_INIT)
        labels = model.predict(X)
        fitted_models[(alpha, k)] = model
        fitted_features[(alpha, k)] = X
        fitted_labels[(alpha, k)] = labels
        sample_idx = rng_sample.choice(len(X), size=min(2000, len(X)), replace=False)
        sizes = np.bincount(labels, minlength=k)
        row = {
            "alpha": alpha,
            "K": k,
            "is_bic_best_K": k == int(bic_best.loc[bic_best["alpha"] == alpha, "bic_best_K"].iloc[0]),
            "BIC": float(model.bic(X)),
            "converged": bool(model.converged_),
            "fit_seconds": seconds,
            "silhouette": float(silhouette_score(X[sample_idx], labels[sample_idx])),
            "min_cluster_n": int(sizes.min()),
            "min_cluster_share": float(sizes.min() / sizes.sum()),
            **effect_sizes(metrics, labels),
        }
        deepdive_rows.append(row)
        log(
            f"      alpha={alpha:g} K={k}: BIC={row['BIC']:.1f} sil={row['silhouette']:.3f} "
            f"activity_eps2={row['kw_epsilon2_log_total_activity']:.3f} "
            f"timing_mean_eta2={row['timing_mean_eta2']:.3f} min_share={row['min_cluster_share']:.3f}"
        )
    deepdive = pd.DataFrame(deepdive_rows)

    log(f"[5/6] Conditional multinomial resampling at each deep-dive (alpha, K), n={args.replicates}")
    rng = np.random.default_rng(SEED + 20260721)
    low_mask = metrics["total_activity"].to_numpy() < LOW_ACTIVITY_THRESHOLD
    high_mask = ~low_mask
    resample_rows = []
    for replicate in range(args.replicates):
        sample_a = base.resample_counts(rng, counts)
        sample_b = base.resample_counts(rng, counts)
        for alpha, k in deepdive_pairs:
            model = fitted_models[(alpha, k)]
            pred_a = model.predict(base.features_from_resample(sample_a, priors, alpha))
            pred_b = model.predict(base.features_from_resample(sample_b, priors, alpha))
            resample_rows.append(
                {
                    "alpha": alpha,
                    "K": k,
                    "replicate": replicate,
                    "ari_below450": adjusted_rand_score(pred_a[low_mask], pred_b[low_mask]),
                    "ari_at_least450": adjusted_rand_score(pred_a[high_mask], pred_b[high_mask]),
                    "ari_all": adjusted_rand_score(pred_a, pred_b),
                }
            )
        log(f"      replicate {replicate + 1}/{args.replicates}")
    resamples = pd.DataFrame(resample_rows)
    resamples.to_csv(DIAGNOSTICS / "bic_k_search_resamples.csv", index=False)
    resample_summary = (
        resamples.groupby(["alpha", "K"], as_index=False)
        .agg(
            resample_below450_ari_mean=("ari_below450", "mean"),
            resample_below450_ari_sd=("ari_below450", "std"),
            resample_at_least450_ari_mean=("ari_at_least450", "mean"),
            resample_all_ari_mean=("ari_all", "mean"),
        )
    )
    deepdive = deepdive.merge(resample_summary, on=["alpha", "K"], how="left")

    log("[6/6] Applying the pre-declared decision rule and writing the report")
    baseline = deepdive.loc[(deepdive["alpha"] == 5.0) & (deepdive["K"] == 3)].iloc[0]
    deepdive["timing_retention_vs_reference"] = deepdive["timing_mean_eta2"] / baseline["timing_mean_eta2"]
    deepdive["resample_below450_ari_vs_reference"] = (
        deepdive["resample_below450_ari_mean"] - baseline["resample_below450_ari_mean"]
    )
    deepdive["gate_activity_below_timing"] = deepdive["eta2_log_total_activity"] < deepdive["timing_mean_eta2"]
    deepdive["gate_timing_retention"] = deepdive["timing_retention_vs_reference"] >= 0.85
    deepdive["gate_cluster_size"] = deepdive["min_cluster_share"] >= 0.05
    deepdive["gate_low_activity_repeatability"] = deepdive["resample_below450_ari_mean"] >= (
        baseline["resample_below450_ari_mean"] + 0.05
    )
    gate_columns = [
        "gate_activity_below_timing",
        "gate_timing_retention",
        "gate_cluster_size",
        "gate_low_activity_repeatability",
    ]
    deepdive["alternate_k_adopts"] = deepdive[gate_columns].all(axis=1) & (~deepdive["K"].eq(3) | deepdive["alpha"].eq(5.0))
    deepdive.to_csv(DATA / "bic_k_search_deepdive_summary.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for alpha in ALPHA_CANDIDATES:
        sub = scan[scan["alpha"] == alpha]
        axes[0].plot(sub["K"], sub["BIC"], marker="o", label=f"alpha={alpha:g}")
    axes[0].set_xlabel("K")
    axes[0].set_ylabel("BIC (scan, n_init=5)")
    axes[0].set_title("Full-covariance BIC by K, per alpha")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.25)

    axes[1].bar([f"a={a:g}" for a in bic_best["alpha"]], bic_best["bic_best_K"])
    axes[1].axhline(3, color="black", linestyle="--", linewidth=1, label="K=3 reference")
    axes[1].set_ylabel("BIC-best K")
    axes[1].set_title("BIC-preferred K by alpha")
    axes[1].legend(fontsize=8)
    fig.savefig(FIGURES / "bic_k_search_by_alpha.png", dpi=180)
    plt.close(fig)

    elapsed = time.time() - started
    run_environment = {
        "command": "python src/run_bic_k_search_by_alpha.py",
        "started_utc": started_iso,
        "elapsed_seconds": elapsed,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "seed": SEED,
        "scan_n_init": SCAN_N_INIT,
        "deepdive_n_init": DEEPDIVE_N_INIT,
        "replicates": args.replicates,
        "reg_covar": REG_COVAR,
        "max_iter": MAX_ITER,
    }
    (OUT / "run_environment_bic_k_search.json").write_text(json.dumps(run_environment, indent=2), encoding="utf-8")

    write_report(scan, bic_best, adjacent, deepdive, baseline, started_iso, elapsed)
    log(f"Completed in {elapsed:.1f}s")
    log(str(REPORT / "BIC_K_SEARCH_BY_ALPHA.md"))


def write_report(
    scan: pd.DataFrame,
    bic_best: pd.DataFrame,
    adjacent: pd.DataFrame,
    deepdive: pd.DataFrame,
    baseline: pd.Series,
    started_iso: str,
    elapsed: float,
) -> None:
    display_cols = [
        "alpha", "K", "is_bic_best_K", "BIC", "silhouette", "min_cluster_share",
        "kw_epsilon2_log_total_activity", "eta2_log_total_activity", "timing_mean_eta2",
        "timing_retention_vs_reference", "resample_below450_ari_mean",
        "resample_below450_ari_vs_reference", "alternate_k_adopts",
    ]
    moved = bic_best[bic_best["bic_best_K"] != 3]
    moved_text = (
        ", ".join(f"alpha={row.alpha:g}->K={int(row.bic_best_K)}" for row in moved.itertuples())
        if not moved.empty
        else "none: every alpha in {5, 20, 50, 100, 200} still has BIC-best K=3"
    )
    adopted = deepdive.loc[deepdive["alternate_k_adopts"] & (deepdive["K"] != 3), ["alpha", "K"]]
    adopted_text = (
        ", ".join(f"alpha={row.alpha:g}, K={int(row.K)}" for row in adopted.itertuples())
        if not adopted.empty
        else "None"
    )
    report = f"""## Material Passport

- Origin: Claude Code, follow-up to rq1_bus_hub_first_alpha_grid_screen
- Verification Status: ANALYZED
- Version Label: bic_k_search_by_alpha_v1

# Does the BIC-preferred K move away from 3 as shrinkage increases?

## Motivation

`ALPHA_GRID_SCREEN.md` forced K=3 at every alpha to isolate the shrinkage
effect cheaply. That design cannot detect whether suppressing low-count
compositional noise changes the natural cluster count. This is a known
precedent in this project: the unrelated reliable-core reclustering
(`rq1_bus_activity_tiered_reclustering`) found BIC-best K=2 once low-activity
units were excluded, even though bootstrap stability still favoured K=3.

## Stage 1: exploratory BIC scan (full covariance, K=2..12, n_init=5)

BIC-best K by alpha:

{bic_best.to_markdown(index=False)}

**BIC-preferred K shift vs the established K=3 reference: {moved_text}.**

Full scan grid: `outputs/diagnostics/bic_k_search_scan_grid.csv`.
Adjacent-K purity/ARI at every alpha: `outputs/diagnostics/bic_k_search_adjacent_k.csv`.

## Stage 2: confirmatory deep dive (full covariance, n_init=20)

Only K=3 and each alpha's BIC-best K (deduplicated) were refit at full
n_init. `resample_below450_ari_vs_reference` compares against the
alpha=5/K=3 reference ({baseline['resample_below450_ari_mean']:.3f}), which
is the same quantity Gate 4 in `ALPHA_GRID_SCREEN.md` used.

{deepdive[display_cols].to_markdown(index=False)}

## Decision rule (pre-declared before reading Stage 2 results)

An alternate K at a given alpha is only a candidate replacement for the
K=3 reference if, relative to the alpha=5/K=3 baseline:

1. activity ANOVA eta-squared stays below the mean of the three timing
   metrics' eta-squared at that (alpha, K);
2. mean timing eta-squared retains at least 85% of the alpha=5/K=3 baseline;
3. every cluster contains at least 5% of LSOAs;
4. the below-450 conditional-resampling ARI is at least 0.05 higher than the
   alpha=5/K=3 baseline (not just higher than the same alpha forced to K=3;
   it must beat the original reference outright).

Adopting an alternate K also requires it to be the alpha's BIC-best K, not a
manually chosen runner-up.

**(alpha, K) pairs meeting all four conditions: {adopted_text}.**

## Reading

This resolves the open question directly: within the alphas already
screened, {"structure does move" if not moved.empty else "BIC does not prefer a different K"}
{"(see the shift above), but that alone does not automatically justify adopting the new K" if not moved.empty else ""}
-- Gate 4's failure mode in `ALPHA_GRID_SCREEN.md` (low-activity resampling
stability not improving) is evaluated again here at each alpha's own
BIC-best K, not only at a forced K=3. If the adopted-pairs list above is
empty, the conclusion is that stronger shrinkage does not unlock a more
defensible structure in the range tested; if it is non-empty, that (alpha, K)
pair is the next candidate for the full historical-comparison and profile
work already done for K=3.

## Warnings and limitations

- Stage 1 uses n_init=5 for tractability; BIC differences smaller than
  run-to-run BIC noise at that n_init should not be over-interpreted --
  Stage 2 exists precisely to re-check the surviving candidates at n_init=20.
- The conditional multinomial resampling diagnostic still only measures
  count-sampling repeatability with the GMM held fixed; it does not include
  refitting uncertainty (same limitation as `ALPHA_GRID_SCREEN.md`).
- Comparing BIC across different alpha values remains invalid; BIC is only
  used within a fixed alpha to choose K here.
- Six alphas were not exhaustively re-swept in Stage 2 -- only K=3 and each
  alpha's own BIC-best K were confirmed. A K that is second-best by BIC but
  more stable is not evaluated by this script.

---

Started {started_iso}; elapsed {elapsed:.1f}s.
"""
    (REPORT / "BIC_K_SEARCH_BY_ALPHA.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
