"""Exclude the bottom 20% of hub-first bus LSOAs by full-week total activity,
then run the project's original GMM/BIC pipeline (4 covariance families,
K=2..12, n_init=20, seed=42 -- matching rq1_bus_hub_first_reclustering/src
/config.py exactly) on the remaining 80%, alpha=0 (no shrinkage, since the
exclusion itself is now the noise-control mechanism being tested).

This directly tests: does removing the lowest-activity fifth of LSOAs let the
project's standard, unmodified method find a clean, non-activity-dominated
K on its own -- without forcing K=3, without a weaker-direction floor, and
without empirical-Bayes shrinkage.

Reuses only the pure fitting helpers from run_fullweek_first_pass.py
(fit_gmm, cluster_size_metrics, matched_jaccard). It does not call that
script's file-writing functions, so it cannot overwrite the existing
hub-first reclustering outputs. Writes only inside
rq1_bus_hub_first_reliable_core_assignment/outputs.
"""

from __future__ import annotations

import hashlib
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
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent

BASE_SRC = FYP / "rq1_bus_hub_first_reclustering" / "src"
sys.path.insert(0, str(BASE_SRC))
import config as C  # noqa: E402
import run_fullweek_first_pass as base  # noqa: E402

X_INPUT = (
    FYP
    / "rq1_bus_hub_first_reclustering_alpha_sensitivity"
    / "outputs"
    / "features"
    / "X_bus_fullweek_alpha0_fixed_sample.parquet"
)
META_INPUT = (
    FYP / "rq1_bus_hub_first_reclustering" / "outputs" / "features" / "bus_fullweek_meta_alpha5.csv"
)
METRICS_INPUT = (
    FYP / "rq1_bus_hub_first_alpha_grid_screen" / "outputs" / "data" / "hub_first_raw_metrics.csv"
)
REFERENCE_ALPHA5_GRID = FYP / "rq1_bus_hub_first_reclustering" / "outputs" / "diagnostics" / "bus_fullweek_bic_grid.csv"
REFERENCE_ALPHA0_GRID = (
    FYP / "rq1_bus_hub_first_reclustering_alpha_sensitivity" / "outputs" / "diagnostics" / "alpha0_bic_grid.csv"
)

OUT = ROOT / "outputs"
DATA = OUT / "data"
DIAGNOSTICS = OUT / "diagnostics"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
for directory in (OUT, DATA, DIAGNOSTICS, FIGURES, REPORT):
    directory.mkdir(parents=True, exist_ok=True)

TIMING_METRICS = ["post_midnight_share", "deep_night_share", "post_midnight_persistence"]
EXCLUDE_QUANTILE = 0.20
K_RANGE = list(range(2, 13))
PROFILE_K = list(range(2, 9))
BOOTSTRAP_REPLICATES = 20


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = float(y.mean())
    total = float(np.square(y - grand).sum())
    if total <= 0:
        return float("nan")
    between = 0.0
    for cluster in np.unique(labels):
        mask = labels == cluster
        between += int(mask.sum()) * (float(y[mask].mean()) - grand) ** 2
    return float(between / total)


def kw_epsilon_squared(values: pd.Series, labels: np.ndarray) -> float:
    groups = [values.to_numpy(dtype=float)[labels == cluster] for cluster in np.unique(labels)]
    result = stats.kruskal(*groups)
    n = sum(len(group) for group in groups)
    k = len(groups)
    return float((float(result.statistic) - k + 1) / (n - k))


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    X = pd.read_parquet(X_INPUT)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    meta = pd.read_csv(META_INPUT)
    meta["lsoa"] = meta["lsoa"].astype(str)
    meta = meta.set_index("lsoa").reindex(X.index)
    metrics = pd.read_csv(METRICS_INPUT)
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    metrics = metrics.set_index("lsoa").reindex(X.index)
    required = ["total_activity", "log_total_activity", "direction_balance", "weekend_ratio", *TIMING_METRICS]
    if metrics[required].isna().any().any():
        raise ValueError("Raw metrics missing for retained LSOAs")
    return X, metrics


