"""IMD 2025 x RQ1 outputs -- 800 m rail catchment sensitivity variant.

Non-destructive sidecar to run_imd2025_analysis.py: identical statistical
design (weak line + main line), only the rail catchment source differs --
reads outputs_800m/spatial/rail_catchments_800m.geojson and
outputs_800m/data/rail_analysis_station.csv (produced by
run_analysis_800m.py) instead of the 1200 m canonical outputs under
outputs/. Writes to outputs_800m/imd_metrics_2025/; the 1200 m canonical
outputs/imd_metrics_2025/ is never read or written by this script.

  (A) weak line  -- does IMD differ across RQ1 shape clusters (Kruskal-Wallis)
  (B) main line  -- do continuous context metrics vary with IMD, controlling
                    for distance to Charing Cross (centrality-adjusted
                    Freedman-Lane permutation, mirroring the LNWC test)

STATUS: line (B) remains PROVISIONAL / not a primary RQ2 result for the same
reason as the 1200 m canonical run (pooled, cluster-blind design) --
unrelated to the catchment radius change. Line (A), the weak-line cluster x
IMD Kruskal-Wallis test, is the primary comparison of interest for this
800 m sensitivity check: compare its epsilon-squared/Cramer's-V-equivalent
directly against the 1200 m canonical numbers in
outputs/imd_metrics_2025/report/RESULTS_SUMMARY.md.
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
BASELINE = ROOT / "outputs_800m" / "data"
SPATIAL = ROOT / "outputs_800m" / "spatial"
LSOA_BOUNDARIES = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
IMD_LSOA21 = FYP / "IMDdata_2025" / "imd2025_lsoa21_london.csv"

OUT = ROOT / "outputs_800m" / "imd_metrics_2025"
DATA = OUT / "data"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
for directory in (DATA, FIGURES, REPORT):
    directory.mkdir(parents=True, exist_ok=True)

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
CENTRE_EASTING = 530134.0
CENTRE_NORTHING = 180379.0
N_PERMUTATIONS = 999
RANDOM_SEED = 42
IMD_DECILES = list(range(1, 11))
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


def kruskal_by_group(frame: pd.DataFrame, group_col: str, groups: list, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for metric in metrics:
        samples = [
            frame.loc[frame[group_col] == group, metric].dropna().to_numpy()
            for group in groups
        ]
        samples = [s for s in samples if len(s) > 0]
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


def partial_model_test(y: np.ndarray, reduced: np.ndarray, full: np.ndarray, rng: np.random.Generator) -> dict[str, float]:
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


def centrality_imd_tests(frame: pd.DataFrame, metrics: list[str], mode: str) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    rows = []
    for metric in metrics:
        sample = frame.dropna(subset=[metric, "distance_to_centre_km", "imd_score"]).copy()
        distance = sample["distance_to_centre_km"].to_numpy(dtype=float)
        distance = (distance - distance.mean()) / distance.std()
        imd = sample["imd_score"].to_numpy(dtype=float)
        imd = (imd - imd.mean()) / imd.std()
        reduced = np.column_stack([np.ones(len(sample)), distance])
        full = np.column_stack([reduced, imd])
        result = partial_model_test(sample[metric].to_numpy(dtype=float), reduced, full, rng)
        spearman_r, spearman_p = stats.spearmanr(sample[metric], sample["imd_score"])
        rows.append(
            {
                "mode": mode,
                "metric": metric,
                "n": len(sample),
                "spearman_r_imd_raw": spearman_r,
                "spearman_p_imd_raw": spearman_p,
                **result,
            }
        )
    output = pd.DataFrame(rows)
    output["p_fdr_bh"] = bh_adjust(output["p_freedman_lane"])
    return output


def build_bus() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    metrics = pd.read_csv(RQ1_CONTEXT / "bus_unit_metrics.csv").rename(columns={"lsoa": "lsoa21cd"})
    baseline = pd.read_csv(BASELINE / "bus_analysis_lsoa.csv")
    imd = pd.read_csv(IMD_LSOA21)

    bus_all = baseline[["lsoa21cd", "cluster", "lnc_grp"]].merge(
        metrics.drop(columns=["cluster", "max_posterior", "entropy"]),
        on="lsoa21cd",
        validate="one_to_one",
    )
    bus = bus_all.merge(imd, on="lsoa21cd", how="left", validate="one_to_one")

    audit = {
        "input_rows": int(len(bus)),
        "matched_imd_rows": int(bus["imd_score"].notna().sum()),
        "unmatched_imd_rows": int(bus["imd_score"].isna().sum()),
        "match_rate": float(bus["imd_score"].notna().mean()),
    }

    boundaries = gpd.read_file(LSOA_BOUNDARIES).to_crs("EPSG:27700")
    centroids = boundaries.geometry.centroid
    boundaries["distance_to_centre_km"] = np.sqrt(
        (centroids.x - CENTRE_EASTING) ** 2 + (centroids.y - CENTRE_NORTHING) ** 2
    ) / 1000
    bus = bus.merge(
        boundaries[["LSOA21CD", "distance_to_centre_km"]].rename(columns={"LSOA21CD": "lsoa21cd"}),
        on="lsoa21cd",
        validate="one_to_one",
    )
    bus_matched = bus.dropna(subset=["imd_score"]).copy()
    bus_matched.to_csv(DATA / "bus_imd_metrics_lsoa.csv", index=False)

    weak_line = kruskal_by_group(bus_matched, "cluster", sorted(bus_matched["cluster"].unique()), ["imd_score"])
    weak_line.to_csv(DATA / "bus_cluster_vs_imd_kruskal.csv", index=False)

    kw_rows = []
    for metric in BUS_PRIMARY:
        rows = kruskal_by_group(bus_matched, "imd_decile_int", IMD_DECILES, [metric])
        kw_rows.append(rows)
    main_line_kw = pd.concat(kw_rows, ignore_index=True)
    main_line_kw["p_fdr_bh"] = bh_adjust(main_line_kw["p_value"])
    main_line_kw.to_csv(DATA / "bus_imd_decile_kruskal.csv", index=False)

    summary_rows = []
    for decile, subset in bus_matched.groupby("imd_decile_int"):
        for metric in BUS_PRIMARY:
            values = subset[metric].dropna()
            summary_rows.append(
                {
                    "imd_decile": int(decile),
                    "metric": metric,
                    "n": len(values),
                    "median": values.median(),
                    "q25": values.quantile(0.25),
                    "q75": values.quantile(0.75),
                }
            )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(DATA / "bus_metrics_by_imd_decile.csv", index=False)

    adjusted = centrality_imd_tests(bus_matched, BUS_PRIMARY, "bus")
    adjusted.to_csv(DATA / "bus_centrality_imd_adjusted_tests.csv", index=False)

    return bus_matched, weak_line, main_line_kw, summary, adjusted, audit


def build_rail() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    catchments = gpd.read_file(SPATIAL / "rail_catchments_800m.geojson").to_crs("EPSG:27700")
    catchments["NLC"] = catchments["NLC"].astype(int)
    boundaries = gpd.read_file(LSOA_BOUNDARIES).to_crs("EPSG:27700")
    boundaries = boundaries.rename(columns={"LSOA21CD": "lsoa21cd"})
    imd = pd.read_csv(IMD_LSOA21)
    boundaries_imd = boundaries.merge(imd, on="lsoa21cd", how="left", validate="one_to_one")

    intersections = gpd.overlay(
        catchments[["NLC", "geometry"]],
        boundaries_imd[["lsoa21cd", "imd_score", "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )
    intersections["piece_area_m2"] = intersections.geometry.area
    intersections["catchment_area_m2"] = intersections["NLC"].map(
        catchments.set_index("NLC").geometry.area
    )
    valid = intersections.loc[
        (intersections["piece_area_m2"] > 0) & intersections["imd_score"].notna()
    ].copy()

    coverage = valid.groupby("NLC")["piece_area_m2"].sum().rename("imd_covered_area_m2")
    weighted_score = (
        valid.assign(weighted=valid["imd_score"] * valid["piece_area_m2"])
        .groupby("NLC")["weighted"]
        .sum()
        .div(coverage)
        .rename("imd_score")
    )
    rail_imd = pd.concat([weighted_score, coverage], axis=1).reset_index()
    rail_imd = rail_imd.merge(
        catchments[["NLC", "catchment_area_m2"]].rename(columns={"catchment_area_m2": "total_catchment_area_m2"}),
        on="NLC",
        validate="one_to_one",
    )
    rail_imd["imd_coverage_ratio"] = rail_imd["imd_covered_area_m2"] / rail_imd["total_catchment_area_m2"]

    baseline = pd.read_csv(BASELINE / "rail_analysis_station.csv")
    metrics = pd.read_csv(RQ1_CONTEXT / "rail_unit_metrics.csv")
    rail = baseline.merge(rail_imd, on="NLC", how="left", validate="one_to_one")
    rail = rail.merge(
        metrics.drop(columns=["cluster", "max_posterior", "entropy", "tot_entry", "tot_exit"]),
        on="NLC",
        validate="one_to_one",
        suffixes=("", "_metric"),
    )

    audit = {
        "input_rows": int(len(rail)),
        "lnwc_eligible_stations": int(rail["analysis_eligible"].astype(bool).sum()),
        "imd_matched_stations": int(rail["imd_score"].notna().sum()),
        "both_eligible": int((rail["analysis_eligible"].astype(bool) & rail["imd_score"].notna()).sum()),
    }

    rail_valid = rail.loc[rail["analysis_eligible"].astype(bool) & rail["imd_score"].notna()].copy()
    rail_valid["distance_to_centre_km"] = np.sqrt(
        (rail_valid["easting"] - CENTRE_EASTING) ** 2 + (rail_valid["northing"] - CENTRE_NORTHING) ** 2
    ) / 1000
    rail_valid.to_csv(DATA / "rail_imd_metrics_station.csv", index=False)

    weak_line = kruskal_by_group(rail_valid, "cluster", sorted(rail_valid["cluster"].unique()), ["imd_score"])
    weak_line.to_csv(DATA / "rail_cluster_vs_imd_kruskal.csv", index=False)

    adjusted = centrality_imd_tests(rail_valid, RAIL_PRIMARY, "rail")
    adjusted.to_csv(DATA / "rail_centrality_imd_adjusted_tests.csv", index=False)

    return rail_valid, weak_line, adjusted, audit


def plot_bus(bus: pd.DataFrame, kw: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    labels = {
        "log_total_activity": "log(1 + total activity)",
        "post_midnight_share": "Post-midnight share",
        "direction_balance": "Direction balance",
        "weekend_ratio": "Weekend / weekday ratio",
    }
    for axis, metric in zip(axes.flat, BUS_PRIMARY, strict=True):
        sns.boxplot(
            data=bus, x="imd_decile_int", y=metric, hue="imd_decile_int",
            legend=False, palette="RdYlBu", showfliers=False, ax=axis,
        )
        effect = kw.loc[kw["metric"] == metric, "epsilon_squared"].iloc[0]
        axis.set_title(f"{labels[metric]} (epsilon²={effect:.3f})")
        axis.set_xlabel("IMD decile (1 = most deprived)")
    plt.tight_layout()
    plt.savefig(FIGURES / "bus_direct_metrics_by_imd_decile.png", dpi=220, bbox_inches="tight")
    plt.close()


def plot_cluster_imd(bus: pd.DataFrame, bus_weak: pd.DataFrame, rail: pd.DataFrame, rail_weak: pd.DataFrame) -> None:
    """Weak-line figure: RQ1 cluster vs IMD score distribution (bus + rail), 800 m variant."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    bus_row = bus_weak.iloc[0]
    sns.boxplot(
        data=bus, x="cluster", y="imd_score", hue="cluster",
        legend=False, palette="Set2", showfliers=False, ax=axes[0],
    )
    sns.stripplot(
        data=bus, x="cluster", y="imd_score", color="black",
        size=1.5, alpha=0.15, jitter=0.25, ax=axes[0],
    )
    axes[0].set_title(
        f"Bus: cluster x IMD score\nH={bus_row.kruskal_h:.1f}, epsilon²={bus_row.epsilon_squared:.3f}, "
        f"BH p={bus_row.p_fdr_bh:.3g}, n={int(bus_row.n)}"
    )
    axes[0].set_xlabel("RQ1 bus cluster")
    axes[0].set_ylabel("IMD 2025 score (higher = more deprived)")
    axes[0].xaxis.set_major_formatter(lambda x, _: f"C{int(x)}")

    rail_row = rail_weak.iloc[0]
    sns.boxplot(
        data=rail, x="cluster", y="imd_score", hue="cluster",
        legend=False, palette="Set2", showfliers=False, ax=axes[1],
    )
    sns.stripplot(
        data=rail, x="cluster", y="imd_score", color="black",
        size=3, alpha=0.35, jitter=0.25, ax=axes[1],
    )
    axes[1].set_title(
        f"Rail: cluster x IMD score\nH={rail_row.kruskal_h:.1f}, epsilon²={rail_row.epsilon_squared:.3f}, "
        f"BH p={rail_row.p_fdr_bh:.3g}, n={int(rail_row.n)}"
    )
    axes[1].set_xlabel("RQ1 rail cluster")
    axes[1].set_ylabel("")
    axes[1].xaxis.set_major_formatter(lambda x, _: f"C{int(x)}")

    fig.suptitle("Weak line -- RQ1 shape cluster vs IMD 2025 score (800 m catchment sensitivity)", y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES / "cluster_vs_imd_score.png", dpi=220, bbox_inches="tight")
    plt.close()


