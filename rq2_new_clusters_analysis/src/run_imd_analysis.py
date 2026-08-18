"""RQ1 cluster x IMD2025 "weak line" association, for the two new
sensitivity clustering results.

Adapted from ``rq2test analysis/src/run_imd2025_analysis.py``, weak-line
block only (does IMD score differ across clusters, Kruskal-Wallis). The
pooled, cluster-blind "main line" continuous-metric x IMD test is
deliberately NOT reproduced here -- per the user's 2026-07-23 decision, it
was never part of their current report version, it is cluster-blind by
construction (defeats the point of this sensitivity layer), and it remains
flagged provisional/not primary for the canonical result too.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

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
        samples = [frame.loc[frame[group_col] == group, metric].dropna().to_numpy() for group in groups]
        samples = [s for s in samples if len(s) > 0]
        statistic, p_value = stats.kruskal(*samples)
        n = sum(map(len, samples))
        k = len(samples)
        epsilon_sq = max(0.0, (statistic - k + 1) / (n - k))
        rows.append({"metric": metric, "kruskal_h": statistic, "df": k - 1, "p_value": p_value, "epsilon_squared": epsilon_sq, "n": n})
    result = pd.DataFrame(rows)
    result["p_fdr_bh"] = bh_adjust(result["p_value"])
    return result


def build_bus_imd(imd: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    baseline = pd.read_csv(C.DATA_OUT / "bus_analysis_lsoa.csv")
    bus = baseline.merge(imd, on="lsoa21cd", how="left", validate="one_to_one")
    audit = {
        "input_rows": int(len(bus)), "matched_imd_rows": int(bus["imd_score"].notna().sum()),
        "unmatched_imd_rows": int(bus["imd_score"].isna().sum()), "match_rate": float(bus["imd_score"].notna().mean()),
    }
    bus_matched = bus.dropna(subset=["imd_score"]).copy()
    bus_matched.to_csv(C.DATA_OUT / "bus_imd_metrics_lsoa.csv", index=False)
    weak_line = kruskal_by_group(bus_matched, "cluster", sorted(bus_matched["cluster"].unique()), ["imd_score"])
    weak_line.to_csv(C.DATA_OUT / "bus_cluster_vs_imd_kruskal.csv", index=False)
    return bus_matched, weak_line, audit


def build_rail_imd(imd: pd.DataFrame, lsoa_boundaries: gpd.GeoDataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    # Changed 2026-08-08, user decision: read whichever radius's catchment
    # geojson run_lnwc_analysis.py just built (filename carries the radius),
    # rather than a hardcoded "1200m" name that would silently go stale if
    # the radius changes.
    catchments = gpd.read_file(
        C.SPATIAL_OUT / f"rail_catchments_{C.RAIL_CATCHMENT_METRES}m_allmodes.geojson"
    ).to_crs(C.CRS_BNG)
    catchments["NLC"] = catchments["NLC"].astype(int)
    boundaries_imd = lsoa_boundaries.merge(imd, on="lsoa21cd", how="left", validate="one_to_one")

    intersections = gpd.overlay(
        catchments[["NLC", "geometry"]], boundaries_imd[["lsoa21cd", "imd_score", "geometry"]], how="intersection", keep_geom_type=False,
    )
    intersections["piece_area_m2"] = intersections.geometry.area
    intersections["catchment_area_m2"] = intersections["NLC"].map(catchments.set_index("NLC").geometry.area)
    valid = intersections.loc[(intersections["piece_area_m2"] > 0) & intersections["imd_score"].notna()].copy()

    # Coverage stays area-based (data-completeness diagnostic). The IMD score
    # itself is now an equal-weight average across distinct intersecting
    # LSOAs -- one vote per LSOA regardless of overlap area -- matching
    # rq2_independent_variables and rq2_loac_analysis, and replacing the
    # previous area-weighted average.
    coverage = valid.groupby("NLC")["piece_area_m2"].sum().rename("imd_covered_area_m2")
    distinct_lsoa = valid[["NLC", "lsoa21cd", "imd_score"]].drop_duplicates()
    equal_weight_score = distinct_lsoa.groupby("NLC")["imd_score"].mean().rename("imd_score")
    rail_imd = pd.concat([equal_weight_score, coverage], axis=1).reset_index()
    rail_imd = rail_imd.merge(
        catchments[["NLC", "catchment_area_m2"]].rename(columns={"catchment_area_m2": "total_catchment_area_m2"}), on="NLC", validate="one_to_one",
    )
    rail_imd["imd_coverage_ratio"] = rail_imd["imd_covered_area_m2"] / rail_imd["total_catchment_area_m2"]

    baseline = pd.read_csv(C.DATA_OUT / "rail_analysis_station.csv")
    rail = baseline.merge(rail_imd, on="NLC", how="left", validate="one_to_one")

    audit = {
        "input_rows": int(len(rail)), "lnwc_eligible_stations": int(rail["analysis_eligible"].astype(bool).sum()),
        "imd_matched_stations": int(rail["imd_score"].notna().sum()),
        "both_eligible": int((rail["analysis_eligible"].astype(bool) & rail["imd_score"].notna()).sum()),
    }
    rail_valid = rail.loc[rail["analysis_eligible"].astype(bool) & rail["imd_score"].notna()].copy()
    rail_valid.to_csv(C.DATA_OUT / "rail_imd_metrics_station.csv", index=False)
    weak_line = kruskal_by_group(rail_valid, "cluster", sorted(rail_valid["cluster"].unique()), ["imd_score"])
    weak_line.to_csv(C.DATA_OUT / "rail_cluster_vs_imd_kruskal.csv", index=False)
    return rail_valid, weak_line, audit


def plot_cluster_imd(bus: pd.DataFrame, bus_weak: pd.DataFrame, rail: pd.DataFrame, rail_weak: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    bus_row = bus_weak.iloc[0]
    sns.boxplot(data=bus, x="cluster", y="imd_score", hue="cluster", legend=False, palette="Set2", showfliers=False, ax=axes[0])
    sns.stripplot(data=bus, x="cluster", y="imd_score", color="black", size=1.5, alpha=0.15, jitter=0.25, ax=axes[0])
    axes[0].set_title(
        f"Bus (StopArea CLR, K={C.BUS_K}): cluster x IMD score\n"
        f"H={bus_row.kruskal_h:.1f}, epsilon2={bus_row.epsilon_squared:.3f}, BH p={bus_row.p_fdr_bh:.3g}, n={int(bus_row.n)}"
    )
    axes[0].set_xlabel("Sensitivity bus cluster")
    axes[0].set_ylabel("IMD 2025 score (higher = more deprived)")
    axes[0].xaxis.set_major_formatter(lambda x, _: f"C{int(x)}")

    rail_row = rail_weak.iloc[0]
    sns.boxplot(data=rail, x="cluster", y="imd_score", hue="cluster", legend=False, palette="Set2", showfliers=False, ax=axes[1])
    sns.stripplot(data=rail, x="cluster", y="imd_score", color="black", size=3, alpha=0.35, jitter=0.25, ax=axes[1])
    axes[1].set_title(
        f"Rail (all-modes, K={C.RAIL_K}): cluster x IMD score\n"
        f"H={rail_row.kruskal_h:.1f}, epsilon2={rail_row.epsilon_squared:.3f}, BH p={rail_row.p_fdr_bh:.3g}, n={int(rail_row.n)}"
    )
    axes[1].set_xlabel("Sensitivity rail cluster")
    axes[1].set_ylabel("")
    axes[1].xaxis.set_major_formatter(lambda x, _: f"C{int(x)}")

    fig.suptitle("Weak line -- sensitivity cluster vs IMD 2025 score", y=1.02)
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / "cluster_vs_imd_score.png", dpi=220, bbox_inches="tight")
    plt.close()


def main() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    required = [
        C.DATA_OUT / "bus_analysis_lsoa.csv", C.DATA_OUT / "rail_analysis_station.csv",
        C.SPATIAL_OUT / "rail_catchments_1200m_allmodes.geojson", C.LSOA_BOUNDARIES, C.IMD_LSOA21,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs (run run_context_metrics.py and run_lnwc_analysis.py first): {missing}")

    imd = pd.read_csv(C.IMD_LSOA21)
    lsoa_boundaries = gpd.read_file(C.LSOA_BOUNDARIES).to_crs(C.CRS_BNG).rename(columns={"LSOA21CD": "lsoa21cd"})

    bus, bus_weak, bus_audit = build_bus_imd(imd)
    rail, rail_weak, rail_audit = build_rail_imd(imd, lsoa_boundaries)
    plot_cluster_imd(bus, bus_weak, rail, rail_weak)

    combined_weak = pd.concat([bus_weak.assign(mode="bus"), rail_weak.assign(mode="rail")], ignore_index=True)
    combined_weak.to_csv(C.DATA_OUT / "cluster_vs_imd_kruskal_all.csv", index=False)

    audit = pd.DataFrame(
        [{"component": "bus", "metric": k, "value": v} for k, v in bus_audit.items()]
        + [{"component": "rail", "metric": k, "value": v} for k, v in rail_audit.items()]
    )
    audit.to_csv(C.DATA_OUT / "imd_data_audit.csv", index=False)

    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# RQ2 sensitivity clusters -- IMD2025 weak-line association",
        "",
        "## Material Passport",
        "",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "- Version Label: rq2_new_clusters_imd_v1",
        "",
        "## Design",
        "",
        "- IMD 2025 (MHCLG, 2025-10), natively on 2021 LSOA boundaries -- same source as the canonical pipeline's IMD2025 refresh.",
        "- Weak line only: does IMD score differ across sensitivity clusters (Kruskal-Wallis). The pooled 'main line' "
        "continuous-metric x IMD test is intentionally not reproduced here -- it is cluster-blind by design and was "
        "not part of the user's current report version either.",
        f"- Rail IMD is the equal-weight average across distinct intersecting LSOAs (one vote per LSOA, "
        f"not weighted by overlap area), using the same {C.RAIL_CATCHMENT_METRES} m Voronoi-clipped catchments built in "
        f"run_lnwc_analysis.py (403-station all-modes geometry, not the canonical 270-station one). "
        f"Changed 2026-08-08 from a previous 1,200 m, area-weighted design to match rq2_independent_variables "
        f"and rq2_loac_analysis.",
        "",
        "## Coverage",
        "",
        f"- Bus: {bus_audit['matched_imd_rows']}/{bus_audit['input_rows']} LSOAs matched to IMD ({bus_audit['match_rate']:.1%}).",
        f"- Rail: {rail_audit['both_eligible']}/{rail_audit['input_rows']} stations eligible for both LNWC-extent and IMD analysis "
        f"(LNWC-eligible alone: {rail_audit['lnwc_eligible_stations']}; IMD-matched alone: {rail_audit['imd_matched_stations']}).",
        "",
        "## Weak line: cluster vs IMD score (Kruskal-Wallis)",
        "",
    ]
    for row in combined_weak.itertuples(index=False):
        lines.append(f"- {row.mode} cluster -> imd_score: H={row.kruskal_h:.2f}, epsilon2={row.epsilon_squared:.3f}, BH-adjusted p={row.p_fdr_bh:.4g}.")
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "- IMD describes the deprivation profile of resident/surrounding populations, not the transport users themselves.",
        "- Distance-to-centre is not modelled here (that belongs to the pooled main-line design, which is deliberately excluded).",
        "- Compare against the canonical weak-line numbers via the combined report, not in isolation.",
    ])
    (C.REPORT_OUT / "IMD_ASSOCIATION.md").write_text("\n".join(lines), encoding="utf-8")

    metadata = {
        "generated_utc": generated, "duration_seconds": time.time() - START,
        "command": "py -3 src/run_imd_analysis.py", "python": sys.version, "platform": platform.platform(),
        "imd_source": "IMD2025 File 7 (MHCLG, 2025-10), 2021 LSOA native",
    }
    (C.REPORT_OUT / "run_metadata_imd.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Completed IMD weak-line analysis in {metadata['duration_seconds']:.1f}s; bus={len(bus)}, rail={len(rail)}.")


if __name__ == "__main__":
    main()
