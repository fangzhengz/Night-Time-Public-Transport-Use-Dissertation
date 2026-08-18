"""Fixed-sample alpha grid for the hub-first full-week bus K=3 candidate.

The experiment changes only direction-specific prior concentration alpha.
It screens whether stronger shrinkage can reduce activity-label association
while retaining temporal differentiation and improving low-activity label
repeatability under conditional multinomial count resampling.

This script writes only inside rq1_bus_hub_first_alpha_grid_screen/outputs.
"""

from __future__ import annotations

import argparse
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
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

UPSTREAM = FYP / "rq1_bus_hub_first_reorganisation"
BASE = FYP / "rq1_bus_hub_first_reclustering"
ALPHA0_BASE = FYP / "rq1_bus_hub_first_reclustering_alpha_sensitivity"

LONG_INPUT = UPSTREAM / "outputs" / "preprocessed" / "bus_lsoa_night_long.parquet"
EXCEPTION_INPUT = UPSTREAM / "outputs" / "data" / "one_direction_exception_areas.csv"
REFERENCE_X = BASE / "outputs" / "features" / "X_bus_fullweek_alpha5.parquet"
REFERENCE_META = BASE / "outputs" / "features" / "bus_fullweek_meta_alpha5.csv"
REFERENCE_ALPHA5_LABELS = BASE / "outputs" / "labels" / "bus_fullweek_k3_labels.csv"
REFERENCE_ALPHA0_LABELS = ALPHA0_BASE / "outputs" / "labels" / "alpha0_full_k3_labels.csv"

OUT = ROOT / "outputs"
DATA = OUT / "data"
DIAGNOSTICS = OUT / "diagnostics"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
for directory in (OUT, DATA, DIAGNOSTICS, FIGURES, REPORT):
    directory.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
