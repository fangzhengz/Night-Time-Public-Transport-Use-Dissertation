"""Direct transport-indicator × LNWC analysis for the provisional RQ2 trial.

STATUS (2026-07-14): the centrality-adjusted partial-R^2 tests in this script
(metric ~ distance + LNWC) pool ALL stations/LSOAs regardless of RQ1 cluster
membership, so they cannot say which cluster drives an observed relationship.
The user judged this disconnected from the actual RQ2 question (how does the
RQ1 *typology* relate to LNWC/socio-economic variables) and marked it
provisional / not a primary result pending a different method. A proposed
fix (add cluster as a covariate, or re-run stratified by cluster) was
considered and explicitly rejected -- do not default back to it without
new instruction. The categorical cluster x LNWC test in run_analysis.py is
unaffected by this and remains a kept, primary result.
"""

from __future__ import annotations

import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]
RQ1_CONTEXT = FYP / "rq1_context_metrics_analysis" / "outputs" / "data"
BASELINE = ROOT / "outputs" / "data"
LSOA_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"

OUT = ROOT / "outputs" / "direct_metrics"
DATA = OUT / "data"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
WORKBOOK = OUT / "workbook"
for directory in (DATA, FIGURES, REPORT, WORKBOOK):
    directory.mkdir(parents=True, exist_ok=True)

LNWC_GROUPS = list(range(1, 8))
SHARES = [f"lnwc_{group}_share" for group in LNWC_GROUPS]
BUS_PRIMARY = [
    "log_total_activity",
    "post_midnight_share",
    "direction_balance",
    "weekend_ratio",
]
RAIL_PRIMARY = [
    "log_total_activity",
    "night_tube_extension_share",
    "direction_balance",
    "weekend_common_ratio",
]
RAIL_SECONDARY = ["midnight_share_common_window"]
CENTRE_EASTING = 530134.0
CENTRE_NORTHING = 180379.0
N_PERMUTATIONS = 999
RANDOM_SEED = 42
START = time.time()


def bh_adjust(p_values: pd.Series) -> pd.Series:
    values = p_values.to_numpy(dtype=float)
    order = np.argsort(values)
    ranked = values[order]
    adjusted = ranked * len(values) / np.arange(1, len(values) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0, 1)
    return pd.Series(result, index=p_values.index)


