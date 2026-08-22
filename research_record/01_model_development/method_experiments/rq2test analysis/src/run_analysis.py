"""Run the provisional RQ2 LNWC baseline analysis.

The script is deterministic and writes only inside ``rq2test analysis/outputs``.
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

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import seaborn as sns
import shapely
from matplotlib.colors import ListedColormap
from scipy.spatial import Voronoi
from scipy.stats import chi2_contingency
from shapely.geometry import Polygon

from config import (
    BUS_K,
    BUS_LABELS,
    BUS_META,
    CRS_BNG,
    DATA_OUT,
    FIGURE_OUT,
    LNWC,
    LNWC_COLOURS,
    LNWC_PORTRAITS,
    LSOA_BOUNDARIES,
    N_PERMUTATIONS,
    RANDOM_SEED,
    RAIL_CATCHMENT_METRES,
    RAIL_COORDS,
    RAIL_K,
    RAIL_LABELS,
    RAIL_META,
    REPORT_OUT,
    SPATIAL_OUT,
)


LNWC_GROUPS = list(range(1, 8))
SHARE_COLUMNS = [f"lnwc_{g}_share" for g in LNWC_GROUPS]
START_TIME = time.time()


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def finite_voronoi_polygons(vor: Voronoi, radius: float | None = None):
    """Convert a 2D SciPy Voronoi diagram to finite polygons in point order."""
    if vor.points.shape[1] != 2:
        raise ValueError("Voronoi input must be two-dimensional")

    new_regions: list[list[int]] = []
    new_vertices = vor.vertices.tolist()
    centre = vor.points.mean(axis=0)
    if radius is None:
        radius = float(np.ptp(vor.points, axis=0).max() * 2)

    all_ridges: dict[int, list[tuple[int, int, int]]] = {}
    for (point_1, point_2), (vertex_1, vertex_2) in zip(
        vor.ridge_points, vor.ridge_vertices, strict=True
    ):
        all_ridges.setdefault(point_1, []).append((point_2, vertex_1, vertex_2))
        all_ridges.setdefault(point_2, []).append((point_1, vertex_1, vertex_2))

    for point_index, region_index in enumerate(vor.point_region):
        vertices = vor.regions[region_index]
        if all(vertex >= 0 for vertex in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges[point_index]
        new_region = [vertex for vertex in vertices if vertex >= 0]
        for point_2, vertex_1, vertex_2 in ridges:
            if vertex_2 < 0:
                vertex_1, vertex_2 = vertex_2, vertex_1
            if vertex_1 >= 0:
                continue

            tangent = vor.points[point_2] - vor.points[point_index]
            tangent /= np.linalg.norm(tangent)
            normal = np.array([-tangent[1], tangent[0]])
            midpoint = vor.points[[point_index, point_2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - centre, normal)) * normal
            far_point = vor.vertices[vertex_2] + direction * radius
            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        polygon_vertices = np.asarray([new_vertices[v] for v in new_region])
        polygon_centre = polygon_vertices.mean(axis=0)
        angles = np.arctan2(
            polygon_vertices[:, 1] - polygon_centre[1],
            polygon_vertices[:, 0] - polygon_centre[0],
        )
        new_region = np.asarray(new_region)[np.argsort(angles)].tolist()
        new_regions.append(new_region)

    return new_regions, np.asarray(new_vertices)


def association_outputs(observed: pd.DataFrame):
    observed = observed.reindex(index=sorted(observed.index), columns=LNWC_GROUPS, fill_value=0)
    chi2, p_value, dof, expected_array = chi2_contingency(observed.to_numpy())
    expected = pd.DataFrame(expected_array, index=observed.index, columns=observed.columns)
    row_pct = observed.div(observed.sum(axis=1), axis=0)
    col_pct = observed.div(observed.sum(axis=0), axis=1)
    universe_share = observed.sum(axis=0) / observed.to_numpy().sum()
    enrichment = row_pct.div(universe_share, axis=1)
    std_residual = (observed - expected) / np.sqrt(expected)
    n = observed.to_numpy().sum()
    denominator = min(observed.shape[0] - 1, observed.shape[1] - 1)
    cramers_v = math.sqrt(chi2 / (n * denominator)) if denominator > 0 else np.nan
    stats = {
        "chi_square": float(chi2),
        "p_value": float(p_value),
        "degrees_of_freedom": int(dof),
        "cramers_v": float(cramers_v),
        "n": int(n),
    }
    return expected, row_pct, col_pct, enrichment, std_residual, stats


def composition_permutation_test(
    composition: np.ndarray, labels: np.ndarray, permutations: int, seed: int
):
    overall = composition.mean(axis=0)
    total_ss = float(((composition - overall) ** 2).sum())

    def between_ss(group_labels: np.ndarray) -> float:
        value = 0.0
        for group in np.unique(group_labels):
            group_values = composition[group_labels == group]
            value += len(group_values) * float(((group_values.mean(axis=0) - overall) ** 2).sum())
        return value

    observed = between_ss(labels)
    rng = np.random.default_rng(seed)
    null_values = np.empty(permutations)
    for index in range(permutations):
        null_values[index] = between_ss(rng.permutation(labels))
    p_value = (1 + int((null_values >= observed).sum())) / (permutations + 1)
    r_squared = observed / total_ss if total_ss > 0 else np.nan
    return {
        "pseudo_f_between_ss": observed,
        "total_ss": total_ss,
        "r_squared": float(r_squared),
        "permutation_p": float(p_value),
        "n_permutations": permutations,
        "n": int(len(composition)),
    }


def save_matrix(matrix: pd.DataFrame, name: str, index_label: str = "cluster"):
    matrix.rename_axis(index=index_label, columns="lnwc_group").to_csv(DATA_OUT / f"{name}.csv")


def draw_heatmap(matrix: pd.DataFrame, title: str, output: Path, fmt: str = ".2f"):
    plt.figure(figsize=(10, max(4.5, 0.8 * len(matrix))))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=fmt,
        cmap="RdBu_r",
        center=1 if "Enrichment" in title else None,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Ratio" if "Enrichment" in title else "Share"},
    )
    plt.title(title, pad=14)
    plt.xlabel("LNWC group")
    plt.ylabel("RQ1 cluster")
    plt.tight_layout()
    plt.savefig(output, dpi=220, bbox_inches="tight")
    plt.close()


def top_enrichments(enrichment: pd.DataFrame, top_n: int = 2):
    rows = []
    for cluster, values in enrichment.iterrows():
        for group, ratio in values.sort_values(ascending=False).head(top_n).items():
            rows.append(
                {
                    "cluster": int(cluster),
                    "lnwc_group": int(group),
                    "enrichment_ratio": float(ratio),
                }
            )
    return pd.DataFrame(rows)


def build_bus_analysis(lnwc: pd.DataFrame, lsoa: gpd.GeoDataFrame):
    labels = pd.read_csv(BUS_LABELS).rename(columns={"unit": "lsoa21cd"})
    meta = pd.read_csv(BUS_META).rename(columns={"lsoa": "lsoa21cd"})
    bus = labels.merge(meta, on="lsoa21cd", how="left", validate="one_to_one")
    bus = bus.merge(lnwc, on="lsoa21cd", how="left", validate="many_to_one")
    bus["lnc_grp"] = bus["lnc_grp"].astype("Int64")
    bus.to_csv(DATA_OUT / "bus_analysis_lsoa.csv", index=False)

    matched = bus.dropna(subset=["lnc_grp"]).copy()
    matched["lnc_grp"] = matched["lnc_grp"].astype(int)
    observed = pd.crosstab(matched["cluster"], matched["lnc_grp"]).reindex(
        index=sorted(matched["cluster"].unique()), columns=LNWC_GROUPS, fill_value=0
    )
    expected, row_pct, col_pct, enrichment, residual, stats = association_outputs(observed)

    save_matrix(observed, "bus_crosstab_counts")
    save_matrix(expected, "bus_crosstab_expected")
    save_matrix(row_pct, "bus_crosstab_row_pct")
    save_matrix(col_pct, "bus_crosstab_col_pct")
    save_matrix(enrichment, "bus_enrichment")
    save_matrix(residual, "bus_standardized_residuals")
    top_enrichments(enrichment).to_csv(DATA_OUT / "bus_top_enrichments.csv", index=False)

    draw_heatmap(
        enrichment,
        f"Bus K={BUS_K}: LNWC enrichment (coverage-universe baseline)",
        FIGURE_OUT / "bus_enrichment_heatmap.png",
    )
    draw_heatmap(
        row_pct,
        f"Bus K={BUS_K}: LNWC composition within cluster",
        FIGURE_OUT / "bus_lnwc_composition_heatmap.png",
    )

    map_data = lsoa.merge(
        bus[["lsoa21cd", "cluster", "lnc_grp"]], on="lsoa21cd", how="left"
    )
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))
    map_data.plot(
        column="cluster",
        categorical=True,
        cmap="tab10",
        linewidth=0,
        missing_kwds={"color": "#EEEEEE"},
        ax=axes[0],
        legend=True,
    )
    axes[0].set_title(f"Bus RQ1 clusters (K={BUS_K})")
    map_data.plot(
        column="lnc_grp",
        categorical=True,
        cmap=ListedColormap([LNWC_COLOURS[g] for g in LNWC_GROUPS]),
        linewidth=0,
        missing_kwds={"color": "#EEEEEE"},
        ax=axes[1],
        legend=True,
    )
    axes[1].set_title("LNWC groups in the bus analysis universe")
    for axis in axes:
        axis.set_axis_off()
    plt.tight_layout()
    plt.savefig(FIGURE_OUT / "bus_clusters_lnwc_map.png", dpi=220, bbox_inches="tight")
    plt.close()

    audit = {
        "input_rows": int(len(bus)),
        "matched_lnwc_rows": int(bus["lnc_grp"].notna().sum()),
        "unmatched_lnwc_rows": int(bus["lnc_grp"].isna().sum()),
        "match_rate": float(bus["lnc_grp"].notna().mean()),
        "clusters": int(bus["cluster"].nunique()),
    }
    return bus, enrichment, stats, audit


def build_rail_analysis(lnwc: pd.DataFrame, lsoa: gpd.GeoDataFrame):
    labels = pd.read_csv(RAIL_LABELS).rename(columns={"unit": "NLC"})
    meta = pd.read_csv(RAIL_META)
    coords = pd.read_csv(RAIL_COORDS)
    labels["NLC"] = labels["NLC"].astype(int)
    meta["NLC"] = meta["NLC"].astype(int)
    coords["NLC"] = coords["NLC"].astype(int)

    rail = labels.merge(meta, on="NLC", how="left", validate="one_to_one")
    rail = rail.merge(coords, on="NLC", how="left", validate="one_to_one")
    if rail[["easting", "northing"]].isna().any().any():
        missing = rail.loc[rail["easting"].isna(), "NLC"].tolist()
        raise ValueError(f"Missing coordinates for NLC values: {missing}")
    if rail.duplicated(["easting", "northing"]).any():
        raise ValueError("Duplicate rail coordinates prevent an unambiguous Voronoi diagram")

    stations = gpd.GeoDataFrame(
        rail,
        geometry=gpd.points_from_xy(rail["easting"], rail["northing"]),
        crs=CRS_BNG,
    )
    points = np.column_stack([stations.geometry.x, stations.geometry.y])
    regions, vertices = finite_voronoi_polygons(Voronoi(points), radius=100_000)
    london_union = lsoa.geometry.union_all()
    catchment_geometries = []
    for station_geometry, region in zip(stations.geometry, regions, strict=True):
        cell = Polygon(vertices[region])
        if not cell.is_valid:
            cell = shapely.make_valid(cell)
        catchment = station_geometry.buffer(RAIL_CATCHMENT_METRES).intersection(cell)
        catchment_geometries.append(catchment)

    catchments = gpd.GeoDataFrame(
        stations.drop(columns="geometry"),
        geometry=catchment_geometries,
        crs=CRS_BNG,
    )
    catchments["catchment_area_m2"] = catchments.geometry.area
    catchments["station_in_lnwc_extent"] = stations.geometry.apply(
        lambda station_point: london_union.covers(station_point)
    ).to_numpy()

    lsoa_lnwc = lsoa.merge(lnwc, on="lsoa21cd", how="left", validate="one_to_one")
    intersections = gpd.overlay(
        catchments[["NLC", "geometry"]],
        lsoa_lnwc[["lsoa21cd", "lnc_grp", "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )
    intersections["piece_area_m2"] = intersections.geometry.area
    intersections = intersections.loc[
        (intersections["piece_area_m2"] > 0) & intersections["lnc_grp"].notna()
    ].copy()
    intersections["lnc_grp"] = intersections["lnc_grp"].astype(int)
    covered_area = intersections.groupby("NLC")["piece_area_m2"].sum().rename("covered_area_m2")
    intersections = intersections.merge(covered_area, on="NLC", validate="many_to_one")
    intersections["area_share"] = (
        intersections["piece_area_m2"] / intersections["covered_area_m2"]
    )

    shares = (
        intersections.pivot_table(
            index="NLC",
            columns="lnc_grp",
            values="area_share",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=LNWC_GROUPS, fill_value=0)
        .rename(columns={g: f"lnwc_{g}_share" for g in LNWC_GROUPS})
    )
    rail_analysis = catchments.drop(columns="geometry").merge(
        shares, left_on="NLC", right_index=True, how="left", validate="one_to_one"
    )
    rail_analysis = rail_analysis.merge(
        covered_area, left_on="NLC", right_index=True, how="left", validate="one_to_one"
    )
    rail_analysis["lnwc_coverage_ratio"] = (
        rail_analysis["covered_area_m2"] / rail_analysis["catchment_area_m2"]
    )
    valid_composition = rail_analysis[SHARE_COLUMNS].notna().all(axis=1)
    analysis_eligible = rail_analysis["station_in_lnwc_extent"] & valid_composition
    rail_analysis["analysis_eligible"] = analysis_eligible
    rail_analysis["dominant_lnwc"] = pd.Series(pd.NA, index=rail_analysis.index, dtype="Int64")
    rail_analysis.loc[analysis_eligible, "dominant_lnwc"] = (
        rail_analysis.loc[analysis_eligible, SHARE_COLUMNS].to_numpy().argmax(axis=1) + 1
    )
    values = rail_analysis[SHARE_COLUMNS].to_numpy()
    entropy_terms = np.zeros_like(values)
    positive = values > 0
    entropy_terms[positive] = values[positive] * np.log(values[positive])
    rail_analysis["lnwc_entropy_normalized"] = -entropy_terms.sum(axis=1) / np.log(7)
    rail_analysis.loc[~analysis_eligible, "lnwc_entropy_normalized"] = np.nan

    share_sums = rail_analysis.loc[valid_composition, SHARE_COLUMNS].sum(axis=1)
    if not np.allclose(share_sums, 1.0, atol=1e-6):
        raise AssertionError("Rail LNWC shares do not sum to one")

    exclusion_reason = np.where(
        ~rail_analysis["station_in_lnwc_extent"],
        "station point outside Greater London/LNWC extent",
        "no LNWC-covered catchment area",
    )
    rail_analysis["exclusion_reason"] = np.where(
        analysis_eligible, "", exclusion_reason
    )
    rail_analysis.to_csv(DATA_OUT / "rail_analysis_station.csv", index=False)
    rail_analysis.loc[
        ~analysis_eligible,
        [
            "NLC",
            "Station",
            "cluster",
            "lon",
            "lat",
            "station_in_lnwc_extent",
            "lnwc_coverage_ratio",
            "exclusion_reason",
        ],
    ].to_csv(DATA_OUT / "rail_stations_excluded_from_lnwc_analysis.csv", index=False)
    intersections.drop(columns="geometry").to_csv(
        DATA_OUT / "rail_catchment_lsoa_intersections.csv", index=False
    )
    catchments.to_crs("EPSG:4326").to_file(
        SPATIAL_OUT / "rail_catchments_1200m.geojson", driver="GeoJSON"
    )

    rail_valid = rail_analysis.loc[analysis_eligible].copy()
    equal_composition = rail_valid.groupby("cluster")[SHARE_COLUMNS].mean()
    equal_composition.columns = LNWC_GROUPS
    benchmark = rail_valid[SHARE_COLUMNS].mean()
    benchmark.index = LNWC_GROUPS
    enrichment = equal_composition.div(benchmark, axis=1)

    def weighted_average(group: pd.DataFrame):
        return pd.Series(
            np.average(
                group[SHARE_COLUMNS],
                axis=0,
                weights=group["total_activity"].clip(lower=0),
            ),
            index=LNWC_GROUPS,
        )

    weighted_composition = rail_valid.groupby("cluster").apply(
        weighted_average, include_groups=False
    )
    cluster_summary = rail_analysis.groupby("cluster").agg(
        stations=("NLC", "size"),
        eligible_stations=("analysis_eligible", "sum"),
        eligibility_rate=("analysis_eligible", "mean"),
        mean_total_activity=("total_activity", "mean"),
        mean_lnwc_entropy=("lnwc_entropy_normalized", "mean"),
        mean_lnwc_coverage=("lnwc_coverage_ratio", "mean"),
        mean_max_posterior=("max_posterior", "mean"),
    )

    save_matrix(equal_composition, "rail_lnwc_composition_equal_weight")
    save_matrix(weighted_composition, "rail_lnwc_composition_activity_weighted")
    save_matrix(enrichment, "rail_enrichment")
    cluster_summary.to_csv(DATA_OUT / "rail_cluster_summary.csv")
    top_enrichments(enrichment).to_csv(DATA_OUT / "rail_top_enrichments.csv", index=False)

    dominant = pd.crosstab(rail_valid["cluster"], rail_valid["dominant_lnwc"]).reindex(
        index=sorted(rail_valid["cluster"].unique()),
        columns=LNWC_GROUPS,
        fill_value=0,
    )
    (
        dominant_expected,
        dominant_row_pct,
        dominant_col_pct,
        dominant_enrichment,
        dominant_residual,
        dominant_stats,
    ) = association_outputs(dominant)
    save_matrix(dominant, "rail_dominant_lnwc_counts")
    save_matrix(dominant_row_pct, "rail_dominant_lnwc_row_pct")
    save_matrix(dominant_enrichment, "rail_dominant_lnwc_enrichment")
    save_matrix(dominant_residual, "rail_dominant_lnwc_standardized_residuals")

    permutation = composition_permutation_test(
        rail_valid[SHARE_COLUMNS].to_numpy(),
        rail_valid["cluster"].to_numpy(),
        N_PERMUTATIONS,
        RANDOM_SEED,
    )

    draw_heatmap(
        enrichment,
        f"Rail K={RAIL_K}: catchment LNWC enrichment (equal-station weighting)",
        FIGURE_OUT / "rail_enrichment_heatmap.png",
    )
    draw_heatmap(
        equal_composition,
        f"Rail K={RAIL_K}: mean LNWC composition by station cluster",
        FIGURE_OUT / "rail_lnwc_composition_heatmap.png",
    )

    catchment_map = catchments.merge(
        rail_analysis[["NLC", "dominant_lnwc"]], on="NLC", validate="one_to_one"
    )
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))
    lsoa.boundary.plot(color="#D5D5D5", linewidth=0.15, ax=axes[0])
    catchment_map.plot(
        column="cluster",
        categorical=True,
        cmap="tab10",
        linewidth=0.2,
        edgecolor="white",
        ax=axes[0],
        legend=True,
    )
    stations.plot(
        column="cluster", categorical=True, cmap="tab10", markersize=7, ax=axes[0]
    )
    axes[0].set_title(f"Rail RQ1 clusters and 1,200 m Voronoi catchments (K={RAIL_K})")
    lsoa.boundary.plot(color="#D5D5D5", linewidth=0.15, ax=axes[1])
    catchment_map.plot(
        column="dominant_lnwc",
        categorical=True,
        cmap=ListedColormap([LNWC_COLOURS[g] for g in LNWC_GROUPS]),
        linewidth=0.2,
        edgecolor="white",
        ax=axes[1],
        legend=True,
    )
    axes[1].set_title("Dominant LNWC group within each rail catchment")
    for axis in axes:
        axis.set_axis_off()
    plt.tight_layout()
    plt.savefig(FIGURE_OUT / "rail_catchments_clusters_lnwc_map.png", dpi=220, bbox_inches="tight")
    plt.close()

    lowest_eligibility_cluster = int(cluster_summary["eligibility_rate"].idxmin())
    audit = {
        "input_rows": int(len(rail_analysis)),
        "stations_eligible_for_lnwc_analysis": int(analysis_eligible.sum()),
        "stations_outside_lnwc_extent": int(
            (~rail_analysis["station_in_lnwc_extent"]).sum()
        ),
        "stations_inside_without_lnwc_coverage": int(
            (rail_analysis["station_in_lnwc_extent"] & ~valid_composition).sum()
        ),
        "mean_lnwc_coverage_ratio": float(
            rail_analysis.loc[analysis_eligible, "lnwc_coverage_ratio"].mean()
        ),
        "minimum_lnwc_coverage_ratio": float(
            rail_analysis.loc[analysis_eligible, "lnwc_coverage_ratio"].min()
        ),
        "lowest_eligibility_cluster": lowest_eligibility_cluster,
        "lowest_cluster_eligibility_rate": float(
            cluster_summary.loc[lowest_eligibility_cluster, "eligibility_rate"]
        ),
        "clusters": int(rail_analysis["cluster"].nunique()),
    }
    return rail_analysis, enrichment, dominant_stats, permutation, audit


def main():
    sns.set_theme(style="whitegrid", context="notebook")
    required_inputs = [
        RAIL_LABELS,
        BUS_LABELS,
        RAIL_META,
        BUS_META,
        RAIL_COORDS,
        LNWC,
        LNWC_PORTRAITS,
        LSOA_BOUNDARIES,
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")

    print("Loading LNWC and LSOA boundaries...")
    lnwc = pd.read_csv(LNWC).rename(columns={"lsoa21cd": "lsoa21cd"})
    lnwc["lnc_grp"] = lnwc["lnc_grp"].astype(int)
    # The supplied pen-portrait dictionary is Windows-1252 encoded (curly
    # quotation marks); the classification CSV itself is UTF-8/ASCII.
    portraits = pd.read_csv(LNWC_PORTRAITS, encoding="cp1252").rename(
        columns={"Cluster Group": "lnc_grp", "Name": "lnwc_name"}
    )
    portraits["lnc_grp"] = portraits["lnc_grp"].astype(int)
    portraits.to_csv(DATA_OUT / "lnwc_group_lookup.csv", index=False)

    lsoa = gpd.read_file(LSOA_BOUNDARIES).to_crs(CRS_BNG)
    lsoa = lsoa.rename(columns={"LSOA21CD": "lsoa21cd"})
    lsoa["geometry"] = lsoa.geometry.make_valid()
    lsoa = lsoa[["lsoa21cd", "LSOA21NM", "geometry"]]
    if lsoa["lsoa21cd"].duplicated().any():
        raise ValueError("LSOA boundary key is not unique")

    print("Running bus direct-LSOA baseline...")
    bus, bus_enrichment, bus_stats, bus_audit = build_bus_analysis(lnwc, lsoa)
    print("Building rail Voronoi-clipped catchments and LNWC compositions...")
    rail, rail_enrichment, rail_dom_stats, rail_perm, rail_audit = build_rail_analysis(
        lnwc, lsoa
    )

    audit_rows = [
        {"component": "LNWC", "metric": "rows", "value": len(lnwc)},
        {"component": "LNWC", "metric": "unique_lsoa", "value": lnwc["lsoa21cd"].nunique()},
        {"component": "LSOA boundaries", "metric": "rows", "value": len(lsoa)},
    ]
    audit_rows.extend(
        {"component": "bus", "metric": key, "value": value}
        for key, value in bus_audit.items()
    )
    audit_rows.extend(
        {"component": "rail", "metric": key, "value": value}
        for key, value in rail_audit.items()
    )
    pd.DataFrame(audit_rows).to_csv(DATA_OUT / "data_audit.csv", index=False)

    statistical_summary = pd.DataFrame(
        [
            {
                "mode": "bus",
                "analysis": "cluster_x_lnwc_chi_square",
                **bus_stats,
                "note": "Exploratory; ordinary chi-square ignores spatial autocorrelation.",
            },
            {
                "mode": "rail",
                "analysis": "cluster_x_dominant_lnwc_chi_square",
                **rail_dom_stats,
                "note": "Secondary categorical reduction; composition is the primary rail result.",
            },
            {
                "mode": "rail",
                "analysis": "composition_label_permutation",
                "chi_square": np.nan,
                "p_value": rail_perm["permutation_p"],
                "degrees_of_freedom": np.nan,
                "cramers_v": np.nan,
                "n": rail_perm["n"],
                "r_squared": rail_perm["r_squared"],
                "note": "Exploratory Euclidean composition test with label permutations.",
            },
        ]
    )
    statistical_summary.to_csv(DATA_OUT / "statistical_summary.csv", index=False)

    manifest = pd.DataFrame(
        [
            {
                "role": path.stem,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in required_inputs
        ]
    )
    manifest.to_csv(DATA_OUT / "input_manifest.csv", index=False)

    bus_top = top_enrichments(bus_enrichment)
    rail_top = top_enrichments(rail_enrichment)
    summary_json = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "rail_k": RAIL_K,
            "bus_k": BUS_K,
            "rail_catchment_metres": RAIL_CATCHMENT_METRES,
            "permutations": N_PERMUTATIONS,
            "random_seed": RANDOM_SEED,
        },
        "coverage": {"bus": bus_audit, "rail": rail_audit},
        "statistics": {
            "bus": bus_stats,
            "rail_dominant": rail_dom_stats,
            "rail_composition_permutation": rail_perm,
        },
        "top_enrichments": {
            "bus": bus_top.to_dict(orient="records"),
            "rail": rail_top.to_dict(orient="records"),
        },
    }
    (REPORT_OUT / "results_summary.json").write_text(
        json.dumps(summary_json, indent=2), encoding="utf-8"
    )

    lines = [
        "# RQ2 LNWC baseline — provisional results",
        "",
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite / experiment-agent",
        "- Origin Mode: run",
        f"- Origin Date: {summary_json['generated_utc']}",
        "- Verification Status: ANALYZED",
        "- Version Label: rq2_lnwc_baseline_v1",
        "",
        "## Scope",
        "",
        f"- Rail: provisional K={RAIL_K}; {RAIL_CATCHMENT_METRES} m Voronoi-clipped catchments.",
        f"- Bus: provisional K={BUS_K}; direct LSOA-to-LNWC join.",
        "- LNWC is treated as area context, not as passenger-level characteristics.",
        "",
        "## Coverage",
        "",
        f"- Bus LNWC match: {bus_audit['matched_lnwc_rows']}/{bus_audit['input_rows']} "
        f"({bus_audit['match_rate']:.1%}).",
        f"- Rail stations eligible for LNWC analysis: "
        f"{rail_audit['stations_eligible_for_lnwc_analysis']}/{rail_audit['input_rows']}; "
        f"{rail_audit['stations_outside_lnwc_extent']} station points are outside the LNWC extent.",
        f"- Mean rail catchment LNWC coverage ratio: "
        f"{rail_audit['mean_lnwc_coverage_ratio']:.3f}.",
        f"- Eligibility is uneven: rail Cluster "
        f"{rail_audit['lowest_eligibility_cluster']} has the lowest inclusion rate "
        f"({rail_audit['lowest_cluster_eligibility_rate']:.1%}), so its LNWC composition "
        f"does not represent the full RQ1 cluster.",
        "",
        "## Exploratory association statistics",
        "",
        f"- Bus cluster × LNWC: chi-square={bus_stats['chi_square']:.2f}, "
        f"Cramer's V={bus_stats['cramers_v']:.3f}, n={bus_stats['n']}.",
        f"- Rail dominant-LNWC cross-tab: chi-square={rail_dom_stats['chi_square']:.2f}, "
        f"Cramer's V={rail_dom_stats['cramers_v']:.3f}, n={rail_dom_stats['n']}.",
        f"- Rail seven-part composition: permutation R²={rail_perm['r_squared']:.3f}, "
        f"p={rail_perm['permutation_p']:.4f} ({N_PERMUTATIONS} permutations).",
        "",
        "These tests are exploratory. The bus chi-square test does not account for spatial "
        "autocorrelation, and the rail dominant-category test discards composition detail.",
        "",
        "## Highest enrichment ratios by cluster",
        "",
        "### Bus",
        "",
    ]
    for row in bus_top.itertuples(index=False):
        lines.append(
            f"- Cluster {row.cluster}: LNWC {row.lnwc_group}, ratio {row.enrichment_ratio:.2f}."
        )
    lines.extend(["", "### Rail", ""])
    for row in rail_top.itertuples(index=False):
        lines.append(
            f"- Cluster {row.cluster}: LNWC {row.lnwc_group}, ratio {row.enrichment_ratio:.2f}."
        )
    lines.extend(
        [
            "",
            "## Interpretation limits and next validation gate",
            "",
            "1. Cluster numbers are arbitrary labels and need profile-based names before substantive interpretation.",
            "2. Repeat rail analysis with 800 m Voronoi and station-containing LSOA definitions.",
            "3. Repeat for plausible neighbouring K values before treating any enrichment as stable.",
            "4. Retain equal-station weighting as primary and activity weighting as a secondary service-intensity view.",
        ]
    )
    (REPORT_OUT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    run_metadata = {
        "started_utc": datetime.fromtimestamp(START_TIME, tz=timezone.utc).isoformat(),
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": time.time() - START_TIME,
        "command": "py -3 src/run_analysis.py",
        "python": sys.version,
        "platform": platform.platform(),
        "package_versions": {
            "pandas": pd.__version__,
            "geopandas": gpd.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "shapely": shapely.__version__,
        },
    }
    (REPORT_OUT / "run_metadata.json").write_text(
        json.dumps(run_metadata, indent=2), encoding="utf-8"
    )
    print(
        f"Completed in {run_metadata['duration_seconds']:.1f}s. "
        f"Outputs: {DATA_OUT.parent}"
    )


if __name__ == "__main__":
    main()