HOURS = list(range(1080, 1800, 60))
MIN_TOTAL = 50.0
LOW_ACTIVITY_THRESHOLD = 450.0
REG_COVAR = 1e-6
MAX_ITER = 300
TIMING_METRICS = [
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
]


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alphas", type=float, nargs="+", required=True)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--covariance", choices=["spherical", "diag", "tied", "full"], default="full")
    parser.add_argument("--n-init", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--replicates", type=int, default=20)
    args = parser.parse_args()
    if len(set(args.alphas)) != len(args.alphas):
        raise ValueError("Alphas must be unique")
    if any(alpha < 0 for alpha in args.alphas):
        raise ValueError("Alpha must be non-negative")
    if 5.0 not in args.alphas:
        raise ValueError("alpha=5 is required as the comparison baseline")
    if args.k < 2 or args.n_init < 1 or args.replicates < 1:
        raise ValueError("Invalid K, n-init, or replicate count")
    return args


def validate_long(long: pd.DataFrame) -> None:
    required = {"lsoa", "day_type", "direction", "hour_bin", "count"}
    missing = required.difference(long.columns)
    if missing:
        raise ValueError(f"Long input missing columns: {sorted(missing)}")
    if set(long["day_type"].unique()) != set(DAY_TYPES):
        raise ValueError("Unexpected day_type domain")
    if set(long["direction"].unique()) != set(DIRECTIONS):
        raise ValueError("Unexpected direction domain")
    if set(long["hour_bin"].astype(int).unique()) != set(HOURS):
        raise ValueError("Unexpected hour_bin domain")
    if long["count"].isna().any() or (long["count"] < 0).any():
        raise ValueError("Counts contain missing or negative values")


def prepare_counts() -> tuple[dict[str, pd.DataFrame], dict[str, np.ndarray], pd.DataFrame, pd.DataFrame]:
    long = pd.read_parquet(LONG_INPUT)
    validate_long(long)
    long = long.copy()
    long["lsoa"] = long["lsoa"].astype(str)
    long["hour_bin"] = long["hour_bin"].astype(int)

    reference = pd.read_parquet(REFERENCE_X)
    keep = pd.Index(reference.index.astype(str), name="lsoa")
    if len(keep) != 3593 or keep.has_duplicates:
        raise ValueError(f"Expected 3,593 unique reference LSOAs, got {len(keep)}")

    full_totals = long.groupby("lsoa", observed=True)["count"].sum()
    exceptions = set(pd.read_csv(EXCEPTION_INPUT)["lsoa"].astype(str))
    recomputed = pd.Index(
        sorted(set(full_totals.index[full_totals >= MIN_TOTAL].astype(str)).difference(exceptions)),
        name="lsoa",
    )
    if set(keep) != set(recomputed):
        raise ValueError("Reference sample does not match min-total and exception logic")

    grouped = (
        long.groupby(["lsoa", "day_type", "direction", "hour_bin"], as_index=False, observed=True)["count"]
        .sum()
    )
    counts: dict[str, pd.DataFrame] = {}
    priors: dict[str, np.ndarray] = {}
    meta = pd.DataFrame(index=keep)
    for direction in DIRECTIONS:
        parts = []
        for day_type in DAY_TYPES:
            sub = grouped[(grouped["direction"] == direction) & (grouped["day_type"] == day_type)]
            wide = sub.pivot_table(
                index="lsoa", columns="hour_bin", values="count", aggfunc="sum", fill_value=0.0
            )
            wide = wide.reindex(index=keep, columns=HOURS, fill_value=0.0).astype(float)
            wide.columns = pd.MultiIndex.from_product([[day_type], HOURS])
            parts.append(wide)
        block = pd.concat(parts, axis=1)
        block.columns = [f"{direction}_{day}_{int(hour)}" for day, hour in block.columns]
        total = block.sum(axis=1)
        if (total <= 0).any():
            raise ValueError(f"Retained sample contains non-positive {direction} total")
        prior = block.sum(axis=0).to_numpy(dtype=float)
        prior = prior / prior.sum()
        counts[direction] = block
        priors[direction] = prior
        meta[f"tot_{direction}"] = total
    meta["total_activity"] = meta[["tot_boardings", "tot_alightings"]].sum(axis=1)

    raw = long[long["lsoa"].isin(keep)].copy()
    metrics = build_raw_metrics(raw, keep)
    return counts, priors, meta, metrics


def build_raw_metrics(raw: pd.DataFrame, keep: pd.Index) -> pd.DataFrame:
    total = raw.groupby("lsoa", observed=True)["count"].sum().reindex(keep)
    direction = (
        raw.groupby(["lsoa", "direction"], observed=True)["count"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(index=keep, columns=DIRECTIONS, fill_value=0.0)
    )
    post_midnight = (
        raw.loc[raw["hour_bin"].between(1440, 1799)]
        .groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    )
    deep_night = (
        raw.loc[raw["hour_bin"].between(1620, 1799)]
        .groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    )
    evening = (
        raw.loc[raw["hour_bin"].between(1080, 1259)]
        .groupby("lsoa", observed=True)["count"].sum().reindex(keep, fill_value=0.0)
    )
    day_total = (
        raw.groupby(["lsoa", "day_type"], observed=True)["count"]
        .sum().unstack(fill_value=0.0)
        .reindex(index=keep, columns=DAY_TYPES, fill_value=0.0)
    )
    result = pd.DataFrame(index=keep)
    result["total_activity"] = total
    result["log_total_activity"] = np.log1p(total)
    result["direction_balance"] = (direction["boardings"] - direction["alightings"]) / total
    result["post_midnight_share"] = post_midnight / total
    result["deep_night_share"] = deep_night / total
    result["post_midnight_persistence"] = post_midnight / evening.replace(0.0, np.nan)
    result["weekend_ratio"] = day_total[["Saturday", "Sunday"]].mean(axis=1) / day_total[
        "Weekday"
    ].replace(0.0, np.nan)
    result["activity_band"] = np.where(total < LOW_ACTIVITY_THRESHOLD, "below_450", "at_least_450")
    if not np.isfinite(result.drop(columns="activity_band").to_numpy(dtype=float)).all():
        raise ValueError("Raw metrics contain non-finite values")
    return result


def features_for_alpha(
    counts: dict[str, pd.DataFrame], priors: dict[str, np.ndarray], alpha: float
) -> pd.DataFrame:
    blocks = []
    for direction in DIRECTIONS:
        block = counts[direction]
        totals = block.sum(axis=1).to_numpy(dtype=float)
        posterior = (block.to_numpy(dtype=float) + alpha * priors[direction]) / (totals[:, None] + alpha)
        blocks.append(pd.DataFrame(posterior, index=block.index, columns=block.columns))
    features = pd.concat(blocks, axis=1)
    if features.shape != (3593, 72):
        raise ValueError(f"Unexpected feature shape: {features.shape}")
    if not np.isfinite(features.to_numpy()).all():
        raise ValueError("Features contain non-finite values")
    if not np.allclose(features.sum(axis=1), 2.0, atol=1e-10):
        raise ValueError("Direction-normalised feature rows do not sum to two")
    return features


def fit_model(X: np.ndarray, args: argparse.Namespace) -> tuple[GaussianMixture, float]:
    started = time.perf_counter()
    model = GaussianMixture(
        n_components=args.k,
        covariance_type=args.covariance,
        n_init=args.n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=args.seed,
    ).fit(X)
    return model, time.perf_counter() - started


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = y.mean()
    total = np.square(y - grand).sum()
    between = sum(
        int((labels == cluster).sum()) * (y[labels == cluster].mean() - grand) ** 2
        for cluster in np.unique(labels)
    )
    return float(between / total) if total > 0 else float("nan")


def kw_epsilon_squared(values: pd.Series, labels: np.ndarray) -> tuple[float, float, float]:
    groups = [values.to_numpy(dtype=float)[labels == cluster] for cluster in np.unique(labels)]
    result = stats.kruskal(*groups)
    n = sum(len(group) for group in groups)
    k = len(groups)
    epsilon = (float(result.statistic) - k + 1) / (n - k)
    return float(result.statistic), float(result.pvalue), float(epsilon)


def align_to_reference(candidate: np.ndarray, reference: np.ndarray, k: int) -> tuple[np.ndarray, dict[int, int]]:
    contingency = pd.crosstab(
        pd.Series(candidate, name="candidate"), pd.Series(reference, name="reference")
    ).reindex(index=range(k), columns=range(k), fill_value=0)
    rows, cols = linear_sum_assignment(-contingency.to_numpy())
    mapping = {int(row): int(col) for row, col in zip(rows, cols)}
    return np.array([mapping[int(label)] for label in candidate], dtype=int), mapping


def reliability_summary(meta: pd.DataFrame, alpha: float) -> dict[str, float]:
    board = meta["tot_boardings"] / (meta["tot_boardings"] + alpha)
    alight = meta["tot_alightings"] / (meta["tot_alightings"] + alpha)
    minimum = np.minimum(board, alight)
    return {
        "median_min_direction_reliability": float(np.median(minimum)),
        "p10_min_direction_reliability": float(np.quantile(minimum, 0.10)),
        "median_weaker_direction_prior_weight": float(1.0 - np.median(minimum)),
        "pct_min_direction_reliability_lt_0_5": float(100.0 * np.mean(minimum < 0.5)),
        "pct_min_direction_reliability_lt_0_8": float(100.0 * np.mean(minimum < 0.8)),
    }


def resample_counts(
    rng: np.random.Generator, counts: dict[str, pd.DataFrame]
) -> dict[str, np.ndarray]:
    sampled: dict[str, np.ndarray] = {}
    for direction in DIRECTIONS:
        block = counts[direction].to_numpy(dtype=float)
        totals = block.sum(axis=1)
        integer_totals = np.maximum(1, np.rint(totals).astype(int))
        probabilities = block / totals[:, None]
        probabilities = probabilities / probabilities.sum(axis=1, keepdims=True)
        sampled[direction] = np.vstack(
            [rng.multinomial(int(n), probability) for n, probability in zip(integer_totals, probabilities)]
        ).astype(float)
    return sampled


def features_from_resample(
    sampled: dict[str, np.ndarray], priors: dict[str, np.ndarray], alpha: float
) -> np.ndarray:
    blocks = []
    for direction in DIRECTIONS:
        block = sampled[direction]
        totals = block.sum(axis=1)
        blocks.append((block + alpha * priors[direction]) / (totals[:, None] + alpha))
    return np.concatenate(blocks, axis=1)


def input_manifest() -> pd.DataFrame:
    rows = []
    for role, path in [
        ("hub_first_long_counts", LONG_INPUT),
        ("one_direction_exception_register", EXCEPTION_INPUT),
        ("reference_alpha5_features", REFERENCE_X),
        ("reference_alpha5_labels", REFERENCE_ALPHA5_LABELS),
        ("reference_alpha0_labels", REFERENCE_ALPHA0_LABELS),
        ("reference_alpha5_meta", REFERENCE_META),
    ]:
        rows.append(
            {
                "role": role,
                "path": str(path.resolve()),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else np.nan,
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    return pd.DataFrame(rows)


def plot_tradeoffs(summary: pd.DataFrame) -> None:
    labels = [f"{alpha:g}" for alpha in summary["alpha"]]
    x = np.arange(len(summary))
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)

    axes[0, 0].plot(x, summary["kw_epsilon2_log_total_activity"], marker="o", label="KW epsilon2 activity")
    axes[0, 0].plot(x, summary["eta2_log_total_activity"], marker="s", label="ANOVA eta2 activity")
    axes[0, 0].set_ylabel("Effect size")
    axes[0, 0].legend()

    axes[0, 1].plot(x, summary["timing_mean_eta2"], marker="o", color="#2A7F62")
    axes[0, 1].set_ylabel("Mean timing eta2")

    axes[1, 0].plot(x, summary["resample_below450_ari_mean"], marker="o", color="#7C4D9E")
    axes[1, 0].set_ylabel("Below-450 replicate ARI")

    axes[1, 1].plot(x, 100 * summary["median_weaker_direction_prior_weight"], marker="o", label="Median prior weight")
    axes[1, 1].plot(x, summary["pct_min_direction_reliability_lt_0_5"], marker="s", label="Prior-dominated LSOAs")
    axes[1, 1].set_ylabel("Percent")
    axes[1, 1].legend()

    for ax in axes.ravel():
        ax.set_xticks(x, labels)
        ax.set_xlabel("alpha")
        ax.grid(alpha=0.25)
    fig.suptitle("Hub-first bus K=3 alpha-grid screening trade-offs")
    fig.savefig(FIGURES / "alpha_grid_tradeoffs.png", dpi=200)
    plt.close(fig)


def format_alpha(alpha: float) -> str:
    return str(int(alpha)) if float(alpha).is_integer() else str(alpha)


def write_report(
    args: argparse.Namespace,
    summary: pd.DataFrame,
    reproduction: dict[str, float | bool],
    started_iso: str,
    elapsed: float,
) -> None:
    display_columns = [
        "alpha",
        "kw_epsilon2_log_total_activity",
        "eta2_log_total_activity",
        "timing_mean_eta2",
        "timing_retention_vs_alpha5",
        "resample_below450_ari_mean",
        "resample_below450_ari_gain_vs_alpha5",
        "min_cluster_share",
        "median_weaker_direction_prior_weight",
        "pct_min_direction_reliability_lt_0_5",
        "ari_vs_alpha5",
        "strict_screen_pass",
    ]
    candidates = summary.loc[summary["strict_screen_pass"], "alpha"].tolist()
    candidate_text = ", ".join(format_alpha(alpha) for alpha in candidates) if candidates else "None"
    command = (
        "py -3 src\\run_alpha_grid_screen.py --alphas "
        + " ".join(format_alpha(alpha) for alpha in args.alphas)
        + f" --k {args.k} --covariance {args.covariance} --n-init {args.n_init}"
        + f" --seed {args.seed} --replicates {args.replicates}"
    )
    report = f"""## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Origin Date: {datetime.now(timezone.utc).isoformat()}
- Verification Status: ANALYZED
- Version Label: hub_first_alpha_grid_screen_v1

# Hub-first bus K=3 alpha-grid screen

## Experiment Result

- **ID**: hub_first_bus_alpha_grid_2026-07-20
- **Type**: analysis / conditional multinomial resampling
- **Status**: completed
- **Command**: `{command}`
- **Working Directory**: `{ROOT}`
- **Started**: {started_iso}
- **Duration**: {elapsed:.1f} seconds
- **Rows**: 3,593 LSOAs
- **Fixed model**: K={args.k}, covariance={args.covariance}, n_init={args.n_init}, seed={args.seed}

## Reproduction gates

- Rebuilt alpha=5 features max absolute difference from saved reference: {reproduction['alpha5_feature_max_abs_diff']:.3e}
- Rebuilt alpha=5 labels ARI versus saved reference: {reproduction['alpha5_label_ari']:.6f}
- Rebuilt alpha=0 labels ARI versus saved reference: {reproduction['alpha0_label_ari']:.6f}
- Exact reference sample reproduced: {reproduction['sample_exact']}

## Screening results

{summary[display_columns].to_markdown(index=False)}

Strict screen candidates: **{candidate_text}**

This is a screening result, not automatic adoption. A passing alpha may enter
a separate full K/covariance and model-bootstrap analysis. Absolute BIC values
must not be compared across alpha-transformed feature matrices.

## Pre-declared screen gates

An alpha passes only if all conditions hold:

1. activity KW epsilon-squared is at least 20% below alpha=5;
2. activity ANOVA eta-squared is below the mean eta-squared of the three timing metrics;
3. mean timing eta-squared retains at least 85% of alpha=5;
4. below-450 conditional-resampling ARI improves by at least 0.05 over alpha=5;
5. every cluster contains at least 5% of LSOAs;
6. no more than 25% of LSOAs are prior-dominated in their weaker direction
   (direction reliability below 0.5).

## Resampling interpretation

For each replicate, two independent 36-cell multinomial profiles were drawn
conditional on each LSOA's rounded observed direction total and raw direction
shares. The already fitted alpha-specific GMM then classified both profiles.
The same random count-resamples were used for every alpha. This isolates
count-driven classification repeatability; it does not include GMM refitting
uncertainty.

## Warnings and limitations

- Hub-allocation counts are fractional. Multinomial sample sizes therefore use
  rounded direction totals; the diagnostic is an approximation.
- The resampling distribution is conditional on observed shares and assumes
  multinomial variation. It does not model extra-Poisson variation, week-to-week
  change, or spatial dependence.
- Stronger alpha can mechanically move low-count profiles toward the global
  prior. Lower activity association alone is not evidence of recovered local
  information.
- The below-450 subgroup is a diagnostic band, not a transferred final cutoff.
- GMM maximum posterior is model-internal certainty and is not a count-reliability
  measure.

## Fallacy scan

- **Coverage**: 11/11 statistical fallacy types checked.

| Fallacy | Status | Current relevance |
|---|---|---|
| Simpson's paradox | NOTE | Overall and below/above-450 stability are both reported. |
| Ecological fallacy | CAUTION | LSOA labels cannot be interpreted as individual passenger behaviour. |
| Berkson/selection bias | CAUTION | The fixed sample excludes below-50 and one-direction-zero cases. |
| Collider bias | NOTE | No covariate adjustment is used in this screen. |
| Base-rate neglect | NOTE | Not a diagnostic-classification accuracy study. |
| Regression to the mean | NOTE | No extreme-group pre/post claim is made. |
| Survivorship bias | CAUTION | Exclusion rules and retained n are explicit. |
| Look-elsewhere effect | CAUTION | Six alphas are screened; gates were fixed before inspecting results. |
| Garden of forking paths | CAUTION | Fixed factors and gates are recorded in README and this report. |
| Correlation versus causation | CAUTION | Effect sizes quantify association, not causal dominance. |
| Reverse causality | NOTE | No directional causal claim is made. |
"""
    (REPORT / "ALPHA_GRID_SCREEN.md").write_text(report, encoding="utf-8")


def main() -> None:
    args = parse_args()
    started = time.time()
    started_iso = datetime.now(timezone.utc).isoformat()
    log("[1/7] Recording inputs and rebuilding the exact fixed sample")
    manifest = input_manifest()
    if not manifest["exists"].all():
        missing = manifest.loc[~manifest["exists"], "path"].tolist()
        raise FileNotFoundError(f"Missing inputs: {missing}")
    manifest.to_csv(OUT / "input_manifest.csv", index=False)
    counts, priors, meta, metrics = prepare_counts()
    metrics.reset_index().to_csv(DATA / "hub_first_raw_metrics.csv", index=False)

    log("[2/7] Fitting fixed K=3 GMMs across alpha grid")
    models: dict[float, GaussianMixture] = {}
    features: dict[float, pd.DataFrame] = {}
    labels: dict[float, np.ndarray] = {}
    probabilities: dict[float, np.ndarray] = {}
    summary_rows = []
    effect_rows = []

    for alpha in args.alphas:
        alpha = float(alpha)
        X = features_for_alpha(counts, priors, alpha)
        model, fit_seconds = fit_model(X.to_numpy(dtype=float), args)
        label = model.predict(X)
        posterior = model.predict_proba(X)
        models[alpha] = model
        features[alpha] = X
        labels[alpha] = label
        probabilities[alpha] = posterior

        H, p_value, epsilon = kw_epsilon_squared(metrics["log_total_activity"], label)
        metric_effects = {
            metric: eta_squared(metrics[metric], label)
            for metric in [
                "log_total_activity",
                "direction_balance",
                "post_midnight_share",
                "deep_night_share",
                "post_midnight_persistence",
                "weekend_ratio",
            ]
        }
        timing_mean = float(np.mean([metric_effects[metric] for metric in TIMING_METRICS]))
        sizes = np.bincount(label, minlength=args.k)
        entropy_terms = np.zeros_like(posterior)
        np.log(posterior, out=entropy_terms, where=posterior > 0)
        normalized_entropy = -(posterior * entropy_terms).sum(axis=1) / math.log(args.k)
        row = {
            "alpha": alpha,
            "n_lsoa": len(X),
            "fit_seconds": fit_seconds,
            "converged": bool(model.converged_),
            "n_iter": int(model.n_iter_),
            "silhouette": float(silhouette_score(X, label)),
            "min_cluster_n": int(sizes.min()),
            "min_cluster_share": float(sizes.min() / len(label)),
            "median_max_posterior": float(np.median(posterior.max(axis=1))),
            "median_normalized_entropy": float(np.median(normalized_entropy)),
            "kw_H_log_total_activity": H,
            "kw_p_log_total_activity": p_value,
            "kw_epsilon2_log_total_activity": epsilon,
            "eta2_log_total_activity": metric_effects["log_total_activity"],
            "eta2_direction_balance": metric_effects["direction_balance"],
            "eta2_post_midnight_share": metric_effects["post_midnight_share"],
            "eta2_deep_night_share": metric_effects["deep_night_share"],
            "eta2_post_midnight_persistence": metric_effects["post_midnight_persistence"],
            "eta2_weekend_ratio": metric_effects["weekend_ratio"],
            "timing_mean_eta2": timing_mean,
            **reliability_summary(meta, alpha),
        }
        summary_rows.append(row)
        for metric, value in metric_effects.items():
            effect_rows.append({"alpha": alpha, "metric": metric, "eta2": value})
        log(
            f"      alpha={alpha:g}: epsilon2_activity={epsilon:.3f}, "
            f"activity_eta2={metric_effects['log_total_activity']:.3f}, "
            f"timing_mean_eta2={timing_mean:.3f}, sizes={sizes.tolist()}"
        )

    summary = pd.DataFrame(summary_rows)
    pd.DataFrame(effect_rows).to_csv(DATA / "alpha_metric_effects_long.csv", index=False)

    log("[3/7] Reproducing saved alpha=0/5 features and labels")
    ref_X = pd.read_parquet(REFERENCE_X).reindex(index=features[5.0].index, columns=features[5.0].columns)
    feature_diff = float(np.max(np.abs(ref_X.to_numpy() - features[5.0].to_numpy())))
    ref5 = pd.read_csv(REFERENCE_ALPHA5_LABELS).set_index("unit")["cluster"]
    ref5.index = ref5.index.astype(str)
    ref5_values = ref5.reindex(features[5.0].index).to_numpy(dtype=int)
    ref0 = pd.read_csv(REFERENCE_ALPHA0_LABELS).set_index("unit")["cluster"]
    ref0.index = ref0.index.astype(str)
    ref0_values = ref0.reindex(features[0.0].index).to_numpy(dtype=int)
    reproduction = {
        "sample_exact": bool(features[5.0].index.equals(ref_X.index)),
        "alpha5_feature_max_abs_diff": feature_diff,
        "alpha5_label_ari": float(adjusted_rand_score(ref5_values, labels[5.0])),
        "alpha0_label_ari": float(adjusted_rand_score(ref0_values, labels[0.0])),
    }
    if feature_diff > 1e-12 or reproduction["alpha5_label_ari"] < 1.0 - 1e-12 or reproduction["alpha0_label_ari"] < 1.0 - 1e-12:
        raise ValueError(f"Reference reproduction failed: {reproduction}")

    log("[4/7] Aligning labels and writing label/profile diagnostics")
    assignment_parts = []
    profile_rows = []
    metric_profile_rows = []
    transition_rows = []
    base_labels = labels[5.0]
    for alpha in args.alphas:
        alpha = float(alpha)
        aligned, mapping = align_to_reference(labels[alpha], base_labels, args.k)
        summary.loc[summary["alpha"] == alpha, "ari_vs_alpha5"] = adjusted_rand_score(base_labels, labels[alpha])
        minimum_reliability = np.minimum(
            meta["tot_boardings"] / (meta["tot_boardings"] + alpha),
            meta["tot_alightings"] / (meta["tot_alightings"] + alpha),
        )
        posterior = probabilities[alpha]
        entropy_terms = np.zeros_like(posterior)
        np.log(posterior, out=entropy_terms, where=posterior > 0)
        normalized_entropy = -(posterior * entropy_terms).sum(axis=1) / math.log(args.k)
        assignment_parts.append(
            pd.DataFrame(
                {
                    "lsoa": features[alpha].index,
                    "alpha": alpha,
                    "cluster_raw": labels[alpha],
                    "cluster_aligned_to_alpha5": aligned,
                    "max_posterior": posterior.max(axis=1),
                    "normalized_entropy": normalized_entropy,
                    "total_activity": metrics["total_activity"].to_numpy(),
                    "activity_band": metrics["activity_band"].to_numpy(),
                    "min_direction_reliability": minimum_reliability.to_numpy(),
                }
            )
        )
        contingency = pd.crosstab(
            pd.Series(base_labels, name="alpha5_cluster"),
            pd.Series(aligned, name="candidate_cluster"),
        ).reindex(index=range(args.k), columns=range(args.k), fill_value=0)
        for base_cluster in range(args.k):
            for candidate_cluster in range(args.k):
                transition_rows.append(
                    {
                        "alpha": alpha,
                        "alpha5_cluster": base_cluster,
                        "candidate_cluster_aligned": candidate_cluster,
                        "n": int(contingency.loc[base_cluster, candidate_cluster]),
                    }
                )
        X = features[alpha]
        for aligned_cluster in range(args.k):
            mask = aligned == aligned_cluster
            for feature, value in X.loc[mask].mean(axis=0).items():
                stem, hour = feature.rsplit("_", 1)
                direction, day_type = stem.split("_", 1)
                profile_rows.append(
                    {
                        "alpha": alpha,
                        "cluster_aligned_to_alpha5": aligned_cluster,
                        "direction": direction,
                        "day_type": day_type,
                        "hour_bin": int(hour),
                        "mean_share": float(value),
                    }
                )
            for metric in [
                "total_activity",
                "direction_balance",
                "post_midnight_share",
                "deep_night_share",
                "post_midnight_persistence",
                "weekend_ratio",
            ]:
                values = metrics.loc[mask, metric]
                metric_profile_rows.append(
                    {
                        "alpha": alpha,
                        "cluster_aligned_to_alpha5": aligned_cluster,
                        "metric": metric,
                        "mean": float(values.mean()),
                        "median": float(values.median()),
                        "p10": float(values.quantile(0.10)),
                        "p90": float(values.quantile(0.90)),
                    }
                )

    pd.concat(assignment_parts, ignore_index=True).to_csv(DATA / "alpha_label_assignments.csv", index=False)
    pd.DataFrame(profile_rows).to_csv(DATA / "alpha_temporal_profiles.csv", index=False)
    pd.DataFrame(metric_profile_rows).to_csv(DATA / "alpha_cluster_metric_profiles.csv", index=False)
    pd.DataFrame(transition_rows).to_csv(DATA / "alpha_transitions_vs_alpha5.csv", index=False)

    log("[5/7] Running shared conditional multinomial count-resamples")
    rng = np.random.default_rng(args.seed + 20260720)
    resample_rows = []
    low_mask = metrics["total_activity"].to_numpy() < LOW_ACTIVITY_THRESHOLD
    high_mask = ~low_mask
    for replicate in range(args.replicates):
        sample_a = resample_counts(rng, counts)
        sample_b = resample_counts(rng, counts)
        for alpha in args.alphas:
            alpha = float(alpha)
            prediction_a = models[alpha].predict(features_from_resample(sample_a, priors, alpha))
            prediction_b = models[alpha].predict(features_from_resample(sample_b, priors, alpha))
            resample_rows.append(
                {
                    "replicate": replicate,
                    "alpha": alpha,
                    "ari_all": adjusted_rand_score(prediction_a, prediction_b),
                    "ari_below450": adjusted_rand_score(prediction_a[low_mask], prediction_b[low_mask]),
                    "ari_at_least450": adjusted_rand_score(prediction_a[high_mask], prediction_b[high_mask]),
                    "ari_base_vs_a_all": adjusted_rand_score(labels[alpha], prediction_a),
                    "ari_base_vs_a_below450": adjusted_rand_score(labels[alpha][low_mask], prediction_a[low_mask]),
                    "ari_base_vs_a_at_least450": adjusted_rand_score(labels[alpha][high_mask], prediction_a[high_mask]),
                }
            )
        log(f"      replicate {replicate + 1}/{args.replicates}")
    resamples = pd.DataFrame(resample_rows)
    resamples.to_csv(DIAGNOSTICS / "conditional_multinomial_resamples.csv", index=False)
    resample_summary = (
        resamples.groupby("alpha", as_index=False)
        .agg(
            resample_all_ari_mean=("ari_all", "mean"),
            resample_all_ari_sd=("ari_all", "std"),
            resample_below450_ari_mean=("ari_below450", "mean"),
            resample_below450_ari_sd=("ari_below450", "std"),
            resample_at_least450_ari_mean=("ari_at_least450", "mean"),
            resample_at_least450_ari_sd=("ari_at_least450", "std"),
            resample_base_vs_a_below450_mean=("ari_base_vs_a_below450", "mean"),
            resample_base_vs_a_at_least450_mean=("ari_base_vs_a_at_least450", "mean"),
        )
    )
    resample_summary.to_csv(DIAGNOSTICS / "conditional_multinomial_resample_summary.csv", index=False)
    summary = summary.merge(resample_summary, on="alpha", validate="one_to_one")

    log("[6/7] Applying pre-declared screening gates")
    baseline = summary.loc[summary["alpha"] == 5.0].iloc[0]
    summary["activity_epsilon2_reduction_vs_alpha5"] = (
        baseline["kw_epsilon2_log_total_activity"] - summary["kw_epsilon2_log_total_activity"]
    ) / baseline["kw_epsilon2_log_total_activity"]
    summary["timing_retention_vs_alpha5"] = summary["timing_mean_eta2"] / baseline["timing_mean_eta2"]
    summary["resample_below450_ari_gain_vs_alpha5"] = (
        summary["resample_below450_ari_mean"] - baseline["resample_below450_ari_mean"]
    )
    summary["gate_activity_epsilon2"] = summary["activity_epsilon2_reduction_vs_alpha5"] >= 0.20
    summary["gate_activity_below_timing"] = summary["eta2_log_total_activity"] < summary["timing_mean_eta2"]
    summary["gate_timing_retention"] = summary["timing_retention_vs_alpha5"] >= 0.85
    summary["gate_low_activity_repeatability"] = summary["resample_below450_ari_gain_vs_alpha5"] >= 0.05
    summary["gate_cluster_size"] = summary["min_cluster_share"] >= 0.05
    summary["gate_prior_dominance"] = summary["pct_min_direction_reliability_lt_0_5"] <= 25.0
    gate_columns = [
        "gate_activity_epsilon2",
        "gate_activity_below_timing",
        "gate_timing_retention",
        "gate_low_activity_repeatability",
        "gate_cluster_size",
        "gate_prior_dominance",
    ]
    summary["strict_screen_pass"] = summary[gate_columns].all(axis=1)
    summary.to_csv(DATA / "alpha_screen_summary.csv", index=False)
    plot_tradeoffs(summary)

    log("[7/7] Writing run environment and analytical report")
    elapsed = time.time() - started
    run_environment = {
        "command": "py -3 src\\run_alpha_grid_screen.py --alphas 0 5 20 50 100 200 --k 3 --covariance full --n-init 20 --seed 42 --replicates 20",
        "started_utc": started_iso,
        "elapsed_seconds": elapsed,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "seed": args.seed,
        "fixed_k": args.k,
        "covariance": args.covariance,
        "n_init": args.n_init,
        "replicates": args.replicates,
        "reg_covar": REG_COVAR,
        "max_iter": MAX_ITER,
    }
    (OUT / "run_environment.json").write_text(json.dumps(run_environment, indent=2), encoding="utf-8")
    write_report(args, summary, reproduction, started_iso, elapsed)
    log(f"Completed in {elapsed:.1f}s")
    log(str(REPORT / "ALPHA_GRID_SCREEN.md"))


if __name__ == "__main__":
    main()