def dunn_pairwise(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    sample = frame[["lnc_grp", metric]].dropna().copy()
    sample["rank"] = stats.rankdata(sample[metric], method="average")
    n_total = len(sample)
    ties = sample[metric].value_counts()
    tie_correction = 1 - ((ties.pow(3) - ties).sum() / (n_total**3 - n_total))
    rank_means = sample.groupby("lnc_grp")["rank"].mean()
    counts = sample.groupby("lnc_grp").size()
    base_variance = n_total * (n_total + 1) / 12 * tie_correction
    rows = []
    for i, group_i in enumerate(LNWC_GROUPS):
        for group_j in LNWC_GROUPS[i + 1 :]:
            standard_error = np.sqrt(
                base_variance * (1 / counts[group_i] + 1 / counts[group_j])
            )
            z = (rank_means[group_i] - rank_means[group_j]) / standard_error
            rows.append(
                {
                    "metric": metric,
                    "group_i": group_i,
                    "group_j": group_j,
                    "z": z,
                    "p_value": 2 * stats.norm.sf(abs(z)),
                }
            )
    result = pd.DataFrame(rows)
    result["p_fdr_bh"] = bh_adjust(result["p_value"])
    return result


def bus_group_summary(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for group, subset in frame.groupby("lnc_grp"):
        for metric in metrics:
            values = subset[metric].dropna()
            rows.append(
                {
                    "lnwc_group": int(group),
                    "metric": metric,
                    "n": len(values),
                    "median": values.median(),
                    "q25": values.quantile(0.25),
                    "q75": values.quantile(0.75),
                    "mean": values.mean(),
                }
            )
    return pd.DataFrame(rows)


def kruskal_results(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for metric in metrics:
        samples = [
            frame.loc[frame["lnc_grp"] == group, metric].dropna().to_numpy()
            for group in LNWC_GROUPS
        ]
        statistic, p_value = stats.kruskal(*samples)
        n = sum(map(len, samples))
        k = len(samples)
        epsilon_sq = max(0.0, (statistic - k + 1) / (n - k))
        rows.append(
            {
                "metric": metric,
                "kruskal_h": statistic,
                "df": k - 1,
                "p_value": p_value,
                "epsilon_squared": epsilon_sq,
                "n": n,
            }
        )
    result = pd.DataFrame(rows)
    result["p_fdr_bh"] = bh_adjust(result["p_value"])
    return result


def fit_sse(y: np.ndarray, x: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    fitted = x @ beta
    residual = y - fitted
    return float(residual @ residual), fitted, residual


def partial_model_test(
    y: np.ndarray,
    reduced: np.ndarray,
    full: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, float]:
    sse_reduced, fitted_reduced, residual_reduced = fit_sse(y, reduced)
    sse_full, _, _ = fit_sse(y, full)
    partial_r2 = max(0.0, (sse_reduced - sse_full) / sse_reduced)
    df_difference = full.shape[1] - reduced.shape[1]
    df_error = len(y) - full.shape[1]
    f_statistic = (
        ((sse_reduced - sse_full) / df_difference) / (sse_full / df_error)
        if sse_full > 0
        else np.inf
    )
    p_parametric = stats.f.sf(f_statistic, df_difference, df_error)

    exceedances = 0
    for _ in range(N_PERMUTATIONS):
        permuted_y = fitted_reduced + rng.permutation(residual_reduced)
        perm_reduced, _, _ = fit_sse(permuted_y, reduced)
        perm_full, _, _ = fit_sse(permuted_y, full)
        perm_partial = max(0.0, (perm_reduced - perm_full) / perm_reduced)
        exceedances += perm_partial >= partial_r2
    return {
        "partial_r_squared": partial_r2,
        "f_statistic": f_statistic,
        "df_difference": df_difference,
        "df_error": df_error,
        "p_parametric": p_parametric,
        "p_freedman_lane": (exceedances + 1) / (N_PERMUTATIONS + 1),
    }


def centrality_design_bus(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    distance = frame["distance_to_centre_km"].to_numpy(dtype=float)
    distance = (distance - distance.mean()) / distance.std()
    reduced = np.column_stack([np.ones(len(frame)), distance])
    dummies = pd.get_dummies(frame["lnc_grp"], dtype=float).reindex(
        columns=LNWC_GROUPS, fill_value=0
    )
    full = np.column_stack([reduced, dummies.iloc[:, :6].to_numpy()])
    return reduced, full


def centrality_design_rail(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    distance = frame["distance_to_centre_km"].to_numpy(dtype=float)
    distance = (distance - distance.mean()) / distance.std()
    reduced = np.column_stack([np.ones(len(frame)), distance])
    full = np.column_stack([reduced, frame[SHARES[:6]].to_numpy(dtype=float)])
    return reduced, full


def centrality_tests(
    frame: pd.DataFrame,
    metrics: list[str],
    mode: str,
) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    rows = []
    for metric in metrics:
        sample = frame.dropna(subset=[metric, "distance_to_centre_km"]).copy()
        reduced, full = (
            centrality_design_bus(sample)
            if mode == "bus"
            else centrality_design_rail(sample)
        )
        result = partial_model_test(
            sample[metric].to_numpy(dtype=float), reduced, full, rng
        )
        rows.append({"mode": mode, "metric": metric, "n": len(sample), **result})
    output = pd.DataFrame(rows)
    output["p_fdr_bh"] = bh_adjust(output["p_freedman_lane"])
    return output


def rail_weighted_summary(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for group in LNWC_GROUPS:
        weights = frame[f"lnwc_{group}_share"].to_numpy(dtype=float)
        positive = weights > 0
        for metric in metrics:
            values = frame[metric].to_numpy(dtype=float)
            valid = positive & np.isfinite(values)
            w = weights[valid]
            x = values[valid]
            mean = np.average(x, weights=w)
            variance = np.average((x - mean) ** 2, weights=w)
            rows.append(
                {
                    "lnwc_group": group,
                    "metric": metric,
                    "weighted_mean": mean,
                    "weighted_sd": np.sqrt(variance),
                    "sum_station_weights": w.sum(),
                    "effective_n": w.sum() ** 2 / np.square(w).sum(),
                }
            )
    return pd.DataFrame(rows)


def robust_standardised_matrix(
    summary: pd.DataFrame,
    value_column: str,
    metrics: list[str],
) -> pd.DataFrame:
    wide = summary.pivot(index="lnwc_group", columns="metric", values=value_column)
    wide = wide.reindex(index=LNWC_GROUPS, columns=metrics)
    median = wide.median(axis=0)
    iqr = wide.quantile(0.75) - wide.quantile(0.25)
    return wide.sub(median).div(iqr.replace(0, np.nan)).fillna(0)


def build_bus() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics = pd.read_csv(RQ1_CONTEXT / "bus_unit_metrics.csv").rename(
        columns={"lsoa": "lsoa21cd"}
    )
    baseline = pd.read_csv(BASELINE / "bus_analysis_lsoa.csv")
    bus = baseline[
        ["lsoa21cd", "lnc_grp", "cluster", "max_posterior", "entropy"]
    ].merge(
        metrics.drop(columns=["cluster", "max_posterior", "entropy"]),
        on="lsoa21cd",
        validate="one_to_one",
    )

    boundaries = gpd.read_file(LSOA_BOUNDARIES).to_crs("EPSG:27700")
    centres = boundaries[["LSOA21CD", "geometry"]].copy()
    centroids = centres.geometry.centroid
    centres["distance_to_centre_km"] = np.sqrt(
        (centroids.x - CENTRE_EASTING) ** 2
        + (centroids.y - CENTRE_NORTHING) ** 2
    ) / 1000
    bus = bus.merge(
        centres[["LSOA21CD", "distance_to_centre_km"]].rename(
            columns={"LSOA21CD": "lsoa21cd"}
        ),
        on="lsoa21cd",
        validate="one_to_one",
    )
    if bus[BUS_PRIMARY + ["lnc_grp", "distance_to_centre_km"]].isna().any().any():
        raise AssertionError("Bus primary analysis contains missing values")
    bus.to_csv(DATA / "bus_direct_metrics_lsoa.csv", index=False)

    summary = bus_group_summary(bus, BUS_PRIMARY + ["deep_night_share"])
    summary.to_csv(DATA / "bus_metrics_by_lnwc.csv", index=False)
    kruskal = kruskal_results(bus, BUS_PRIMARY)
    kruskal.to_csv(DATA / "bus_kruskal_wallis.csv", index=False)
    pairwise = pd.concat(
        [dunn_pairwise(bus, metric) for metric in BUS_PRIMARY], ignore_index=True
    )
    pairwise.to_csv(DATA / "bus_dunn_pairwise.csv", index=False)
    adjusted = centrality_tests(bus, BUS_PRIMARY, "bus")
    adjusted.to_csv(DATA / "bus_centrality_adjusted_tests.csv", index=False)
    return bus, summary, kruskal, adjusted


def build_rail() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics = pd.read_csv(RQ1_CONTEXT / "rail_unit_metrics.csv")
    baseline = pd.read_csv(BASELINE / "rail_analysis_station.csv")
    rail = baseline.merge(
        metrics.drop(
            columns=[
                "cluster",
                "max_posterior",
                "entropy",
                "tot_entry",
                "tot_exit",
            ]
        ),
        on="NLC",
        validate="one_to_one",
        suffixes=("", "_metric"),
    )
    rail = rail.loc[rail["analysis_eligible"].astype(bool)].copy()
    rail["distance_to_centre_km"] = np.sqrt(
        (rail["easting"] - CENTRE_EASTING) ** 2
        + (rail["northing"] - CENTRE_NORTHING) ** 2
    ) / 1000
    required = RAIL_PRIMARY + RAIL_SECONDARY + SHARES + ["distance_to_centre_km"]
    if rail[required].isna().any().any():
        raise AssertionError("Rail primary analysis contains missing values")
    rail.to_csv(DATA / "rail_direct_metrics_station.csv", index=False)

    weighted = rail_weighted_summary(rail, RAIL_PRIMARY + RAIL_SECONDARY)
    weighted.to_csv(DATA / "rail_metrics_by_lnwc_fractional.csv", index=False)
    adjusted = centrality_tests(rail, RAIL_PRIMARY, "rail")
    adjusted.to_csv(DATA / "rail_centrality_adjusted_tests.csv", index=False)
    return rail, weighted, adjusted


def plot_bus(
    bus: pd.DataFrame,
    summary: pd.DataFrame,
    kruskal: pd.DataFrame,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    labels = {
        "log_total_activity": "log(1 + total activity)",
        "post_midnight_share": "Post-midnight share",
        "direction_balance": "Direction balance",
        "weekend_ratio": "Weekend / weekday ratio",
    }
    for axis, metric in zip(axes.flat, BUS_PRIMARY, strict=True):
        sns.boxplot(
            data=bus,
            x="lnc_grp",
            y=metric,
            hue="lnc_grp",
            legend=False,
            palette="Set2",
            showfliers=False,
            ax=axis,
        )
        effect = kruskal.set_index("metric").loc[metric, "epsilon_squared"]
        axis.set_title(f"{labels[metric]} (epsilon²={effect:.3f})")
        axis.set_xlabel("LNWC group")
    plt.tight_layout()
    plt.savefig(FIGURES / "bus_direct_metrics_by_lnwc.png", dpi=220, bbox_inches="tight")
    plt.close()

    matrix = summary.loc[summary["metric"].isin(BUS_PRIMARY)]
    standardised = robust_standardised_matrix(matrix, "median", BUS_PRIMARY)
    standardised.to_csv(DATA / "bus_lnwc_metric_signature_z.csv")
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        standardised,
        cmap="vlag",
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"label": "Group median deviation / across-group IQR"},
    )
    plt.title("Bus: direct transport-metric signature by LNWC group")
    plt.xlabel("")
    plt.ylabel("LNWC group")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "bus_lnwc_metric_signature.png", dpi=220, bbox_inches="tight")
    plt.close()


def plot_rail(weighted: pd.DataFrame) -> None:
    matrix = weighted.loc[weighted["metric"].isin(RAIL_PRIMARY)]
    standardised = robust_standardised_matrix(matrix, "weighted_mean", RAIL_PRIMARY)
    standardised.to_csv(DATA / "rail_lnwc_metric_signature_z.csv")
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        standardised,
        cmap="vlag",
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"label": "Fractionally weighted mean deviation / across-group IQR"},
    )
    plt.title("Rail: direct transport-metric signature by LNWC catchment composition")
    plt.xlabel("")
    plt.ylabel("LNWC group")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "rail_lnwc_metric_signature.png", dpi=220, bbox_inches="tight")
    plt.close()


def extrema_lines(
    table: pd.DataFrame,
    metric: str,
    value_column: str,
) -> str:
    subset = table.loc[table["metric"] == metric].set_index("lnwc_group")[value_column]
    return (
        f"- `{metric}`: highest group {int(subset.idxmax())} ({subset.max():.3f}); "
        f"lowest group {int(subset.idxmin())} ({subset.min():.3f})."
    )


def main() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    required = [
        RQ1_CONTEXT / "bus_unit_metrics.csv",
        RQ1_CONTEXT / "rail_unit_metrics.csv",
        BASELINE / "bus_analysis_lsoa.csv",
        BASELINE / "rail_analysis_station.csv",
        LSOA_BOUNDARIES,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")

    bus, bus_summary, bus_kw, bus_adjusted = build_bus()
    rail, rail_weighted, rail_adjusted = build_rail()
    plot_bus(bus, bus_summary, bus_kw)
    plot_rail(rail_weighted)

    combined_adjusted = pd.concat(
        [bus_adjusted, rail_adjusted], ignore_index=True
    )
    combined_adjusted.to_csv(DATA / "centrality_adjusted_tests_all.csv", index=False)

    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# RQ2 direct transport metrics × LNWC — provisional results",
        "",
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite / experiment-agent",
        "- Origin Mode: run",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "- Version Label: rq2_direct_metrics_v1",
        "",
        "## Design",
        "",
        f"- Bus: {len(bus)} LSOAs, direct seven-category LNWC label.",
        f"- Rail: {len(rail)} eligible stations, seven-part catchment composition.",
        "- Primary weighting is one LSOA/station per observation. Rail group means use fractional catchment shares.",
        "- Centrality sensitivity controls only straight-line distance to Charing Cross.",
        "",
        "## Bus descriptive contrasts",
        "",
    ]
    for metric in BUS_PRIMARY:
        lines.append(extrema_lines(bus_summary, metric, "median"))
    lines.extend(["", "## Bus omnibus results", ""])
    for row in bus_kw.itertuples(index=False):
        lines.append(
            f"- `{row.metric}`: H={row.kruskal_h:.2f}, epsilon²={row.epsilon_squared:.3f}, "
            f"BH-adjusted p={row.p_fdr_bh:.4g}."
        )
    lines.extend(["", "## Rail fractional-composition contrasts", ""])
    for metric in RAIL_PRIMARY:
        lines.append(extrema_lines(rail_weighted, metric, "weighted_mean"))
    lines.extend(["", "## Centrality-adjusted exploratory omnibus tests", ""])
    for row in combined_adjusted.itertuples(index=False):
        lines.append(
            f"- {row.mode} `{row.metric}`: partial R²={row.partial_r_squared:.3f}, "
            f"Freedman–Lane p={row.p_freedman_lane:.4f}, BH-adjusted p={row.p_fdr_bh:.4f}."
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "- STATUS (2026-07-14): the centrality-adjusted partial-R^2 results below are PROVISIONAL, not a primary RQ2 result. They pool all stations/LSOAs regardless of RQ1 cluster, so they cannot say which cluster type drives the relationship -- this was judged disconnected from the actual RQ2 question and a new method is pending. Do not cite these partial-R^2 numbers as a settled finding without checking for an updated version of this analysis.",
            "- LNWC is available only as a seven-category area typology. The analysis cannot isolate its underlying worker counts, industries or three-hour components.",
            "- Results are area-level associations, not evidence that passengers belong to the worker groups described by an LNWC portrait.",
            "- Distance to centre is only one confounder. Spatial autocorrelation, service supply and interchange structure are not yet modelled.",
            "- Rail Night Tube extension reflects both use and service availability.",
            "- Bus remains an LSOA-level analysis and cannot support stop- or route-level behavioural claims.",
        ]
    )
    (REPORT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    audit = pd.DataFrame(
        [
            {"component": "bus", "metric": "analysis_rows", "value": len(bus)},
            {
                "component": "bus",
                "metric": "lnwc_groups",
                "value": bus["lnc_grp"].nunique(),
            },
            {
                "component": "bus",
                "metric": "missing_primary_values",
                "value": int(bus[BUS_PRIMARY].isna().sum().sum()),
            },
            {"component": "rail", "metric": "eligible_stations", "value": len(rail)},
            {
                "component": "rail",
                "metric": "share_sum_max_error",
                "value": float((rail[SHARES].sum(axis=1) - 1).abs().max()),
            },
            {
                "component": "rail",
                "metric": "missing_primary_values",
                "value": int(rail[RAIL_PRIMARY].isna().sum().sum()),
            },
        ]
    )
    audit.to_csv(DATA / "data_audit.csv", index=False)
    metadata = {
        "generated_utc": generated,
        "duration_seconds": time.time() - START,
        "command": "py -3 src/run_direct_metrics_analysis.py",
        "python": sys.version,
        "platform": platform.platform(),
        "parameters": {
            "permutations": N_PERMUTATIONS,
            "seed": RANDOM_SEED,
            "centrality_reference": "Charing Cross BNG 530134,180379",
        },
    }
    (REPORT / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(
        f"Completed direct RQ2 analysis in {metadata['duration_seconds']:.1f}s; "
        f"bus={len(bus)}, rail={len(rail)}."
    )


if __name__ == "__main__":
    main()

