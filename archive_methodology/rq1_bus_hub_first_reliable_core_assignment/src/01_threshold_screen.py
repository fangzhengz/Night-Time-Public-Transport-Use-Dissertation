"""Stage-1 weaker-direction threshold screen for hub-first bus clustering.

v2: no longer requires a fixed K list to pass simultaneously, and does not
force K=3. The original K=3 result was produced by a pipeline this project
has since found to be activity-noise-contaminated (see
rq1_bus_activity_tiered_reclustering and rq1_bus_hub_first_alpha_grid_screen),
so repeated past agreement on K=3 is not independent evidence that K=3 is
still correct once the low-count noise is actually suppressed by exclusion.

For each threshold this script instead lets BIC pick that threshold's own
preferred K from an exploratory scan, confirms the winning K (and K=3, kept
only as a labelled reference point, never as a requirement) at full n_init,
and gates only on whether activity dominance is resolved at the threshold's
own BIC-preferred K.

This script deliberately varies only the core eligibility threshold. It keeps
the hub-first LSOA sample, alpha=0 features, GMM covariance, feature definition,
and random seed fixed. It does not perform posterior assignment of
low-information LSOAs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy import stats
from sklearn.mixture import GaussianMixture


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent

X_INPUT = (
    FYP
    / "rq1_bus_hub_first_reclustering_alpha_sensitivity"
    / "outputs"
    / "features"
    / "X_bus_fullweek_alpha0_fixed_sample.parquet"
)
META_INPUT = (
    FYP
    / "rq1_bus_hub_first_reclustering"
    / "outputs"
    / "features"
    / "bus_fullweek_meta_alpha5.csv"
)
METRICS_INPUT = (
    FYP
    / "rq1_bus_hub_first_alpha_grid_screen"
    / "outputs"
    / "data"
    / "hub_first_raw_metrics.csv"
)

OUT = ROOT / "outputs"
DATA = OUT / "data"
DIAGNOSTICS = OUT / "diagnostics"
REPORT = OUT / "report"
for directory in (DATA, DIAGNOSTICS, REPORT):
    directory.mkdir(parents=True, exist_ok=True)

TIMING_METRICS = [
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
]
EXPECTED_N = 3593
EXPECTED_D = 72
REG_COVAR = 1e-6
MAX_ITER = 300
REFERENCE_K = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=float,
        default=[0, 50, 70, 90, 100, 110, 125, 150],
    )
    parser.add_argument("--k-scan-min", type=int, default=2)
    parser.add_argument("--k-scan-max", type=int, default=10)
    parser.add_argument("--scan-n-init", type=int, default=5)
    parser.add_argument("--deepdive-n-init", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tag", default="first_pass")
    args = parser.parse_args()
    args.thresholds = sorted(set(float(value) for value in args.thresholds))
    if any(value < 0 for value in args.thresholds):
        parser.error("thresholds must be non-negative")
    if args.k_scan_min < 2 or args.k_scan_max < args.k_scan_min:
        parser.error("k-scan-max must be >= k-scan-min >= 2")
    if args.scan_n_init < 1 or args.deepdive_n_init < 1:
        parser.error("n-init values must be positive")
    if not args.tag.replace("_", "").replace("-", "").isalnum():
        parser.error("tag may contain only letters, numbers, hyphens and underscores")
    return args


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def input_manifest(tag: str) -> pd.DataFrame:
    rows = []
    for role, path in (
        ("alpha0_features", X_INPUT),
        ("hub_first_direction_totals", META_INPUT),
        ("hub_first_raw_metrics", METRICS_INPUT),
    ):
        stat = path.stat()
        rows.append(
            {
                "role": role,
                "path": str(path.resolve()),
                "size_bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
                "sha256": sha256(path),
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(DATA / f"input_manifest_{tag}.csv", index=False)
    return manifest


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = [path for path in (X_INPUT, META_INPUT, METRICS_INPUT) if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")

    X = pd.read_parquet(X_INPUT)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    if X.shape != (EXPECTED_N, EXPECTED_D):
        raise ValueError(f"Expected feature shape {(EXPECTED_N, EXPECTED_D)}, got {X.shape}")
    if X.index.has_duplicates:
        raise ValueError("Feature index contains duplicate LSOAs")
    Xv = X.to_numpy(dtype=float)
    if not np.isfinite(Xv).all():
        raise ValueError("Features contain non-finite values")
    if not np.allclose(Xv.sum(axis=1), 2.0, atol=1e-10):
        raise ValueError("Direction-normalized feature rows do not sum to two")

    meta = pd.read_csv(META_INPUT)
    meta["lsoa"] = meta["lsoa"].astype(str)
    meta = meta.set_index("lsoa").reindex(X.index)
    required_meta = ["total_activity", "tot_boardings", "tot_alightings"]
    if meta[required_meta].isna().any().any():
        raise ValueError("Direction-total metadata are missing for retained LSOAs")
    meta["min_direction_activity"] = meta[["tot_boardings", "tot_alightings"]].min(axis=1)

    metrics = pd.read_csv(METRICS_INPUT)
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    metrics = metrics.set_index("lsoa").reindex(X.index)
    required_metrics = [
        "total_activity",
        "log_total_activity",
        "direction_balance",
        *TIMING_METRICS,
        "weekend_ratio",
    ]
    if metrics[required_metrics].isna().any().any():
        raise ValueError("Raw metrics are missing for retained LSOAs")
    total_diff = np.abs(
        meta["total_activity"].to_numpy(dtype=float)
        - metrics["total_activity"].to_numpy(dtype=float)
    )
    if float(total_diff.max()) > 1e-8:
        raise ValueError(f"Metadata/raw-metric total mismatch: max diff={total_diff.max()}")

    analysis = metrics[required_metrics].copy()
    analysis["tot_boardings"] = meta["tot_boardings"]
    analysis["tot_alightings"] = meta["tot_alightings"]
    analysis["min_direction_activity"] = meta["min_direction_activity"]
    return X, analysis


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


def kw_epsilon_squared(values: pd.Series, labels: np.ndarray) -> tuple[float, float, float]:
    groups = [
        values.to_numpy(dtype=float)[labels == cluster]
        for cluster in np.unique(labels)
    ]
    result = stats.kruskal(*groups)
    n = sum(len(group) for group in groups)
    k = len(groups)
    epsilon = (float(result.statistic) - k + 1) / (n - k)
    return float(result.statistic), float(result.pvalue), float(epsilon)


def fit_one(
    X: np.ndarray,
    metrics: pd.DataFrame,
    threshold: float,
    k: int,
    n_total: int,
    n_init: int,
    seed: int,
    stage: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    started = time.perf_counter()
    model = GaussianMixture(
        n_components=k,
        covariance_type="full",
        n_init=n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=seed,
    ).fit(X)
    fit_seconds = time.perf_counter() - started
    labels = model.predict(X)

    timing_effects = {name: eta_squared(metrics[name], labels) for name in TIMING_METRICS}
    timing_mean = float(np.mean(list(timing_effects.values())))
    activity_eta2 = eta_squared(metrics["log_total_activity"], labels)
    kw_h, kw_p, kw_epsilon2 = kw_epsilon_squared(metrics["log_total_activity"], labels)
    unique, counts = np.unique(labels, return_counts=True)
    cluster_sizes = [
        {
            "threshold": threshold,
            "stage": stage,
            "k": k,
            "cluster": int(cluster),
            "n_units": int(count),
            "pct_of_core": float(100.0 * count / len(labels)),
        }
        for cluster, count in zip(unique, counts)
    ]

    row: dict[str, object] = {
        "threshold": threshold,
        "stage": stage,
        "k": k,
        "n_core": len(labels),
        "pct_core": 100.0 * len(labels) / n_total,
        "n_excluded_from_fit": n_total - len(labels),
        "pct_excluded_from_fit": 100.0 * (n_total - len(labels)) / n_total,
        "n_init": n_init,
        "seed": seed,
        "converged": bool(model.converged_),
        "n_iter": int(model.n_iter_),
        "fit_seconds": fit_seconds,
        "lower_bound": float(model.lower_bound_),
        "bic_within_threshold": float(model.bic(X)),
        "aic_within_threshold": float(model.aic(X)),
        "min_cluster_size": int(counts.min()),
        "max_cluster_size": int(counts.max()),
        "min_cluster_pct": float(100.0 * counts.min() / len(labels)),
        "activity_eta2": activity_eta2,
        "activity_kw_h": kw_h,
        "activity_kw_p": kw_p,
        "activity_kw_epsilon2": kw_epsilon2,
        "direction_balance_eta2": eta_squared(metrics["direction_balance"], labels),
        "weekend_ratio_eta2": eta_squared(metrics["weekend_ratio"], labels),
        **{f"{name}_eta2": value for name, value in timing_effects.items()},
        "timing_mean_eta2": timing_mean,
        "activity_to_timing_ratio": (
            float(activity_eta2 / timing_mean) if timing_mean > 0 else float("inf")
        ),
        "gate_activity_below_timing": bool(activity_eta2 < timing_mean),
    }
    return row, cluster_sizes


def write_environment(args: argparse.Namespace, manifest: pd.DataFrame) -> None:
    payload = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "command": [sys.executable, *sys.argv],
        "working_directory": str(Path.cwd().resolve()),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "parameters": vars(args),
        "inputs": manifest.to_dict(orient="records"),
    }
    (REPORT / f"run_environment_{args.tag}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def build_threshold_summary(deepdive: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold, group in deepdive.groupby("threshold", sort=True):
        natural = group.loc[group["is_bic_best_k"]].iloc[0]
        reference = group.loc[group["k"] == REFERENCE_K]
        rows.append(
            {
                "threshold": float(threshold),
                "n_core": int(natural["n_core"]),
                "pct_core": float(natural["pct_core"]),
                "bic_best_k": int(natural["k"]),
                "bic_best_k_activity_eta2": float(natural["activity_eta2"]),
                "bic_best_k_timing_mean_eta2": float(natural["timing_mean_eta2"]),
                "bic_best_k_activity_to_timing_ratio": float(natural["activity_to_timing_ratio"]),
                "gate_pass_at_bic_best_k": bool(natural["gate_activity_below_timing"]),
                "bic_best_k_min_cluster_pct": float(natural["min_cluster_pct"]),
                "bic_best_k_converged": bool(natural["converged"]),
                "reference_k3_activity_eta2": (
                    float(reference["activity_eta2"].iloc[0]) if not reference.empty else float("nan")
                ),
                "reference_k3_gate_pass": (
                    bool(reference["gate_activity_below_timing"].iloc[0]) if not reference.empty else None
                ),
                "bic_best_k_differs_from_reference": int(natural["k"]) != REFERENCE_K,
            }
        )
    summary = pd.DataFrame(rows).sort_values("threshold").reset_index(drop=True)
    pass_flags = summary["gate_pass_at_bic_best_k"].to_numpy(dtype=bool)
    adjacent = np.zeros(len(summary), dtype=bool)
    if len(summary) > 1:
        adjacent[:-1] |= pass_flags[:-1] & pass_flags[1:]
        adjacent[1:] |= pass_flags[:-1] & pass_flags[1:]
    summary["part_of_consecutive_pass_run"] = adjacent
    summary["coverage_band"] = np.select(
        [summary["pct_core"] >= 75.0, summary["pct_core"] >= 70.0],
        ["preferred_at_least_75pct", "fallback_70_to_75pct"],
        default="stress_below_70pct",
    )
    summary["strict_candidate"] = (
        summary["gate_pass_at_bic_best_k"]
        & summary["part_of_consecutive_pass_run"]
        & summary["bic_best_k_converged"]
        & (summary["pct_core"] >= 75.0)
    )
    return summary


def write_report(
    args: argparse.Namespace,
    scan: pd.DataFrame,
    deepdive: pd.DataFrame,
    summary: pd.DataFrame,
    elapsed: float,
) -> None:
    strict = summary.loc[summary["strict_candidate"]]
    recommendation = (
        f"Lowest strict candidate: **{strict['threshold'].iloc[0]:g}** "
        f"(its own BIC-best K = {int(strict['bic_best_k'].iloc[0])})."
        if not strict.empty
        else "No threshold passed the strict gate at its own BIC-best K."
    )
    moved = summary.loc[summary["bic_best_k_differs_from_reference"]]
    moved_text = (
        ", ".join(
            f"threshold={row.threshold:g}->K={int(row.bic_best_k)}"
            for row in moved.itertuples()
        )
        if not moved.empty
        else f"none: every screened threshold still has BIC-best K={REFERENCE_K}"
    )
    summary_cols = [
        "threshold",
        "pct_core",
        "bic_best_k",
        "bic_best_k_differs_from_reference",
        "bic_best_k_activity_eta2",
        "bic_best_k_timing_mean_eta2",
        "gate_pass_at_bic_best_k",
        "part_of_consecutive_pass_run",
        "coverage_band",
        "strict_candidate",
        "reference_k3_activity_eta2",
        "reference_k3_gate_pass",
    ]
    scan_cols = [
        "threshold", "k", "bic_within_threshold", "activity_eta2",
        "timing_mean_eta2", "gate_activity_below_timing", "min_cluster_pct", "converged",
    ]
    deepdive_cols = [
        "threshold", "k", "is_bic_best_k", "bic_within_threshold", "activity_eta2",
        "timing_mean_eta2", "activity_to_timing_ratio", "gate_activity_below_timing",
        "min_cluster_pct", "converged", "fit_seconds",
    ]
    lines = [
        "## Material Passport",
        "",
        f"- ID: `hub-first-core-threshold-screen-{args.tag}`",
        "- Type: code experiment result",
        "- Verification status: ANALYZED",
        f"- Created UTC: {datetime.now(timezone.utc).isoformat()}",
        "- Scope: threshold screen with per-threshold BIC-driven K selection;",
        "  no forced K, no posterior assignment yet",
        "",
        "# Hub-first reliable-core threshold screen (v2: BIC picks K per threshold)",
        "",
        "## Why this version does not fix K",
        "",
        "The historical K=3 result comes from a pipeline this project has since",
        "shown to be activity-noise-contaminated. Requiring K=3 to keep winning",
        "after the contamination is removed would assume the answer. This script",
        "instead lets BIC choose each threshold's own preferred K from an",
        f"exploratory scan (K={args.k_scan_min}..{args.k_scan_max}, full covariance,",
        f"n_init={args.scan_n_init}), confirms the winning K at n_init=",
        f"{args.deepdive_n_init}, and gates on that K. K={REFERENCE_K} is refit and",
        "shown alongside purely as a labelled reference point, never as a requirement.",
        "",
        "## Fixed design",
        "",
        f"- Thresholds: {args.thresholds}",
        f"- K scan range: {args.k_scan_min}..{args.k_scan_max}",
        f"- Full-covariance GMM; scan n_init={args.scan_n_init}; "
        f"deep-dive n_init={args.deepdive_n_init}; seed={args.seed}",
        "- Core criterion: min(total_boardings, total_alightings) >= threshold",
        "- Features: fixed hub-first alpha=0 direction-normalized 72-vector",
        f"- Total elapsed seconds: {elapsed:.3f}",
        "",
        f"**BIC-best K shift away from K={REFERENCE_K}: {moved_text}.**",
        "",
        "## Threshold-level gate (own BIC-best K)",
        "",
        summary[summary_cols].to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Exploratory scan grid (all screened K, n_init={})".format(args.scan_n_init),
        "",
        "Informational only -- not gating. Low n_init means individual cells can",
        "be noisy; only the deep-dive-confirmed BIC-best K per threshold is used",
        "for the decision above.",
        "",
        scan[scan_cols].to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Deep-dive confirmatory fits (BIC-best K and K={} reference, n_init={})".format(
            REFERENCE_K, args.deepdive_n_init
        ),
        "",
        deepdive[deepdive_cols].to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Automated verdict",
        "",
        recommendation,
        "",
        "BIC values are valid for comparing K values within the same threshold",
        "and must not be used to rank different thresholds with different samples.",
    ]
    (REPORT / f"THRESHOLD_SCREEN_{args.tag.upper()}.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> None:
    args = parse_args()
    run_started = time.perf_counter()
    manifest = input_manifest(args.tag)
    X, metrics = load_inputs()
    write_environment(args, manifest)

    k_scan_range = list(range(args.k_scan_min, args.k_scan_max + 1))
    n_total = len(X)
    print(
        f"Loaded {X.shape[0]} LSOAs x {X.shape[1]} features; "
        f"thresholds={args.thresholds}; K scan={k_scan_range}; "
        f"scan_n_init={args.scan_n_init}; deepdive_n_init={args.deepdive_n_init}",
        flush=True,
    )

    scan_rows: list[dict[str, object]] = []
    scan_size_rows: list[dict[str, object]] = []
    deepdive_rows: list[dict[str, object]] = []
    deepdive_size_rows: list[dict[str, object]] = []

    for threshold in args.thresholds:
        keep = metrics["min_direction_activity"].to_numpy(dtype=float) >= threshold
        X_core = X.to_numpy(dtype=float)[keep]
        metrics_core = metrics.loc[keep].copy()
        if len(X_core) <= args.k_scan_max:
            raise ValueError(f"Threshold {threshold:g} leaves too few rows: {len(X_core)}")
        print(
            f"threshold={threshold:g}: n_core={len(X_core)} "
            f"({100.0 * len(X_core) / n_total:.1f}%) -- exploratory scan",
            flush=True,
        )
        threshold_scan = []
        for k in k_scan_range:
            row, sizes = fit_one(
                X_core, metrics_core, threshold, k, n_total, args.scan_n_init, args.seed, "scan"
            )
            threshold_scan.append(row)
            scan_rows.append(row)
            scan_size_rows.extend(sizes)
            print(
                f"  [scan] K={k}: BIC={row['bic_within_threshold']:.1f} "
                f"activity_eta2={row['activity_eta2']:.4f} "
                f"timing_mean_eta2={row['timing_mean_eta2']:.4f} "
                f"pass={row['gate_activity_below_timing']}",
                flush=True,
            )
        bic_best_k = int(min(threshold_scan, key=lambda r: r["bic_within_threshold"])["k"])
        print(f"  threshold={threshold:g}: bic_best_K={bic_best_k} -- confirmatory deep dive", flush=True)

        for k in sorted({bic_best_k, REFERENCE_K}):
            row, sizes = fit_one(
                X_core, metrics_core, threshold, k, n_total, args.deepdive_n_init, args.seed, "deepdive"
            )
            row["is_bic_best_k"] = k == bic_best_k
            deepdive_rows.append(row)
            deepdive_size_rows.extend(sizes)
            print(
                f"  [deepdive] K={k} (bic_best={row['is_bic_best_k']}): "
                f"activity_eta2={row['activity_eta2']:.4f} "
                f"timing_mean_eta2={row['timing_mean_eta2']:.4f} "
                f"pass={row['gate_activity_below_timing']}; {row['fit_seconds']:.2f}s",
                flush=True,
            )
        pd.DataFrame(scan_rows).to_csv(
            DIAGNOSTICS / f"threshold_k_screen_{args.tag}.partial.csv", index=False
        )

    scan = pd.DataFrame(scan_rows).sort_values(["threshold", "k"]).reset_index(drop=True)
    deepdive = pd.DataFrame(deepdive_rows).sort_values(["threshold", "k"]).reset_index(drop=True)
    scan_sizes = pd.DataFrame(scan_size_rows).sort_values(["threshold", "k", "cluster"])
    deepdive_sizes = pd.DataFrame(deepdive_size_rows).sort_values(["threshold", "k", "cluster"])
    summary = build_threshold_summary(deepdive)

    scan.to_csv(DATA / f"threshold_k_scan_{args.tag}.csv", index=False)
    deepdive.to_csv(DATA / f"threshold_k_deepdive_{args.tag}.csv", index=False)
    scan_sizes.to_csv(DATA / f"threshold_k_scan_cluster_sizes_{args.tag}.csv", index=False)
    deepdive_sizes.to_csv(DATA / f"threshold_k_deepdive_cluster_sizes_{args.tag}.csv", index=False)
    summary.to_csv(DATA / f"threshold_screen_summary_{args.tag}.csv", index=False)

    elapsed = time.perf_counter() - run_started
    write_report(args, scan, deepdive, summary, elapsed)
    partial = DIAGNOSTICS / f"threshold_k_screen_{args.tag}.partial.csv"
    if partial.exists():
        partial.unlink()

    print("", flush=True)
    print(summary.to_string(index=False), flush=True)
    print(f"Completed in {elapsed:.2f}s", flush=True)


if __name__ == "__main__":
    main()