def main() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    required = [RQ1_CONTEXT / "bus_unit_metrics.csv", RQ1_CONTEXT / "rail_unit_metrics.csv",
                BASELINE / "bus_analysis_lsoa.csv", BASELINE / "rail_analysis_station.csv",
                SPATIAL / "rail_catchments_800m.geojson", LSOA_BOUNDARIES, IMD_LSOA21]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")

    bus, bus_weak, bus_kw, bus_summary, bus_adjusted, bus_audit = build_bus()
    plot_bus(bus, bus_kw)
    rail, rail_weak, rail_adjusted, rail_audit = build_rail()
    plot_cluster_imd(bus, bus_weak, rail, rail_weak)

    combined_adjusted = pd.concat([bus_adjusted, rail_adjusted], ignore_index=True)
    combined_adjusted.to_csv(DATA / "centrality_imd_adjusted_tests_all.csv", index=False)
    combined_weak = pd.concat(
        [bus_weak.assign(mode="bus"), rail_weak.assign(mode="rail")], ignore_index=True
    )
    combined_weak.to_csv(DATA / "cluster_vs_imd_kruskal_all.csv", index=False)

    audit = pd.DataFrame(
        [{"component": "bus", "metric": k, "value": v} for k, v in bus_audit.items()]
        + [{"component": "rail", "metric": k, "value": v} for k, v in rail_audit.items()]
    )
    audit.to_csv(DATA / "data_audit.csv", index=False)

    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# RQ2 IMD extension (IMD2025, 800 m rail catchment sensitivity) -- provisional results",
        "",
        "## Material Passport",
        "",
        "- Origin Mode: run",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "- Version Label: rq2_imd_extension_v2_imd2025_800m",
        "",
        "## Design",
        "",
        "- Same design as the 1200 m canonical run (outputs/imd_metrics_2025/report/RESULTS_SUMMARY.md); only the rail catchment radius differs (800 m vs 1200 m Voronoi-clipped station buffers). Bus is catchment-independent (direct LSOA join) and is unaffected.",
        "- IMD is an independent socio-economic lens, parallel to LNWC (per Mikaella's guidance): not fused into the RQ1 cluster typology, not used as a covariate competing with LNWC.",
        "- Weak line: does IMD score differ across RQ1 shape clusters (Kruskal-Wallis).",
        "- Main line: do continuous context metrics vary with IMD, controlling for distance to Charing Cross (Freedman-Lane permutation, mirroring the LNWC centrality test).",
        "",
        "## Coverage",
        "",
        f"- Bus: {bus_audit['matched_imd_rows']}/{bus_audit['input_rows']} LSOAs matched to IMD ({bus_audit['match_rate']:.1%}).",
        f"- Rail: {rail_audit['both_eligible']}/{rail_audit['input_rows']} stations eligible for both LNWC-extent and IMD analysis (LNWC-eligible alone: {rail_audit['lnwc_eligible_stations']}; IMD-matched alone: {rail_audit['imd_matched_stations']}).",
        "",
        "## Weak line: RQ1 cluster vs IMD score (Kruskal-Wallis)",
        "",
    ]
    for row in combined_weak.itertuples(index=False):
        lines.append(
            f"- {row.mode} cluster -> imd_score: H={row.kruskal_h:.2f}, epsilon²={row.epsilon_squared:.3f}, BH-adjusted p={row.p_fdr_bh:.4g}."
        )
    lines.extend(["", "## Main line: continuous metrics by IMD decile (bus, Kruskal-Wallis)", ""])
    for row in bus_kw.itertuples(index=False):
        lines.append(
            f"- `{row.metric}`: H={row.kruskal_h:.2f}, epsilon²={row.epsilon_squared:.3f}, BH-adjusted p={row.p_fdr_bh:.4g}."
        )
    lines.extend(["", "## Centrality-adjusted exploratory omnibus tests (IMD score, partial R² beyond distance)", ""])
    for row in combined_adjusted.itertuples(index=False):
        lines.append(
            f"- {row.mode} `{row.metric}`: partial R²={row.partial_r_squared:.3f}, Freedman-Lane p={row.p_freedman_lane:.4f}, BH-adjusted p={row.p_fdr_bh:.4f}, Spearman r (raw, unadjusted)={row.spearman_r_imd_raw:.3f}."
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "- STATUS: the 'Main line' centrality-adjusted partial-R^2 results above are PROVISIONAL, not a primary RQ2 result -- same pooled-design caveat as the 1200 m canonical run, unrelated to the catchment radius change. The 'Weak line' (cluster vs IMD score) is the primary comparison of interest for this 800 m sensitivity check.",
            "- IMD describes the deprivation profile of resident/surrounding populations, not the transport users themselves.",
            "- Rail IMD is an area-weighted average of the 800 m Voronoi-clipped catchment (sensitivity variant); restricted to the same LNWC-eligible station set used in the 800 m RQ2 baseline for comparability.",
            "- Distance to centre is the only confounder modelled; spatial autocorrelation is not addressed.",
        ]
    )
    (REPORT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    metadata = {
        "generated_utc": generated,
        "duration_seconds": time.time() - START,
        "command": "py -3 src/run_imd2025_analysis_800m.py",
        "python": sys.version,
        "platform": platform.platform(),
        "parameters": {"permutations": N_PERMUTATIONS, "seed": RANDOM_SEED},
        "imd_source": "IMD2025 File 7 (MHCLG, 2025-10), 2021 LSOA native",
        "rail_catchment_metres": 800,
    }
    (REPORT / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Completed IMD2025 800m-sensitivity extension in {metadata['duration_seconds']:.1f}s; bus={len(bus)}, rail={len(rail)}.")


if __name__ == "__main__":
    main()
