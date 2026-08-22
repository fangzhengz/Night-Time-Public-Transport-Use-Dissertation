"""RQ1 cluster x LNWC association, for the two new sensitivity clustering
results.

Adapted from ``rq2test analysis/src/run_analysis.py``: same association
statistics (chi-square, Cramer's V, standardised residuals, Location
Quotient enrichment), same rail catchment design (Voronoi-clipped station
buffers). Changed 2026-08-08, user decision: catchment radius is now
``config.RAIL_CATCHMENT_METRES`` (800 m) and each station's LNWC composition
is an equal-weight average across the distinct LSOAs its catchment
intersects -- one vote per intersecting LSOA regardless of how much of it
falls inside the catchment -- replacing the previous area-weighted design, so
that the LSOA-level aggregation logic matches rq2_independent_variables and
rq2_loac_analysis exactly. This is a different axis from the activity-weighted
vs equal-weight choice made later when averaging stations within a cluster
(see ``weighted_composition``/``equal_composition`` below); both stages are
now equal-weight by default, with activity-weighting kept as a secondary
service-intensity view of the station-level averaging only. The only
structural change from the original ``run_analysis.py`` is scope: rail
catchments are rebuilt from scratch over the current 403-station
clustering-eligible all-modes refit (not reused from the 270-station
canonical geojson), and bus uses the StopArea CLR 3,372-LSOA universe.
Cluster labels and continuous metrics are read from this folder's own
``run_context_metrics.py`` output rather than a separate meta file.

Eligibility for the LNWC analysis (unified 2026-08-14, user decision):
a station is eligible iff its catchment intersects at least one LSOA with
a valid LNWC classification -- the same rule used for the continuous
contextual variables elsewhere in the project. This replaces an earlier,
stricter rule that additionally required the station's own point to fall
within the union of all London LSOAs; that extra gate excluded only two
stations beyond the continuous-variable exclusion set (Grange Hill, Roding
Valley), whose catchments intersect London LSOAs but whose station point
sits just outside it.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

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
        "chi_square": float(chi2), "p_value": float(p_value), "degrees_of_freedom": int(dof),
        "cramers_v": float(cramers_v), "n": int(n),
    }
    return expected, row_pct, col_pct, enrichment, std_residual, stats


def composition_permutation_test(composition: np.ndarray, labels: np.ndarray, permutations: int, seed: int):
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
        "pseudo_f_between_ss": observed, "total_ss": total_ss, "r_squared": float(r_squared),
        "permutation_p": float(p_value), "n_permutations": permutations, "n": int(len(composition)),
    }


def save_matrix(matrix: pd.DataFrame, name: str, index_label: str = "cluster"):
    matrix.rename_axis(index=index_label, columns="lnwc_group").to_csv(C.DATA_OUT / f"{name}.csv")


def draw_heatmap(
    matrix: pd.DataFrame,
    title: str,
    output: Path,
    fmt: str = ".2f",
    cluster_labels: dict | None = None,
):
    # Case-insensitive: the call sites write "LNWC enrichment", so the former
    # `"Enrichment" in title` test never fired. The colour scale was therefore
    # left uncentred on an enrichment ratio, placing white near 1.25 instead of
    # at 1.0 -- genuinely enriched cells rendered as depleted ones.
    is_enrichment = "enrichment" in title.lower()
    display = matrix.copy()
    display.columns = [C.LNWC_SHORT_NAMES.get(int(c), c) for c in display.columns]
    if cluster_labels:
        display.index = [cluster_labels.get(int(i), f"C{i}") for i in display.index]
    else:
        display.index = [f"C{int(i)}" for i in display.index]

    plt.figure(figsize=(12, max(4.5, 0.9 * len(display))))
    sns.heatmap(
        display, annot=True, fmt=fmt, cmap="RdBu_r",
        center=1 if is_enrichment else None,
        linewidths=0.5, linecolor="white",
        cbar_kws={
            "label": "Enrichment ratio (1 = London average)" if is_enrichment
            else "Share of cluster"
        },
    )
    plt.title(title, pad=14)
    plt.xlabel("LNWC group")
    plt.ylabel("")
    plt.xticks(rotation=0, fontsize=8)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    plt.savefig(output, dpi=220, bbox_inches="tight")
    plt.close()


def top_enrichments(enrichment: pd.DataFrame, top_n: int = 2):
    rows = []
    for cluster, values in enrichment.iterrows():
        for group, ratio in values.sort_values(ascending=False).head(top_n).items():
            rows.append({"cluster": int(cluster), "lnwc_group": int(group), "enrichment_ratio": float(ratio)})
    return pd.DataFrame(rows)


def build_bus_analysis(lnwc: pd.DataFrame, lsoa: gpd.GeoDataFrame):
    bus = pd.read_csv(C.DATA_OUT / "bus_unit_metrics.csv").rename(columns={"lsoa": "lsoa21cd"})
    bus = bus.merge(lnwc, on="lsoa21cd", how="left", validate="many_to_one")
    bus["lnc_grp"] = bus["lnc_grp"].astype("Int64")
    bus.to_csv(C.DATA_OUT / "bus_analysis_lsoa.csv", index=False)

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
    top_enrichments(enrichment).to_csv(C.DATA_OUT / "bus_top_enrichments.csv", index=False)

    draw_heatmap(enrichment, f"Bus K={C.BUS_K} (StopArea CLR): LNWC enrichment", C.FIGURE_OUT / "bus_enrichment_heatmap.png", cluster_labels=C.BUS_CLUSTER_NAMES)
    draw_heatmap(row_pct, f"Bus K={C.BUS_K} (StopArea CLR): LNWC composition within cluster", C.FIGURE_OUT / "bus_lnwc_composition_heatmap.png", cluster_labels=C.BUS_CLUSTER_NAMES)

    map_data = lsoa.merge(bus[["lsoa21cd", "cluster", "lnc_grp"]], on="lsoa21cd", how="left")
    # Named legend rather than raw cluster ids -- fixed 2026-08-08, this map was
    # the one place left plotting the bare "cluster" column while every heatmap
    # already used C.BUS_CLUSTER_NAMES via draw_heatmap's cluster_labels arg.
    # An explicit ordered Categorical keeps the colour-to-cluster correspondence
    # stable (geopandas would otherwise re-sort alphabetically by label text).
    bus_cluster_order = sorted(C.BUS_CLUSTER_NAMES)
    map_data["cluster_label"] = pd.Categorical(
        map_data["cluster"].map(C.BUS_CLUSTER_NAMES),
        categories=[C.BUS_CLUSTER_NAMES[k] for k in bus_cluster_order], ordered=True,
    )
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))
    map_data.plot(
        column="cluster_label", categorical=True,
        cmap=ListedColormap(C.BUS_CLUSTER_COLOURS[: C.BUS_K]),
        linewidth=0, missing_kwds={"color": "#EEEEEE"}, ax=axes[0], legend=True,
    )
    axes[0].set_title(f"Bus sensitivity clusters (K={C.BUS_K}, StopArea CLR)")
    map_data.plot(
        column="lnc_grp", categorical=True, cmap=ListedColormap([C.LNWC_COLOURS[g] for g in LNWC_GROUPS]),
        linewidth=0, missing_kwds={"color": "#EEEEEE"}, ax=axes[1], legend=True,
    )
    axes[1].set_title("LNWC groups in the bus analysis universe")
    for axis in axes:
        axis.set_axis_off()
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / "bus_clusters_lnwc_map.png", dpi=220, bbox_inches="tight")
    plt.close()

    audit = {
        "input_rows": int(len(bus)), "matched_lnwc_rows": int(bus["lnc_grp"].notna().sum()),
        "unmatched_lnwc_rows": int(bus["lnc_grp"].isna().sum()), "match_rate": float(bus["lnc_grp"].notna().mean()),
        "clusters": int(bus["cluster"].nunique()),
    }
    return bus, enrichment, stats, audit


def build_rail_analysis(lnwc: pd.DataFrame, lsoa: gpd.GeoDataFrame):
    rail_metrics = pd.read_csv(C.DATA_OUT / "rail_unit_metrics.csv")
    coords = pd.read_csv(C.RAIL_COORDS).rename(columns={"unit": "NLC"})
    coords["NLC"] = coords["NLC"].astype(int)
    rail = rail_metrics.merge(coords[["NLC", "easting", "northing", "lon", "lat", "coord_source"]], on="NLC", how="left", validate="one_to_one")

    no_coords = rail["easting"].isna()
    rail.loc[no_coords, [
        "NLC", "Station", "cluster",
    ]].assign(exclusion_reason="no NaPTAN coordinate match (outside Greater London extract)").to_csv(
        C.DATA_OUT / "rail_stations_excluded_no_coords.csv", index=False
    )
    rail_with_coords = rail.loc[~no_coords].copy()
    if rail_with_coords.duplicated(["easting", "northing"]).any():
        raise ValueError("Duplicate rail coordinates prevent an unambiguous Voronoi diagram")

    stations = gpd.GeoDataFrame(
        rail_with_coords, geometry=gpd.points_from_xy(rail_with_coords["easting"], rail_with_coords["northing"]), crs=C.CRS_BNG,
    )
    points = np.column_stack([stations.geometry.x, stations.geometry.y])
    regions, vertices = finite_voronoi_polygons(Voronoi(points), radius=100_000)
    london_union = lsoa.geometry.union_all()
    catchment_geometries = []
    for station_geometry, region in zip(stations.geometry, regions, strict=True):
        cell = Polygon(vertices[region])
        if not cell.is_valid:
            cell = shapely.make_valid(cell)
        catchment = station_geometry.buffer(C.RAIL_CATCHMENT_METRES).intersection(cell)
        catchment_geometries.append(catchment)

    catchments = gpd.GeoDataFrame(stations.drop(columns="geometry"), geometry=catchment_geometries, crs=C.CRS_BNG)
    catchments["catchment_area_m2"] = catchments.geometry.area
    catchments["station_in_lnwc_extent"] = stations.geometry.apply(lambda p: london_union.covers(p)).to_numpy()

    lsoa_lnwc = lsoa.merge(lnwc, on="lsoa21cd", how="left", validate="one_to_one")
    intersections = gpd.overlay(
        catchments[["NLC", "geometry"]], lsoa_lnwc[["lsoa21cd", "lnc_grp", "geometry"]], how="intersection", keep_geom_type=False,
    )
    intersections["piece_area_m2"] = intersections.geometry.area
    intersections = intersections.loc[(intersections["piece_area_m2"] > 0) & intersections["lnc_grp"].notna()].copy()
    intersections["lnc_grp"] = intersections["lnc_grp"].astype(int)
    # Coverage/eligibility diagnostics stay area-based (this asks "how much of
    # the catchment geometry is covered by a matched LSOA", a data-completeness
    # question, not the composition weighting choice below).
    covered_area = intersections.groupby("NLC")["piece_area_m2"].sum().rename("covered_area_m2")
    intersections = intersections.merge(covered_area, on="NLC", validate="many_to_one")

    # Composition itself is an equal-weight average across distinct
    # intersecting LSOAs: an overlay can return multiple polygon pieces for
    # the same NLC-LSOA pair (e.g. split by a third boundary), so collapse to
    # one row per (NLC, LSOA) before giving each intersecting LSOA one vote,
    # matching the estimand used for the continuous variables elsewhere in the
    # project (see rq2_independent_variables/src/01_build_variable_table.py).
    distinct_lsoa = intersections[["NLC", "lsoa21cd", "lnc_grp"]].drop_duplicates()
    distinct_lsoa["equal_share"] = 1.0 / distinct_lsoa.groupby("NLC")["lsoa21cd"].transform("nunique")

    shares = (
        distinct_lsoa.pivot_table(index="NLC", columns="lnc_grp", values="equal_share", aggfunc="sum", fill_value=0)
        .reindex(columns=LNWC_GROUPS, fill_value=0)
        .rename(columns={g: f"lnwc_{g}_share" for g in LNWC_GROUPS})
    )
    rail_analysis = catchments.drop(columns="geometry").merge(shares, left_on="NLC", right_index=True, how="left", validate="one_to_one")
    rail_analysis = rail_analysis.merge(covered_area, left_on="NLC", right_index=True, how="left", validate="one_to_one")
    rail_analysis["lnwc_coverage_ratio"] = rail_analysis["covered_area_m2"] / rail_analysis["catchment_area_m2"]
    valid_composition = rail_analysis[SHARE_COLUMNS].notna().all(axis=1)
    # Unified 2026-08-14 (user decision): eligibility now matches the continuous
    # contextual variables' rule exactly (catchment intersects >=1 classified
    # LSOA), dropping the extra station-point-in-extent gate. That gate had
    # excluded exactly two additional stations (Grange Hill, Roding Valley)
    # whose catchments intersect London LSOAs but whose station point sits just
    # outside the LSOA union -- see rail_stations_excluded_from_lnwc_analysis.csv.
    analysis_eligible = valid_composition
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

    rail_analysis["exclusion_reason"] = np.where(analysis_eligible, "", "no LNWC-covered catchment area")
    rail_analysis.to_csv(C.DATA_OUT / "rail_analysis_station.csv", index=False)
    rail_analysis.loc[
        ~analysis_eligible, ["NLC", "Station", "cluster", "lon", "lat", "station_in_lnwc_extent", "lnwc_coverage_ratio", "exclusion_reason"],
    ].to_csv(C.DATA_OUT / "rail_stations_excluded_from_lnwc_analysis.csv", index=False)
    intersections.drop(columns="geometry").to_csv(C.DATA_OUT / "rail_catchment_lsoa_intersections.csv", index=False)
    catchments.to_crs(C.CRS_WGS84).to_file(
        C.SPATIAL_OUT / f"rail_catchments_{C.RAIL_CATCHMENT_METRES}m_allmodes.geojson", driver="GeoJSON"
    )

    rail_valid = rail_analysis.loc[analysis_eligible].copy()
    equal_composition = rail_valid.groupby("cluster")[SHARE_COLUMNS].mean()
    equal_composition.columns = LNWC_GROUPS
    benchmark = rail_valid[SHARE_COLUMNS].mean()
    benchmark.index = LNWC_GROUPS
    enrichment = equal_composition.div(benchmark, axis=1)

    def weighted_average(group: pd.DataFrame):
        return pd.Series(np.average(group[SHARE_COLUMNS], axis=0, weights=group["total_activity"].clip(lower=0)), index=LNWC_GROUPS)

    weighted_composition = rail_valid.groupby("cluster").apply(weighted_average, include_groups=False)
    cluster_summary = rail_analysis.groupby("cluster").agg(
        stations=("NLC", "size"), eligible_stations=("analysis_eligible", "sum"), eligibility_rate=("analysis_eligible", "mean"),
        mean_total_activity=("total_activity", "mean"), mean_lnwc_entropy=("lnwc_entropy_normalized", "mean"),
        mean_lnwc_coverage=("lnwc_coverage_ratio", "mean"),
    )

    save_matrix(equal_composition, "rail_lnwc_composition_equal_weight")
    save_matrix(weighted_composition, "rail_lnwc_composition_activity_weighted")
    save_matrix(enrichment, "rail_enrichment")
    cluster_summary.to_csv(C.DATA_OUT / "rail_cluster_summary.csv")
    top_enrichments(enrichment).to_csv(C.DATA_OUT / "rail_top_enrichments.csv", index=False)

    dominant = pd.crosstab(rail_valid["cluster"], rail_valid["dominant_lnwc"]).reindex(
        index=sorted(rail_valid["cluster"].unique()), columns=LNWC_GROUPS, fill_value=0
    )
    (dominant_expected, dominant_row_pct, dominant_col_pct, dominant_enrichment, dominant_residual, dominant_stats) = association_outputs(dominant)
    save_matrix(dominant, "rail_dominant_lnwc_counts")
    save_matrix(dominant_row_pct, "rail_dominant_lnwc_row_pct")
    save_matrix(dominant_enrichment, "rail_dominant_lnwc_enrichment")
    save_matrix(dominant_residual, "rail_dominant_lnwc_standardized_residuals")

    permutation = composition_permutation_test(rail_valid[SHARE_COLUMNS].to_numpy(), rail_valid["cluster"].to_numpy(), C.N_PERMUTATIONS, C.RANDOM_SEED)

    draw_heatmap(enrichment, f"Rail K={C.RAIL_K} (all-modes): catchment LNWC enrichment", C.FIGURE_OUT / "rail_enrichment_heatmap.png", cluster_labels=C.RAIL_CLUSTER_NAMES)
    draw_heatmap(equal_composition, f"Rail K={C.RAIL_K} (all-modes): mean LNWC composition by cluster", C.FIGURE_OUT / "rail_lnwc_composition_heatmap.png", cluster_labels=C.RAIL_CLUSTER_NAMES)

    catchment_map = catchments.merge(rail_analysis[["NLC", "dominant_lnwc"]], on="NLC", validate="one_to_one")
    # Named legend rather than raw cluster ids -- same fix as the bus map above.
    rail_cluster_order = sorted(C.RAIL_CLUSTER_NAMES)
    rail_label_categories = [C.RAIL_CLUSTER_NAMES[k] for k in rail_cluster_order]
    catchment_map["cluster_label"] = pd.Categorical(
        catchment_map["cluster"].map(C.RAIL_CLUSTER_NAMES), categories=rail_label_categories, ordered=True,
    )
    stations = stations.copy()
    stations["cluster_label"] = pd.Categorical(
        stations["cluster"].map(C.RAIL_CLUSTER_NAMES), categories=rail_label_categories, ordered=True,
    )
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))
    lsoa.boundary.plot(color="#D5D5D5", linewidth=0.15, ax=axes[0])
    catchment_map.plot(column="cluster_label", categorical=True, cmap="tab10", linewidth=0.2, edgecolor="white", ax=axes[0], legend=True)
    stations.plot(column="cluster_label", categorical=True, cmap="tab10", markersize=7, ax=axes[0])
    axes[0].set_title(f"Rail sensitivity clusters + {C.RAIL_CATCHMENT_METRES} m Voronoi catchments (K={C.RAIL_K}, all-modes, NaPTAN-matched)")
    lsoa.boundary.plot(color="#D5D5D5", linewidth=0.15, ax=axes[1])
    catchment_map.plot(
        column="dominant_lnwc", categorical=True, cmap=ListedColormap([C.LNWC_COLOURS[g] for g in LNWC_GROUPS]),
        linewidth=0.2, edgecolor="white", ax=axes[1], legend=True,
    )
    axes[1].set_title("Dominant LNWC group within each rail catchment")
    for axis in axes:
        axis.set_axis_off()
    plt.tight_layout()
    plt.savefig(C.FIGURE_OUT / "rail_catchments_clusters_lnwc_map.png", dpi=220, bbox_inches="tight")
    plt.close()

    lowest_eligibility_cluster = int(cluster_summary["eligibility_rate"].idxmin())
    audit = {
        "input_rows": int(len(rail_analysis)), "stations_without_coords": int(no_coords.sum()),
        "stations_eligible_for_lnwc_analysis": int(analysis_eligible.sum()),
        "stations_outside_lnwc_extent": int((~rail_analysis["station_in_lnwc_extent"]).sum()),
        "stations_inside_without_lnwc_coverage": int((rail_analysis["station_in_lnwc_extent"] & ~valid_composition).sum()),
        "mean_lnwc_coverage_ratio": float(rail_analysis.loc[analysis_eligible, "lnwc_coverage_ratio"].mean()),
        "minimum_lnwc_coverage_ratio": float(rail_analysis.loc[analysis_eligible, "lnwc_coverage_ratio"].min()),
        "lowest_eligibility_cluster": lowest_eligibility_cluster,
        "lowest_cluster_eligibility_rate": float(cluster_summary.loc[lowest_eligibility_cluster, "eligibility_rate"]),
        "clusters": int(rail_analysis["cluster"].nunique()),
    }
    return rail_analysis, enrichment, dominant_stats, permutation, audit


def main():
    sns.set_theme(style="whitegrid", context="notebook")
    required_inputs = [
        C.DATA_OUT / "bus_unit_metrics.csv", C.DATA_OUT / "rail_unit_metrics.csv",
        C.RAIL_COORDS, C.LNWC, C.LNWC_PORTRAITS, C.LSOA_BOUNDARIES,
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing required inputs (run run_context_metrics.py first): {missing}"
        )

    print("Loading LNWC and LSOA boundaries...")
    lnwc = pd.read_csv(C.LNWC)
    lnwc["lnc_grp"] = lnwc["lnc_grp"].astype(int)
    portraits = pd.read_csv(C.LNWC_PORTRAITS, encoding="cp1252").rename(columns={"Cluster Group": "lnc_grp", "Name": "lnwc_name"})
    portraits["lnc_grp"] = portraits["lnc_grp"].astype(int)
    portraits.to_csv(C.DATA_OUT / "lnwc_group_lookup.csv", index=False)

    lsoa = gpd.read_file(C.LSOA_BOUNDARIES).to_crs(C.CRS_BNG)
    lsoa = lsoa.rename(columns={"LSOA21CD": "lsoa21cd"})
    lsoa["geometry"] = lsoa.geometry.make_valid()
    lsoa = lsoa[["lsoa21cd", "LSOA21NM", "geometry"]]
    if lsoa["lsoa21cd"].duplicated().any():
        raise ValueError("LSOA boundary key is not unique")

    print("Running bus direct-LSOA LNWC linkage (StopArea CLR, K=4)...")
    bus, bus_enrichment, bus_stats, bus_audit = build_bus_analysis(lnwc, lsoa)
    rail_n = pd.read_csv(C.RAIL_LABELS, usecols=["unit"])["unit"].nunique()
    print(f"Building rail Voronoi-clipped catchments over the {rail_n}-station clustering-eligible all-modes refit...")
    rail, rail_enrichment, rail_dom_stats, rail_perm, rail_audit = build_rail_analysis(lnwc, lsoa)

    audit_rows = [
        {"component": "LNWC", "metric": "rows", "value": len(lnwc)},
        {"component": "LNWC", "metric": "unique_lsoa", "value": lnwc["lsoa21cd"].nunique()},
        {"component": "LSOA boundaries", "metric": "rows", "value": len(lsoa)},
    ]
    audit_rows.extend({"component": "bus", "metric": k, "value": v} for k, v in bus_audit.items())
    audit_rows.extend({"component": "rail", "metric": k, "value": v} for k, v in rail_audit.items())
    pd.DataFrame(audit_rows).to_csv(C.DATA_OUT / "lnwc_data_audit.csv", index=False)

    statistical_summary = pd.DataFrame(
        [
            {"mode": "bus", "analysis": "cluster_x_lnwc_chi_square", **bus_stats, "note": "Exploratory; ordinary chi-square ignores spatial autocorrelation."},
            {"mode": "rail", "analysis": "cluster_x_dominant_lnwc_chi_square", **rail_dom_stats, "note": "Secondary categorical reduction; composition is the primary rail result."},
            {
                "mode": "rail", "analysis": "composition_label_permutation", "chi_square": np.nan, "p_value": rail_perm["permutation_p"],
                "degrees_of_freedom": np.nan, "cramers_v": np.nan, "n": rail_perm["n"], "r_squared": rail_perm["r_squared"],
                "note": "Exploratory Euclidean composition test with label permutations.",
            },
        ]
    )
    statistical_summary.to_csv(C.DATA_OUT / "lnwc_statistical_summary.csv", index=False)

    manifest = pd.DataFrame(
        [{"role": path.stem, "path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in required_inputs]
    )
    manifest.to_csv(C.DATA_OUT / "lnwc_input_manifest.csv", index=False)

    bus_top = top_enrichments(bus_enrichment)
    rail_top = top_enrichments(rail_enrichment)
    generated = datetime.now(timezone.utc).isoformat()

    lines = [
        "# RQ2 sensitivity clusters -- LNWC association",
        "",
        "## Material Passport",
        "",
        f"- Origin Date: {generated}",
        "- Verification Status: ANALYZED",
        "- Version Label: rq2_new_clusters_lnwc_v1",
        "",
        "## Scope",
        "",
        f"- Rail: all-modes merged sensitivity clustering K={C.RAIL_K}; {C.RAIL_CATCHMENT_METRES} m Voronoi-clipped catchments rebuilt over all {rail_audit['input_rows']} stations (not reused from the canonical 270-station geometry).",
        f"- Bus: StopArea CLR sensitivity clustering K={C.BUS_K}; direct LSOA-to-LNWC join.",
        "- LNWC is treated as area context, not as passenger-level characteristics.",
        "",
        "## Coverage",
        "",
        f"- Bus LNWC match: {bus_audit['matched_lnwc_rows']}/{bus_audit['input_rows']} ({bus_audit['match_rate']:.1%}).",
        f"- Rail: {rail_audit['stations_without_coords']} stations excluded for no NaPTAN coordinate match (outside Greater London extract); "
        f"{rail_audit['stations_eligible_for_lnwc_analysis']}/{rail_audit['input_rows']} eligible for LNWC analysis "
        f"(catchment intersects >=1 classified LSOA -- same rule as the continuous contextual variables).",
        f"- Mean rail catchment LNWC coverage ratio: {rail_audit['mean_lnwc_coverage_ratio']:.3f}.",
        "",
        "## Exploratory association statistics",
        "",
        f"- Bus cluster x LNWC: chi-square={bus_stats['chi_square']:.2f}, Cramer's V={bus_stats['cramers_v']:.3f}, n={bus_stats['n']}.",
        f"- Rail dominant-LNWC cross-tab: chi-square={rail_dom_stats['chi_square']:.2f}, Cramer's V={rail_dom_stats['cramers_v']:.3f}, n={rail_dom_stats['n']}.",
        f"- Rail seven-part composition: permutation R2={rail_perm['r_squared']:.3f}, p={rail_perm['permutation_p']:.4f} ({C.N_PERMUTATIONS} permutations).",
        "",
        "## Highest enrichment ratios by cluster",
        "",
        "### Bus",
        "",
    ]
    for row in bus_top.itertuples(index=False):
        lines.append(f"- Cluster {row.cluster}: LNWC {row.lnwc_group}, ratio {row.enrichment_ratio:.2f}.")
    lines.extend(["", "### Rail", ""])
    for row in rail_top.itertuples(index=False):
        lines.append(f"- Cluster {row.cluster}: LNWC {row.lnwc_group}, ratio {row.enrichment_ratio:.2f}.")
    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "- Cluster numbers are arbitrary labels; compare against the canonical rail-K5(270)/bus-K3 numbers using the combined report, not in isolation.",
        "- Ordinary chi-square/permutation tests here ignore spatial autocorrelation.",
        "- Rail catchment LNWC composition (LSOA level) is an equal-weight average across distinct intersecting LSOAs. "
        "Rail cluster composition (station level) uses equal-station weighting as primary; activity weighting is a secondary service-intensity view.",
    ])
    (C.REPORT_OUT / "LNWC_ASSOCIATION.md").write_text("\n".join(lines), encoding="utf-8")

    metadata = {
        "generated_utc": generated, "duration_seconds": time.time() - START_TIME,
        "command": "py -3 src/run_lnwc_analysis.py", "python": sys.version, "platform": platform.platform(),
        "package_versions": {"pandas": pd.__version__, "geopandas": gpd.__version__, "numpy": np.__version__, "scipy": scipy.__version__, "shapely": shapely.__version__},
    }
    (C.REPORT_OUT / "run_metadata_lnwc.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Completed LNWC analysis in {metadata['duration_seconds']:.1f}s.")


if __name__ == "__main__":
    main()