def main() -> None:
    started = time.time()
    started_iso = datetime.now(timezone.utc).isoformat()
    log("[1/7] Loading fixed hub-first alpha=0 sample and raw metrics")
    X, metrics = load_inputs()
    n_total = len(X)

    cutoff = float(metrics["total_activity"].quantile(EXCLUDE_QUANTILE))
    keep_mask = metrics["total_activity"].to_numpy(dtype=float) >= cutoff
    X_core = X.loc[keep_mask]
    metrics_core = metrics.loc[keep_mask]
    n_core = len(X_core)
    log(
        f"      Bottom {EXCLUDE_QUANTILE*100:.0f}% cutoff (total_activity) = {cutoff:.2f}; "
        f"excluded={n_total - n_core} ({100*(n_total-n_core)/n_total:.1f}%); "
        f"retained={n_core} ({100*n_core/n_total:.1f}%)"
    )

    manifest = pd.DataFrame(
        [
            {"role": "alpha0_features", "path": str(X_INPUT.resolve()), "sha256": sha256(X_INPUT)},
            {"role": "hub_first_meta", "path": str(META_INPUT.resolve()), "sha256": sha256(META_INPUT)},
            {"role": "hub_first_raw_metrics", "path": str(METRICS_INPUT.resolve()), "sha256": sha256(METRICS_INPUT)},
        ]
    )
    manifest.to_csv(DATA / "input_manifest_bottom20_excluded.csv", index=False)
    (DATA / "bottom20_exclusion_summary.json").write_text(
        json.dumps(
            {
                "exclude_quantile": EXCLUDE_QUANTILE,
                "total_activity_cutoff": cutoff,
                "n_total": n_total,
                "n_excluded": int(n_total - n_core),
                "n_core": n_core,
                "pct_core": 100.0 * n_core / n_total,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    Xv = X_core.to_numpy(dtype=float)

    log("[2/7] Full BIC grid: 4 covariance families x K=2..12, n_init=20 (matching config.py)")
    grid_rows = []
    models: dict[tuple[str, int], object] = {}
    for covariance in C.COVARIANCES:
        for k in K_RANGE:
            model, warnings_list, seconds = base.fit_gmm(Xv, k, covariance, C.RANDOM_STATE, C.N_INIT)
            models[(covariance, k)] = model
            labels = model.predict(Xv)
            grid_rows.append(
                {
                    "covariance": covariance,
                    "K": k,
                    "BIC": float(model.bic(Xv)),
                    "AIC": float(model.aic(Xv)),
                    "converged": bool(model.converged_),
                    "fit_seconds": seconds,
                    **base.cluster_size_metrics(labels, k),
                }
            )
            log(
                f"      {covariance:9s} K={k:2d} BIC={grid_rows[-1]['BIC']:.1f} "
                f"min_n={grid_rows[-1]['min_cluster_n']:4d} ({seconds:.1f}s)"
            )
    grid = pd.DataFrame(grid_rows)
    grid.to_csv(DIAGNOSTICS / "bottom20_excluded_bic_grid.csv", index=False)
    best = grid.loc[grid["BIC"].idxmin()]
    best_covariance, best_k = str(best["covariance"]), int(best["K"])
    log(f"      Global BIC minimum: covariance={best_covariance}, K={best_k}")

    log(f"[3/7] K diagnostics at BIC-best covariance={best_covariance} (reusing cached fits)")
    kdiag_rows = []
    labels_by_k: dict[int, np.ndarray] = {}
    for k in K_RANGE:
        model = models[(best_covariance, k)]
        labels = model.predict(Xv)
        labels_by_k[k] = labels
        kdiag_rows.append(
            {
                "K": k,
                "BIC": float(model.bic(Xv)),
                "silhouette": float(silhouette_score(Xv, labels)),
                "davies_bouldin": float(davies_bouldin_score(Xv, labels)),
                "activity_eta2": eta_squared(metrics_core["log_total_activity"], labels),
                "activity_kw_epsilon2": kw_epsilon_squared(metrics_core["log_total_activity"], labels),
                "timing_mean_eta2": float(
                    np.mean([eta_squared(metrics_core[m], labels) for m in TIMING_METRICS])
                ),
                "direction_balance_eta2": eta_squared(metrics_core["direction_balance"], labels),
                "weekend_ratio_eta2": eta_squared(metrics_core["weekend_ratio"], labels),
                **base.cluster_size_metrics(labels, k),
            }
        )
    kdiag = pd.DataFrame(kdiag_rows)
    kdiag["gate_activity_below_timing"] = kdiag["activity_eta2"] < kdiag["timing_mean_eta2"]
    kdiag.to_csv(DIAGNOSTICS / "bottom20_excluded_kdiag.csv", index=False)
    for _, row in kdiag.iterrows():
        log(
            f"      K={int(row['K']):2d} sil={row['silhouette']:.3f} "
            f"activity_eta2={row['activity_eta2']:.3f} timing_mean_eta2={row['timing_mean_eta2']:.3f} "
            f"pass={row['gate_activity_below_timing']}"
        )

    log(f"[4/7] Adjacent-K structure at covariance={best_covariance}")
    adjacent_rows = []
    for k in K_RANGE[:-1]:
        parent, child = labels_by_k[k], labels_by_k[k + 1]
        table = pd.crosstab(pd.Series(parent, name="parent"), pd.Series(child, name="child"))
        weighted_purity = float(table.max(axis=0).sum() / table.to_numpy().sum())
        child_sizes = table.sum(axis=0)
        adjacent_rows.append(
            {
                "K_parent": k,
                "K_child": k + 1,
                "ARI_adjacent": float(adjusted_rand_score(parent, child)),
                "weighted_child_to_parent_purity": weighted_purity,
                "smallest_child_share": float(child_sizes.min() / child_sizes.sum()),
            }
        )
    adjacent = pd.DataFrame(adjacent_rows)
    adjacent.to_csv(DIAGNOSTICS / "bottom20_excluded_adjacent_k.csv", index=False)

    log(f"[5/7] Bootstrap stability, K={PROFILE_K}, n={BOOTSTRAP_REPLICATES}, n_init={C.BOOTSTRAP_N_INIT}")
    rng = np.random.default_rng(C.RANDOM_STATE)
    boot_rows = []
    recovery_rows = []
    for k in PROFILE_K:
        base_labels = labels_by_k[k]
        for replicate in range(BOOTSTRAP_REPLICATES):
            idx = rng.choice(len(Xv), size=len(Xv), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model, _, seconds = base.fit_gmm(Xv[idx], k, best_covariance, seed, C.BOOTSTRAP_N_INIT)
            predicted = model.predict(Xv)
            matched = base.matched_jaccard(base_labels, predicted, k)
            boot_rows.append(
                {
                    "K": k,
                    "replicate": replicate + 1,
                    "ARI": float(adjusted_rand_score(base_labels, predicted)),
                    "mean_matched_cluster_jaccard": float(matched.mean()),
                    "min_matched_cluster_jaccard": float(matched.min()),
                    "converged": bool(model.converged_),
                }
            )
            for cluster, score in enumerate(matched):
                recovery_rows.append({"K": k, "replicate": replicate + 1, "base_cluster": cluster, "matched_jaccard": float(score)})
        sub = pd.DataFrame(boot_rows)
        sub = sub[sub["K"] == k]
        log(f"      K={k}: ARI mean={sub['ARI'].mean():.3f}; min-cluster Jaccard mean={sub['min_matched_cluster_jaccard'].mean():.3f}")
    bootstrap = pd.DataFrame(boot_rows)
    recovery = pd.DataFrame(recovery_rows)
    bootstrap.to_csv(DIAGNOSTICS / "bottom20_excluded_bootstrap.csv", index=False)
    recovery.to_csv(DIAGNOSTICS / "bottom20_excluded_bootstrap_cluster_recovery.csv", index=False)
    boot_summary = bootstrap.groupby("K", as_index=False).agg(
        bootstrap_ari_mean=("ARI", "mean"),
        bootstrap_ari_sd=("ARI", "std"),
        bootstrap_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
    )
    kdiag = kdiag.merge(boot_summary, on="K", how="left")
    kdiag.to_csv(DIAGNOSTICS / "bottom20_excluded_kdiag.csv", index=False)

    log("[6/7] Historical/no-exclusion comparison and figures")
    reference_rows = [
        {"version": "old_nonhubfirst_alpha5_k3 (n=4100)", "activity_eta2": 0.518, "timing_mean_eta2": None},
        {"version": "hub_first_alpha5_k3 (n=3593, no exclusion)", "activity_eta2": 0.5180, "timing_mean_eta2": 0.2989},
        {"version": "hub_first_alpha0_k3 (n=3593, no exclusion)", "activity_eta2": 0.5222, "timing_mean_eta2": 0.2840},
    ]
    pd.DataFrame(reference_rows).to_csv(DATA / "reference_baselines.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    axes[0].plot(kdiag["K"], kdiag["activity_eta2"], marker="o", label="activity eta2")
    axes[0].plot(kdiag["K"], kdiag["timing_mean_eta2"], marker="s", label="timing mean eta2")
    axes[0].set_xlabel("K")
    axes[0].set_title(f"Bottom-20%-excluded (n={n_core}): activity vs timing")
    axes[0].legend()
    axes[0].grid(alpha=0.25)
    axes[1].plot(kdiag["K"], kdiag["bootstrap_ari_mean"], marker="o", label="bootstrap ARI")
    axes[1].plot(kdiag["K"], kdiag["bootstrap_min_cluster_jaccard_mean"], marker="s", label="min-cluster Jaccard")
    axes[1].set_xlabel("K")
    axes[1].set_title("Bootstrap stability")
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    fig.savefig(FIGURES / "bottom20_excluded_k_diagnostics.png", dpi=180)
    plt.close(fig)

    log("[7/7] Writing report")
    elapsed = time.time() - started
    write_report(cutoff, n_total, n_core, grid, best_covariance, best_k, kdiag, adjacent, reference_rows, started_iso, elapsed)
    (OUT / "run_environment_bottom20_excluded.json").write_text(
        json.dumps(
            {
                "started_utc": started_iso,
                "elapsed_seconds": elapsed,
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scipy": scipy.__version__,
                "scikit_learn": sklearn.__version__,
                "seed": C.RANDOM_STATE,
                "n_init": C.N_INIT,
                "bootstrap_n_init": C.BOOTSTRAP_N_INIT,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "exclude_quantile": EXCLUDE_QUANTILE,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    log(f"Completed in {elapsed:.1f}s")
    log(str(REPORT / "BOTTOM20_EXCLUDED_RESULTS.md"))


def write_report(
    cutoff: float,
    n_total: int,
    n_core: int,
    grid: pd.DataFrame,
    best_covariance: str,
    best_k: int,
    kdiag: pd.DataFrame,
    adjacent: pd.DataFrame,
    reference_rows: list[dict],
    started_iso: str,
    elapsed: float,
) -> None:
    best_by_cov = grid.sort_values("BIC").groupby("covariance", as_index=False).first()[
        ["covariance", "K", "BIC", "min_cluster_n", "min_cluster_share"]
    ]
    selected = kdiag[kdiag["K"] == best_k].iloc[0]
    report = f"""## Material Passport

- Origin: Claude Code
- Verification Status: ANALYZED
- Version Label: bottom20_excluded_bic_v1

# Bottom-20%-excluded, alpha=0, unforced GMM/BIC ("old method") result

## Design

Bottom {int(round((n_total-n_core)/n_total*100))}% of the fixed hub-first
3,593-LSOA sample excluded by full-week `total_activity` (cutoff =
{cutoff:.2f}); n_total={n_total}, n_core={n_core}
({100*n_core/n_total:.1f}% retained). Features are alpha=0 (no empirical-Bayes
shrinkage) direction-normalised 72-vectors -- exclusion, not shrinkage, is
the only noise-control mechanism tested here. GMM settings match
`rq1_bus_hub_first_reclustering/src/config.py` exactly: 4 covariance
families, K=2..12, n_init=20, reg_covar=1e-6, max_iter=300, seed=42. K is
not forced to any value.

## Global BIC result

Global BIC minimum: **covariance={best_covariance}, K={best_k}**.

{best_by_cov.to_markdown(index=False)}

## K diagnostics at covariance={best_covariance}

{kdiag[['K','BIC','silhouette','activity_eta2','timing_mean_eta2','gate_activity_below_timing','min_cluster_share','bootstrap_ari_mean','bootstrap_min_cluster_jaccard_mean']].to_markdown(index=False)}

## Adjacent-K structure

{adjacent.to_markdown(index=False)}

## Comparison to no-exclusion baselines (same hub-first sample, K=3)

{pd.DataFrame(reference_rows).to_markdown(index=False)}

## Reading

The BIC-best K here is **{best_k}** under covariance={best_covariance}.
At that K, activity_eta2={selected['activity_eta2']:.4f} versus
timing_mean_eta2={selected['timing_mean_eta2']:.4f}
({"resolved" if selected['gate_activity_below_timing'] else "still activity-dominated"}).
This uses the project's original, unmodified GMM/BIC method (all four
covariance families, full K range, no forced K, no weaker-direction filter,
no shrinkage) on the bottom-20%-excluded sample, so it is a direct test of
whether simple activity-based exclusion alone -- without any of the more
elaborate mechanisms tried earlier (shrinkage grids, weaker-direction
thresholds, BIC-per-threshold search) -- lets the standard method find a
clean structure on its own.

## Warnings and limitations

- BIC values here are only comparable within this sample; they cannot be
  ranked against the no-exclusion baselines' BIC (different n, different
  feature realisation).
- Bootstrap uses K=2..8 only (`PROFILE_K` in the historical config); K=9..12
  are reported for BIC/silhouette only.
- This is a single exclusion quantile (20%). It is not yet a swept threshold
  search like `01_threshold_screen.py`; if this result looks promising, the
  next step is a small quantile sweep (e.g. 10/15/20/25/30%) with the same
  unforced BIC procedure, not a one-shot adoption.

---

Started {started_iso}; elapsed {elapsed:.1f}s.
"""
    (REPORT / "BOTTOM20_EXCLUDED_RESULTS.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
